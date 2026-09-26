# Tài liệu tham khảo

> [← Mục lục](README.md) · File này được **sinh tự động** từ các file bài học. Đừng sửa tay;
> sửa ở file bài học rồi chạy `python3 tools/build_references.py`.

Tổng hợp 1517 trang tài liệu từ 26 chủ đề. Dùng file này theo thứ tự:

1. **[Tài liệu nền theo chủ đề](#1-tài-liệu-nền-theo-chủ-đề)**: 4–8 nguồn chính của mỗi chủ đề. Bắt đầu từ đây.
2. **[Sách](#2-sách)**: danh sách sách, gom từ mọi chủ đề.
3. **[Được dẫn nhiều nhất](#3-được-dẫn-nhiều-nhất)**: nguồn xuất hiện ở nhiều chủ đề, thường đáng đọc kỹ.
4. **[Chỉ mục theo module](#4-chỉ-mục-theo-module)**: toàn bộ tài liệu ở mục "Đọc" của từng module (1981 link), để tra khi đang học một module cụ thể.

Số trong ngoặc vuông, ví dụ [03], là file bài học dẫn tới tài liệu đó.

---

## 1. Tài liệu nền theo chủ đề

### Nền tảng

#### [01. Hệ điều hành và Linux](01-os-linux.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [*Operating Systems: Three Easy Pieces*](https://pages.cs.wisc.edu/~remzi/OSTEP/) (Arpaci-Dusseau) | Sách online miễn phí | Nền lý thuyết: process, scheduling, virtual memory, concurrency, file system. Viết dễ đọc |
| [*Systems Performance*, 2nd ed.](https://www.brendangregg.com/systems-performance-2nd-edition-book.html) (Brendan Gregg, 2020) | Sách | Linux dưới góc vận hành: CPU, memory, disk, network, công cụ quan sát. Sách gối đầu của SRE |
| [Linux man-pages](https://man7.org/linux/man-pages/) và [*The Linux Programming Interface*](https://man7.org/tlpi/) (Kerrisk) | Official docs / Sách | Nguồn chuẩn cho syscall, signal, `/proc`. Khi blog và man page mâu thuẫn, tin man page |
| [Linux kernel docs: Admin Guide](https://docs.kernel.org/admin-guide/cgroup-v2.html) | Official docs | cgroup v2, memory, sysctl, scheduler |
| [Brendan Gregg's site](https://www.brendangregg.com/) | Blog | USE method, flame graph, perf, eBPF, load average |
| [PHP-FPM configuration](https://www.php.net/manual/en/install.fpm.configuration.php) | Official docs | Process model của PHP-FPM, `pm.*`, timeout, slowlog |
| [BashPitfalls](https://mywiki.wooledge.org/BashPitfalls) | Wiki | Các lỗi shell script hay gặp, kèm cách sửa |

#### [02. Mạng: TCP, DNS, HTTP, TLS, proxy, load balancer](02-networking.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [*High Performance Browser Networking*](https://hpbn.co/) (Ilya Grigorik) | Sách online miễn phí | TCP, TLS, HTTP/1.1, HTTP/2 dưới góc latency. Đọc các chương networking 101 và HTTP. Phần HTTP/3 chưa có |
| [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110) (HTTP Semantics), [RFC 9111](https://www.rfc-editor.org/rfc/rfc9111) (Caching), [RFC 9112](https://www.rfc-editor.org/rfc/rfc9112) (HTTP/1.1) | RFC | Nguồn chuẩn cho method, status, header, cache. Tra cứu, không cần đọc hết |
| [MDN: HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP) | Docs | Giải thích HTTP dễ đọc nhất, có ví dụ, cập nhật theo trình duyệt |
| [Nginx docs](https://nginx.org/en/docs/) | Official docs | Proxy, upstream, FastCGI, rate limit, real IP. Mỗi directive ghi giá trị mặc định và phiên bản |
| [*Computer Networking: A Top-Down Approach*](https://gaia.cs.umass.edu/kurose_ross/) (Kurose, Ross) | Sách | Nền lý thuyết nếu chưa học mạng bài bản: chương 2 (application), 3 (transport) |
| [The Illustrated TLS 1.3 Connection](https://tls13.xargs.org/) | Tài liệu trực quan | Từng byte của một handshake TLS 1.3 thật |
| [PortSwigger Web Security Academy](https://portswigger.net/web-security) | Khoá học miễn phí | Request smuggling, các lỗi ở ranh giới proxy và app |

#### [21. Cấu trúc dữ liệu và thuật toán](21-dsa.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [NeetCode Roadmap](https://neetcode.io/roadmap) | Lộ trình + video | Thứ tự học pattern và danh sách NeetCode 150. **Dùng làm xương sống** để chọn bài |
| LeetCode (leetcode.com) | Nền tảng luyện bài | Nơi làm bài; tên bài trong file này là tên trên LeetCode. Hỗ trợ PHP |
| [Tech Interview Handbook](https://www.techinterviewhandbook.org/) | Hướng dẫn miễn phí | [Study cheatsheet](https://www.techinterviewhandbook.org/algorithms/study-cheatsheet/) theo từng cấu trúc, [Grind 75](https://www.techinterviewhandbook.org/grind75) khi ít thời gian |
| [*Algorithms*, 4th ed.](https://algs4.cs.princeton.edu/home/) (Sedgewick, Wayne) | Sách + site miễn phí | Giải thích từng cấu trúc có hình và code. Chương nào đọc ghi ở từng module |
| *Introduction to Algorithms* (CLRS), 4th ed. (MIT Press 2022) | Sách | Tra cứu khi cần chứng minh hoặc phân tích chặt. Không cần đọc hết |
| [VisuAlgo](https://visualgo.net/en) | Mô phỏng tương tác | Xem thuật toán chạy từng bước: sort, heap, BST, graph, union-find |
| [cp-algorithms](https://cp-algorithms.com/) | Bài viết | Union-find, segment tree, Fenwick, Dijkstra viết gọn và chính xác |
| [PHP SPL Data Structures](https://www.php.net/manual/en/spl.datastructures.php) | Official docs | Cấu trúc có sẵn trong PHP khi làm bài bằng PHP |

### Dữ liệu

#### [03. Database quan hệ và SQL](03-database-sql.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [MySQL 8.4 Reference Manual](https://dev.mysql.com/doc/refman/8.4/en/) | Official docs | Nguồn chuẩn cho mọi hành vi của MySQL. Khi blog và docs mâu thuẫn, tin docs |
| [Use The Index, Luke](https://use-the-index-luke.com/) | Sách online miễn phí | Index và query, viết cho developer. **Đọc hết**, khoảng 1 tuần |
| *High Performance MySQL*, 4th ed. (Botros, Tinley; O'Reilly 2021) | Sách | Schema, index, query, replication, vận hành MySQL |
| [*Designing Data-Intensive Applications*](https://dataintensive.net/) (Kleppmann) | Sách | Ch.3 storage, ch.5 replication, ch.6 partitioning, **ch.7 transactions** (số chương theo bản 1) |
| [PostgreSQL docs](https://www.postgresql.org/docs/current/) | Official docs | Đối chiếu. Phần MVCC và isolation viết rất rõ, nên đọc kể cả khi dùng MySQL |
| [Jeremy Cole: InnoDB internals](https://blog.jcole.us/innodb/) | Blog | Cấu trúc page, B+tree, record của InnoDB, có hình vẽ |
| [CMU 15-445 Database Systems](https://15445.courses.cs.cmu.edu/) | Khoá học (video + slide) | Nếu muốn hiểu từ gốc: storage, index, concurrency control, recovery |
| [Laravel docs](https://laravel.com/docs/database) | Official docs | Tầng DB của Laravel: query builder, Eloquent, transaction, migration |

#### [04. NoSQL, search và storage](04-nosql-search-storage.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [Redis docs](https://redis.io/docs/latest/) | Official docs | Kiểu dữ liệu, persistence, eviction, replication, Cluster. Phần lớn áp dụng cho cả [Valkey](https://valkey.io/) |
| [MongoDB Manual](https://www.mongodb.com/docs/manual/) | Official docs | Data modeling, index, aggregation, replica set, sharding, change streams |
| [Elastic docs](https://www.elastic.co/docs/) | Official docs | Analyzer, mapping, pagination, alias, vận hành cluster. OpenSearch: [docs.opensearch.org](https://docs.opensearch.org/latest/) |
| [DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html) và [*The DynamoDB Book*](https://www.dynamodbbook.com/) (Alex DeBrie) | Official docs + sách | Query-first modeling, single-table design |
| [Amazon S3 User Guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html) | Official docs | Presigned URL, multipart, consistency, conditional write, lifecycle, bảo mật |
| [*Designing Data-Intensive Applications*](https://dataintensive.net/) (Kleppmann) | Sách | Ch.2 data model, ch.3 storage (LSM, column store), ch.5 replication, ch.6 partitioning (số chương theo bản 1) |
| [Laravel docs](https://laravel.com/docs/redis) | Official docs | Redis, [Scout](https://laravel.com/docs/scout), [Filesystem](https://laravel.com/docs/filesystem) (S3) |

#### [11. Cache](11-cache.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [Scaling Memcache at Facebook](https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala) (Nishtala và cộng sự, NSDI 2013) | Paper | Bài đọc quan trọng nhất về cache ở quy mô lớn: lease, invalidation qua commit log, nhiều region. Đọc mục 3 (in a cluster) trước |
| [AWS: Database Caching Strategies Using Redis](https://docs.aws.amazon.com/whitepapers/latest/database-caching-strategies-using-redis/welcome.html) và [Caching best practices](https://aws.amazon.com/caching/best-practices/) | Whitepaper | Cache-aside, write-through, TTL, thundering herd, viết ngắn gọn |
| [Redis docs](https://redis.io/docs/latest/) | Official docs | Eviction, TTL, client-side caching. Phần lớn áp dụng cho [Valkey](https://valkey.io/) |
| [Laravel Cache](https://laravel.com/docs/cache) | Official docs | `remember`, `flexible`, lock, tag, memo, failover |
| [RFC 9111: HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111) và [MDN: HTTP caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching) | RFC + guide | Tầng cache HTTP (browser, CDN, proxy). MDN dễ đọc hơn, RFC để tra |
| [*Designing Data-Intensive Applications*](https://dataintensive.net/) (Kleppmann) | Sách | Ch.5 (replication lag, nguồn gốc nhiều race khi nạp cache), ch.11 (CDC, giữ các hệ thống đồng bộ) (số chương theo bản 1) |

#### [22. Dữ liệu thực tế: những thứ "đời thường" hay gây bug production](22-practical-data.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [MySQL 8.4 Reference Manual](https://dev.mysql.com/doc/refman/8.4/en/) | Official docs | Kiểu thời gian, timezone, charset/collation, số |
| [PHP Manual](https://www.php.net/manual/en/) | Official docs | Date/Time, bcmath, mbstring, intl (Normalizer, Transliterator, NumberFormatter), SPL file |
| [Laravel docs](https://laravel.com/docs/eloquent-mutators#date-casting) | Official docs | Date casting, scheduler timezone, queue sau commit, streamed download |
| [Unicode UAX #15](https://unicode.org/reports/tr15/) và [UAX #29](https://unicode.org/reports/tr29/) | Chuẩn | Normalization (NFC/NFD) và grapheme cluster. Đọc phần giới thiệu và hình ví dụ |
| [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html) | Hướng dẫn bảo mật | Upload file, [CSV injection](https://owasp.org/www-community/attacks/CSV_Injection) |
| [Stripe docs](https://docs.stripe.com/webhooks) | Official docs của cổng thanh toán | Webhook, [idempotent request](https://docs.stripe.com/api/idempotent_requests): tài liệu mẫu mực để hiểu khái niệm, áp dụng cho cả VNPay/Momo |
| [Modern Treasury: Accounting for Developers](https://www.moderntreasury.com/journal/accounting-for-developers-part-i) | Blog kỹ thuật | Ledger, bút toán kép viết cho developer |

### Ngôn ngữ và thiết kế code

#### [05. PHP và Laravel](05-php-laravel.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [PHP Manual](https://www.php.net/manual/en/) | Official docs | Nguồn chuẩn cho ngôn ngữ, ini, FPM, OPcache. Đọc cả phần *Changelog* cuối mỗi trang hàm |
| [PHP RFC wiki](https://wiki.php.net/rfc) | Đặc tả thay đổi | Vì sao một tính năng tồn tại, ca biên, thứ bị từ chối. RFC trả lời "vì sao" tốt hơn manual |
| [PHP.Watch: versions](https://php.watch/versions) | Tổng hợp theo phiên bản | Mỗi bản 8.x có gì mới, gì deprecated, gì đổi mặc định. Dùng khi nâng cấp |
| [PHP Internals Book](https://www.phpinternalsbook.com/) | Sách online miễn phí | zval, refcount, `zend_string`, hashtable, lifecycle của extension. Đọc phần PHP 7/8 |
| [Nikita Popov (nikic) blog](https://www.npopov.com/) | Blog của core dev | Các bài kinh điển về biểu diễn giá trị, hashtable, VM của PHP 7+ |
| [Laravel docs](https://laravel.com/docs/lifecycle) | Official docs | Luôn là bản mới nhất (13.x). Đọc kỹ *Architecture Concepts*, *Queues*, *Eloquent* |
| [laravel/framework](https://github.com/laravel/framework) | Source code | Đọc `Container.php`, `Facade.php`, `Http/Kernel.php` khi muốn trả lời "bên dưới làm gì" |
| [PHPStan docs](https://phpstan.org/user-guide/getting-started) | Official docs | Static analysis: rule level, baseline, generics trong PHPDoc |

#### [08. OOP, SOLID, design pattern và clean code](08-oop-design.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| *Design Patterns* (Gamma, Helm, Johnson, Vlissides; 1994) | Sách | Nguồn gốc 23 pattern GoF. Đọc chương 1 (nguyên tắc "program to an interface", "favor composition") và tra từng pattern khi cần |
| [Refactoring.Guru](https://refactoring.guru/design-patterns) | Sách online miễn phí | Pattern và code smell có hình minh hoạ, ví dụ PHP/Java/Go. Dễ đọc hơn sách GoF |
| *Refactoring*, 2nd ed. (Fowler, 2018) và [catalog](https://refactoring.com/catalog/) | Sách + catalog | Code smell (ch.3), các kỹ thuật refactoring, cách refactor từng bước nhỏ |
| *Working Effectively with Legacy Code* (Feathers, 2004) | Sách | Seam, characterization test, đưa code không test vào kiểm soát |
| [*Patterns of Enterprise Application Architecture*](https://martinfowler.com/eaaCatalog/) (Fowler) | Sách + catalog | Repository, Unit of Work, Active Record, Data Mapper, Identity Map |
| [PHP Manual: Classes and Objects](https://www.php.net/manual/en/language.oop5.php) | Official docs | Interface, abstract, trait, enum, readonly, property hooks: hành vi chính xác của PHP |
| [Laravel: Service Container](https://laravel.com/docs/container) | Official docs | DI, binding interface → implementation, contextual binding; nền tảng để hiểu SOLID trong Laravel |
| *Effective Java*, 3rd ed. (Bloch) | Sách | Đối chiếu: item 1 (static factory), item 17 (immutability), item 18 (composition thay kế thừa) |

#### [06. Java, JVM và Spring](06-java-spring.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [dev.java Learn](https://dev.java/learn/) | Official tutorial | Ngôn ngữ, Collections, JVM tools. Bản dịch một phần ở [java/03-collections/](../java/03-collections/README.md) |
| [JEP index](https://openjdk.org/jeps/0) | Đặc tả tính năng | Nguồn chuẩn cho "tính năng X có từ bản nào, còn preview không" |
| *Effective Java*, 3rd ed. (Joshua Bloch) | Sách | Item về `equals`/`hashCode`, generics, exception, concurrency. Đọc theo item, không cần đọc hết |
| *Java Concurrency in Practice* (Goetz và cộng sự) | Sách | Ch.2–3 (thread safety, visibility), ch.6–8 (executor, pool). Cũ nhưng nền tảng không đổi |
| [Spring Framework reference](https://docs.spring.io/spring-framework/reference/) | Official docs | Container, AOP, transaction, web |
| [Spring Boot reference](https://docs.spring.io/spring-boot/reference/) | Official docs | Auto-configuration, config, task execution, testing, Actuator |
| [Hibernate ORM User Guide](https://docs.jboss.org/hibernate/orm/7.2/userguide/html_single/Hibernate_User_Guide.html) | Official docs | Persistence context, fetching, batching, locking |
| [Vlad Mihalcea: Hibernate tutorials](https://vladmihalcea.com/tutorials/hibernate/) | Blog | Các bẫy hiệu năng JPA thực tế, có đo SQL sinh ra |

#### [07. Go](07-go.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [A Tour of Go](https://go.dev/tour/) | Tutorial tương tác | Cú pháp, nếu chưa từng viết Go. Khoảng 1 ngày |
| [Effective Go](https://go.dev/doc/effective_go) | Official docs | Idiom: interface, embedding, concurrency, error. Viết trước generics, đọc kèm release notes |
| [The Go Programming Language Specification](https://go.dev/ref/spec) | Đặc tả | Tra khi cần câu trả lời chính xác (method set, assignability) |
| [The Go Memory Model](https://go.dev/ref/mem) | Đặc tả | Happens-before của channel, mutex, atomic |
| [Release notes](https://go.dev/doc/devel/release) | Official docs | Tính năng có từ bản nào. Đọc ít nhất [1.22](https://go.dev/doc/go1.22) tới [1.27](https://go.dev/doc/go1.27) |
| [100 Go Mistakes](https://100go.co/) (Teiva Harsanyi) | Sách + web | Gần như trùng khít với các câu hỏi vặn trong phỏng vấn |
| *The Go Programming Language* (Donovan, Kernighan) | Sách | Ch.4 (slice, map), ch.7 (interface), ch.8–9 (goroutine, channel, concurrency) |
| [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments) | Wiki | Quy ước code review của team Go |

### Giao tiếp giữa các hệ thống

#### [09. Thiết kế API](09-api-design.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [RFC 9110: HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110) | RFC | Nguồn chuẩn cho method, status code, header, conditional request. Khi blog và RFC mâu thuẫn, tin RFC |
| [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/) | Guideline công ty | Bộ quy tắc REST đầy đủ và thực dụng nhất: naming, lỗi, pagination, compatibility, deprecation |
| [Google AIP](https://google.aip.dev/) | Guideline công ty | Custom method, long-running operation, pagination, batch, backward compatibility; dùng cho cả REST và gRPC |
| *API Design Patterns* (JJ Geewax; Manning 2021) | Sách | Viết từ AIP của Google: naming, pagination, LRO, versioning, bulk, soft delete |
| [Stripe API Reference](https://docs.stripe.com/api) | Tài liệu thật | Mẫu API public tốt: idempotency, lỗi, pagination, versioning theo ngày, webhook |
| [OpenAPI Specification 3.2](https://spec.openapis.org/oas/v3.2.0.html) | Spec | Mô tả contract REST; [bản 3.1.1](https://spec.openapis.org/oas/v3.1.1.html) vẫn là bản tooling hỗ trợ rộng nhất |
| [Laravel docs](https://laravel.com/docs/eloquent-resources) | Official docs | API Resources, validation, Sanctum/Passport, rate limiting, HTTP client |

#### [10. Bảo mật](10-security.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/) | Hướng dẫn thực hành | Nguồn tra cứu chính cho gần như mọi module. Mỗi cheat sheet ngắn, có khuyến nghị cụ thể |
| [OWASP Top 10:2025](https://owasp.org/Top10/2025/) và [OWASP API Security Top 10 2023](https://owasp.org/API-Security/editions/2023/en/0x11-t10/) | Danh mục rủi ro | Khung để nói chuyện về lỗ hổng. Người phỏng vấn hay hỏi "kể tên" |
| [PortSwigger Web Security Academy](https://portswigger.net/web-security) | Khoá học + lab miễn phí | Hiểu lỗ hổng bằng cách tự khai thác. **Làm lab** quan trọng hơn đọc lý thuyết |
| [OWASP ASVS](https://github.com/OWASP/ASVS) | Tiêu chuẩn kiểm chứng | Checklist yêu cầu bảo mật theo cấp độ, dùng khi review thiết kế |
| [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html) | Tiêu chuẩn | Password, MFA, authenticator, session (bản chính thức 08/2025) |
| [RFC 9700: OAuth 2.0 Security BCP](https://www.rfc-editor.org/rfc/rfc9700) | RFC (01/2025) | Cách dùng OAuth 2.0 an toàn hiện nay. OAuth 2.1 vẫn là Internet-Draft |
| *Serious Cryptography*, 2nd ed. (Jean-Philippe Aumasson; No Starch 2024) | Sách | Crypto cho kỹ sư: hash, AEAD, RSA/ECC, TLS. Đọc ch.1–4 và phần về authenticated encryption |
| [Laravel docs](https://laravel.com/docs) và [PHP manual: Security](https://www.php.net/manual/en/security.php) | Official docs | Tầng framework: CSRF, auth, authorization, encryption, hashing |

#### [12. Messaging, event-driven, background job](12-messaging.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [Laravel docs: Queues](https://laravel.com/docs/queues) | Official docs | Nguồn chuẩn cho job, worker, retry, batching của stack PHP. **Đọc hết** |
| [Apache Kafka 4.3: Design](https://kafka.apache.org/43/design/design/) | Official docs | Chương thiết kế: persistence, consumer position, delivery semantics, replication, compaction |
| *Kafka: The Definitive Guide*, 2nd ed. (Shapira, Palino, Sivaram, Petty; O'Reilly 2021) | Sách | Producer, consumer, reliability, exactly-once, vận hành. Ra trước Kafka 4.0 nên phần ZooKeeper và rebalance đã cũ |
| [RabbitMQ docs](https://www.rabbitmq.com/docs) | Official docs | Exchange, ack, confirm, quorum queue, stream |
| [Amazon SQS Developer Guide](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html) | Official docs | Visibility timeout, FIFO, DLQ, quota |
| [*Designing Data-Intensive Applications*](https://dataintensive.net/) (Kleppmann) | Sách | Ch.11 stream processing (log-based broker, CDC, event sourcing), ch.12 phần end-to-end argument (số chương theo bản 1) |
| [Enterprise Integration Patterns](https://www.enterpriseintegrationpatterns.com/patterns/messaging/) (Hohpe, Woolf) | Sách + site | Tên gọi chuẩn của các pattern: claim check, DLQ, idempotent receiver, competing consumers |
| [microservices.io patterns](https://microservices.io/patterns/) (Chris Richardson) | Site | Outbox, idempotent consumer, saga, CQRS, event sourcing |

### Hệ thống quy mô lớn

#### [13. Concurrency](13-concurrency.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [OSTEP](https://pages.cs.wisc.edu/~remzi/OSTEP/) (Arpaci-Dusseau), phần *Concurrency* | Sách online miễn phí | Thread, lock, condition variable, semaphore, bug thường gặp. Ngắn, dễ đọc, có bài tập |
| *Java Concurrency in Practice* (Goetz và cộng sự, 2006) | Sách | Vẫn là sách chuẩn về thread safety, visibility, thread pool. Ví dụ bằng Java nhưng tư duy dùng cho mọi ngôn ngữ |
| [The Go Memory Model](https://go.dev/ref/mem) và [Effective Go: Concurrency](https://go.dev/doc/effective_go#concurrency) | Official docs | Goroutine, channel, happens-before trong Go |
| [JLS ch.17: Threads and Locks](https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html) | Đặc tả | Mục 17.4 là Java Memory Model. Đọc sau khi đã hiểu happens-before ở mức ý tưởng |
| [*Designing Data-Intensive Applications*](https://dataintensive.net/) (Kleppmann) | Sách | Ch.7 transactions: race condition ở tầng DB (lost update, write skew). Quan trọng nhất với backend |
| [Laravel docs](https://laravel.com/docs/cache#atomic-locks) | Official docs | Atomic lock, pessimistic locking, unique job, job middleware |
| [The Little Book of Semaphores](https://greenteapress.com/wp/semaphores/) (Downey) | Sách online miễn phí | Bài tập đồng bộ kinh điển, nếu muốn luyện tư duy primitive |

#### [14. Hệ phân tán](14-distributed-systems.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [*Designing Data-Intensive Applications*](https://dataintensive.net/) (Kleppmann) | Sách | **Ch.5 replication, ch.6 partitioning, ch.8 trouble with distributed systems, ch.9 consistency and consensus** (số chương theo bản 1). Xương sống của file này |
| [Raft paper](https://raft.github.io/raft.pdf) và [raft.github.io](https://raft.github.io/) | Paper + trang minh hoạ | Consensus. Paper viết để dễ hiểu, đọc được trong một buổi; trang có mô phỏng chạy trực tiếp |
| [Jepsen](https://jepsen.io/consistency) | Bản đồ consistency model + [phân tích DB thật](https://jepsen.io/analyses) | Định nghĩa chuẩn các model; xem DB nào hứa gì và thực tế vi phạm ra sao |
| [Aphyr (Kyle Kingsbury)](https://aphyr.com/) | Blog | Tác giả Jepsen. Các bài về strong consistency, network partition viết rất dễ hiểu |
| [Martin Kleppmann: How to do distributed locking](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html) | Blog | Lock cho hiệu quả và lock cho đúng đắn, fencing token, phản biện Redlock |
| [Amazon Builders' Library](https://aws.amazon.com/builders-library/) | Blog kỹ thuật | Timeout, retry, jitter, load shedding, idempotency: kinh nghiệm vận hành thật |
| [Google SRE Book](https://sre.google/sre-book/table-of-contents/) | Sách online miễn phí | Ch.21 *Handling Overload*, ch.22 *Addressing Cascading Failures*, ch.23 *Managing Critical State* |

#### [15. Kiến trúc phần mềm](15-architecture.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| *Learning Domain-Driven Design* (Vlad Khononov; O'Reilly 2021) | Sách | Cửa vào DDD dễ nhất: subdomain, bounded context, aggregate, và khi nào **không** cần DDD. Đọc trước sách Evans |
| *Domain-Driven Design* (Eric Evans, 2003) | Sách | Nguồn gốc. Phần IV (strategic design) quan trọng hơn phần tactical |
| *Building Microservices*, 2nd ed. (Sam Newman; O'Reilly 2021) | Sách | Tách service, giao tiếp, dữ liệu, tổ chức team |
| *Monolith to Microservices* (Sam Newman; O'Reilly 2019) | Sách | Strangler fig, tách dữ liệu từng bước; thực dụng nhất cho người đang có monolith Laravel |
| *Fundamentals of Software Architecture*, 2nd ed. (Richards, Ford; O'Reilly 2025) | Sách | Các kiểu kiến trúc, quality attributes, trade-off, ADR |
| [Martin Fowler: Microservices Guide](https://martinfowler.com/articles/microservices.html) | Blog | Bài gốc về microservices và các bài bliki liên quan (MonolithFirst, StranglerFig, BoundedContext) |
| [microservices.io](https://microservices.io/patterns/index.html) (Chris Richardson) | Catalog pattern | Database per service, API composition, saga, CQRS; mỗi pattern có bối cảnh và nhược điểm |
| [Laravel docs](https://laravel.com/docs/octane) | Official docs | Octane, events, Pennant, global scope: chỗ kiến trúc giao với framework |

#### [16. System design](16-system-design.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| *System Design Interview*, vol 1 và vol 2 (Alex Xu; vol 2 viết cùng Sahn Lam) | Sách | Phương pháp và gần như mọi bài kinh điển trong file này. Một phần vol 1 đọc được trên [ByteByteGo](https://bytebytego.com/) |
| [System Design Primer](https://github.com/donnemartin/system-design-primer) | Repo GitHub miễn phí | Building blocks, bảng con số, danh sách bài đọc thêm |
| [*Designing Data-Intensive Applications*](https://dataintensive.net/) (Kleppmann) | Sách | Lý thuyết phía sau: replication, partitioning, stream. Khi người chấm hỏi "vì sao" |
| [Google SRE Book](https://sre.google/sre-book/table-of-contents/) | Sách online miễn phí | Availability, SLO, overload, cascading failure |
| [Amazon Builders' Library](https://aws.amazon.com/builders-library/) | Blog kỹ thuật | Kinh nghiệm vận hành thật: multi-AZ, shuffle sharding, load shedding |
| Blog kỹ thuật công ty (Discord, Slack, Dropbox, Stripe, Shopify...) | Blog | Bài gốc của từng bài kinh điển, dẫn ở từng module |

#### [17. Performance và scalability](17-performance.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [*Systems Performance*, 2nd ed.](https://www.brendangregg.com/systems-performance-2nd-edition-book.html) (Brendan Gregg, 2020) | Sách | Phương pháp luận (USE, workload characterization), công cụ quan sát, profiling |
| [Brendan Gregg: Performance Methodologies](https://www.brendangregg.com/methodology.html) | Blog | Tóm tắt các phương pháp và anti-pattern ("streetlight", "random change") |
| [*Designing Data-Intensive Applications*](https://dataintensive.net/) (Kleppmann) | Sách | Ch.1: latency, percentile, tail latency amplification, cách mô tả tải |
| [The Tail at Scale](https://research.google/pubs/the-tail-at-scale/) (Dean, Barroso, 2013) | Paper | Tail latency khi fan-out, hedged request. Ngắn, đọc hết |
| [Google SRE Book](https://sre.google/sre-book/handling-overload/) | Sách online miễn phí | Chương *Handling Overload* và *Addressing Cascading Failures* |
| [Grafana k6 docs](https://grafana.com/docs/k6/latest/) | Official docs | Load testing, executor, threshold, open/closed model |
| [PHP-FPM](https://www.php.net/manual/en/install.fpm.configuration.php) và [OPcache](https://www.php.net/manual/en/opcache.configuration.php) configuration | Official docs | Tuning tầng PHP |

### Vận hành và chất lượng

#### [18. Reliability và observability](18-reliability-observability.md)

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

#### [19. DevOps và Cloud](19-devops-cloud.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [Docker docs: Building best practices](https://docs.docker.com/build/building/best-practices/) | Official docs | Dockerfile, layer, multi-stage, cache. Đọc hết trang này trước |
| [Kubernetes docs: Concepts](https://kubernetes.io/docs/concepts/workloads/pods/) | Official docs | Nguồn chuẩn cho mọi hành vi của Kubernetes. Mục *Workloads*, *Services*, *Configuration*, *Security* |
| *Kubernetes in Action* (Marko Lukša, Manning) | Sách | Hiểu Kubernetes từ gốc, có hình vẽ luồng pod, service, rollout |
| [learnk8s.io](https://learnk8s.io/production-best-practices) | Blog kỹ thuật | Checklist production, bài graceful shutdown rất chi tiết |
| [Terraform docs](https://developer.hashicorp.com/terraform/language/state) | Official docs | State, backend, module, locking |
| [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html) | Whitepaper | Sáu trụ cột: vận hành, bảo mật, độ tin cậy, hiệu năng, chi phí, bền vững |
| [The Twelve-Factor App](https://12factor.net/) | Bài viết kinh điển | Nguyên tắc app chạy tốt trên container/PaaS. Đọc hết, khoảng 1 giờ |
| [Laravel docs: Deployment](https://laravel.com/docs/deployment), [Queues](https://laravel.com/docs/queues), [Octane](https://laravel.com/docs/octane) | Official docs | Tối ưu khi deploy, worker, runtime chạy lâu |

#### [20. Testing và chất lượng code](20-testing-quality.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [*Software Engineering at Google*](https://abseil.io/resources/swe-book) (Winters, Manshreck, Wright) | Sách online miễn phí | Ch.9 code review, ch.11–14 testing (tổng quan, unit, test double, test lớn). Góc nhìn ở quy mô lớn |
| [Martin Fowler: The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html) | Bài dài | Các loại test, pyramid, contract test, có ví dụ code |
| *Working Effectively with Legacy Code* (Michael Feathers) | Sách | Seam, characterization test, cách đưa test vào code cũ. Đọc phần I và các chương về seam |
| [Laravel: Testing](https://laravel.com/docs/testing) | Official docs | HTTP test, database test, fakes, mocking, parallel test |
| [PHPUnit Manual](https://docs.phpunit.de/) | Official docs | Bản 13.x hiện tại: attribute, test double, data provider, coverage |
| [Pest docs](https://pestphp.com/docs/installation) | Official docs | Cú pháp Pest, browser testing, mutation testing tích hợp |
| [Pro Git](https://git-scm.com/book/en/v2) | Sách online miễn phí | Branching, rebase, công cụ nâng cao |

### Làm việc cùng AI

#### [26. Dùng AI trong công việc và coding](26-ai-assisted-engineering.md)

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

#### [23. Tích hợp AI/LLM vào backend](23-ai-llm-backend.md)

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

### Ngoài kỹ thuật

#### [24. Kỹ năng senior: ra quyết định, giao hàng, dẫn dắt](24-senior-leadership.md)

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

#### [25. Kỹ năng phỏng vấn](25-interview-skills.md)

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [Tech Interview Handbook](https://www.techinterviewhandbook.org/) | Hướng dẫn miễn phí | Resume, behavioral, câu hỏi ngược, negotiation. **Nguồn chính** của file này |
| [Amazon Leadership Principles](https://www.amazon.jobs/content/en/our-workplace/leadership-principles) | Tài liệu công ty | Bộ tiêu chí behavioral được nhiều công ty bắt chước; dùng để kiểm tra kho câu chuyện có phủ đủ không |
| [Anthropic: Guidance on Candidates' AI Usage](https://www.anthropic.com/candidate-ai-guidance) | Chính sách công ty | Ví dụ chính sách **cấm** AI trong vòng live và take-home, cho phép khi chuẩn bị |
| [Canva: Yes, You Can Use AI in Our Interviews](https://www.canva.dev/blog/engineering/yes-you-can-use-ai-in-our-interviews/) | Blog kỹ thuật (6/2025) | Ví dụ vòng **yêu cầu** dùng AI coding assistant và cách họ chấm |
| [ITviec: Báo cáo Lương IT](https://itviec.com/bao-cao/luong-it-va-thi-truong-tuyen-dung-it-vietnam) | Báo cáo thị trường | Mặt bằng lương IT Việt Nam theo vị trí, số năm kinh nghiệm |
| [levels.fyi](https://www.levels.fyi/t/software-engineer/locations/vietnam) | Dữ liệu lương tự khai | Lương theo level ở công ty nước ngoài/product có văn phòng tại Việt Nam |
| Glassdoor (glassdoor.com) | Review công ty | Review quy trình phỏng vấn và văn hoá. Mẫu nhỏ ở Việt Nam, đọc có chọn lọc |

## 2. Sách

Gom từ bảng tài liệu nền của mọi chủ đề. Sách online miễn phí nằm ở mục 1.

| Sách | Chủ đề | Dùng cho |
|---|---|---|
| [100 Go Mistakes](https://100go.co/) (Teiva Harsanyi) | [07](07-go.md) | Gần như trùng khít với các câu hỏi vặn trong phỏng vấn |
| [*Accelerate*](https://itrevolution.com/product/accelerate/) (Forsgren, Humble, Kim) và [DORA](https://dora.dev/) | [24](24-senior-leadership.md) | Đo năng lực giao hàng bằng số liệu thay vì cảm tính |
| *AI Engineering* (Chip Huyen, O'Reilly 2025) | [23](23-ai-llm-backend.md) | Toàn cảnh xây ứng dụng trên foundation model: eval, RAG, agent, tối ưu inference |
| [*Algorithms*, 4th ed.](https://algs4.cs.princeton.edu/home/) (Sedgewick, Wayne) | [21](21-dsa.md) | Giải thích từng cấu trúc có hình và code. Chương nào đọc ghi ở từng module |
| [*An Elegant Puzzle*](https://lethain.com/elegant-puzzle/) (Will Larson, 2019) | [24](24-senior-leadership.md) | Migration, tech debt, sizing team; góc nhìn của engineering manager giúp hiểu người phỏng vấn |
| *API Design Patterns* (JJ Geewax; Manning 2021) | [09](09-api-design.md) | Viết từ AIP của Google: naming, pagination, LRO, versioning, bulk, soft delete |
| *Building Microservices*, 2nd ed. (Sam Newman; O'Reilly 2021) | [15](15-architecture.md) | Tách service, giao tiếp, dữ liệu, tổ chức team |
| [*Computer Networking: A Top-Down Approach*](https://gaia.cs.umass.edu/kurose_ross/) (Kurose, Ross) | [02](02-networking.md) | Nền lý thuyết nếu chưa học mạng bài bản: chương 2 (application), 3 (transport) |
| *Design Patterns* (Gamma, Helm, Johnson, Vlissides; 1994) | [08](08-oop-design.md) | Nguồn gốc 23 pattern GoF. Đọc chương 1 (nguyên tắc "program to an interface", "favor composition") và tra từng pattern khi cần |
| [*Designing Data-Intensive Applications*](https://dataintensive.net/) (Kleppmann) | [03](03-database-sql.md) [04](04-nosql-search-storage.md) [11](11-cache.md) [12](12-messaging.md) [13](13-concurrency.md) [14](14-distributed-systems.md) [16](16-system-design.md) [17](17-performance.md) | Ch.3 storage, ch.5 replication, ch.6 partitioning, **ch.7 transactions** (số chương theo bản 1) |
| *Domain-Driven Design* (Eric Evans, 2003) | [15](15-architecture.md) | Nguồn gốc. Phần IV (strategic design) quan trọng hơn phần tactical |
| *Effective Java*, 3rd ed. (Bloch) | [06](06-java-spring.md) [08](08-oop-design.md) | Đối chiếu: item 1 (static factory), item 17 (immutability), item 18 (composition thay kế thừa) |
| [Enterprise Integration Patterns](https://www.enterpriseintegrationpatterns.com/patterns/messaging/) (Hohpe, Woolf) | [12](12-messaging.md) | Tên gọi chuẩn của các pattern: claim check, DLQ, idempotent receiver, competing consumers |
| *Fundamentals of Software Architecture*, 2nd ed. (Richards, Ford; O'Reilly 2025) | [15](15-architecture.md) | Các kiểu kiến trúc, quality attributes, trade-off, ADR |
| *High Performance MySQL*, 4th ed. (Botros, Tinley; O'Reilly 2021) | [03](03-database-sql.md) | Schema, index, query, replication, vận hành MySQL |
| *Introduction to Algorithms* (CLRS), 4th ed. (MIT Press 2022) | [21](21-dsa.md) | Tra cứu khi cần chứng minh hoặc phân tích chặt. Không cần đọc hết |
| *Java Concurrency in Practice* (Goetz và cộng sự) | [06](06-java-spring.md) [13](13-concurrency.md) | Ch.2–3 (thread safety, visibility), ch.6–8 (executor, pool). Cũ nhưng nền tảng không đổi |
| *Kafka: The Definitive Guide*, 2nd ed. (Shapira, Palino, Sivaram, Petty; O'Reilly 2021) | [12](12-messaging.md) | Producer, consumer, reliability, exactly-once, vận hành. Ra trước Kafka 4.0 nên phần ZooKeeper và rebalance đã cũ |
| *Kubernetes in Action* (Marko Lukša, Manning) | [19](19-devops-cloud.md) | Hiểu Kubernetes từ gốc, có hình vẽ luồng pod, service, rollout |
| *Learning Domain-Driven Design* (Vlad Khononov; O'Reilly 2021) | [15](15-architecture.md) | Cửa vào DDD dễ nhất: subdomain, bounded context, aggregate, và khi nào **không** cần DDD. Đọc trước sách Evans |
| *Monolith to Microservices* (Sam Newman; O'Reilly 2019) | [15](15-architecture.md) | Strangler fig, tách dữ liệu từng bước; thực dụng nhất cho người đang có monolith Laravel |
| *Observability Engineering* (Majors, Fong-Jones, Miranda; O'Reilly 2022) | [18](18-reliability-observability.md) | Observability khác monitoring ở đâu, event có nhiều chiều, SLO-based alerting |
| [*Patterns of Enterprise Application Architecture*](https://martinfowler.com/eaaCatalog/) (Fowler) | [08](08-oop-design.md) | Repository, Unit of Work, Active Record, Data Mapper, Identity Map |
| *Refactoring*, 2nd ed. (Fowler, 2018) và [catalog](https://refactoring.com/catalog/) | [08](08-oop-design.md) | Code smell (ch.3), các kỹ thuật refactoring, cách refactor từng bước nhỏ |
| *Serious Cryptography*, 2nd ed. (Jean-Philippe Aumasson; No Starch 2024) | [10](10-security.md) | Crypto cho kỹ sư: hash, AEAD, RSA/ECC, TLS. Đọc ch.1–4 và phần về authenticated encryption |
| [*Staff Engineer*](https://staffeng.com/guides/) (Will Larson, staffeng.com) | [24](24-senior-leadership.md) | Các guide ngắn: chọn việc quan trọng, quản lý chất lượng kỹ thuật, làm việc với cấp trên |
| *System Design Interview*, vol 1 và vol 2 (Alex Xu; vol 2 viết cùng Sahn Lam) | [16](16-system-design.md) | Phương pháp và gần như mọi bài kinh điển trong file này. Một phần vol 1 đọc được trên [ByteByteGo](https://bytebytego.com/) |
| [*Systems Performance*, 2nd ed.](https://www.brendangregg.com/systems-performance-2nd-edition-book.html) (Brendan Gregg, 2020) | [01](01-os-linux.md) [17](17-performance.md) | Linux dưới góc vận hành: CPU, memory, disk, network, công cụ quan sát. Sách gối đầu của SRE |
| [DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html) và [*The DynamoDB Book*](https://www.dynamodbbook.com/) (Alex DeBrie) | [04](04-nosql-search-storage.md) | Query-first modeling, single-table design |
| *The Go Programming Language* (Donovan, Kernighan) | [07](07-go.md) | Ch.4 (slice, map), ch.7 (interface), ch.8–9 (goroutine, channel, concurrency) |
| [Linux man-pages](https://man7.org/linux/man-pages/) và [*The Linux Programming Interface*](https://man7.org/tlpi/) (Kerrisk) | [01](01-os-linux.md) | Nguồn chuẩn cho syscall, signal, `/proc`. Khi blog và man page mâu thuẫn, tin man page |
| *The Staff Engineer's Path* (Tanya Reilly, O'Reilly 2022) | [24](24-senior-leadership.md) | Big picture, thực thi dự án, nâng cả team. Đọc được từ senior, không cần đợi lên staff. Tác giả có [trang tổng hợp về staff engineering](https://www.noidea.dog/staff) |
| *Working Effectively with Legacy Code* (Feathers, 2004) | [08](08-oop-design.md) [20](20-testing-quality.md) | Seam, characterization test, đưa code không test vào kiểm soát |

## 3. Được dẫn nhiều nhất

Các trang được từ 3 chủ đề trở lên dẫn tới.

| Tài liệu | Số chủ đề | Chủ đề |
|---|---|---|
| [FPM configuration](https://www.php.net/manual/en/install.fpm.configuration.php) | 9 | [01](01-os-linux.md) [02](02-networking.md) [05](05-php-laravel.md) [06](06-java-spring.md) [07](07-go.md) [16](16-system-design.md) [17](17-performance.md) [18](18-reliability-observability.md) [19](19-devops-cloud.md) |
| [Queues](https://laravel.com/docs/queues) | 9 | [01](01-os-linux.md) [03](03-database-sql.md) [05](05-php-laravel.md) [11](11-cache.md) [12](12-messaging.md) [13](13-concurrency.md) [19](19-devops-cloud.md) [20](20-testing-quality.md) [23](23-ai-llm-backend.md) |
| [Designing Data-Intensive Applications](https://dataintensive.net) | 8 | [03](03-database-sql.md) [04](04-nosql-search-storage.md) [11](11-cache.md) [12](12-messaging.md) [13](13-concurrency.md) [14](14-distributed-systems.md) [16](16-system-design.md) [17](17-performance.md) |
| [Eloquent](https://laravel.com/docs/eloquent) | 8 | [03](03-database-sql.md) [05](05-php-laravel.md) [08](08-oop-design.md) [09](09-api-design.md) [10](10-security.md) [15](15-architecture.md) [17](17-performance.md) [22](22-practical-data.md) |
| [Octane](https://laravel.com/docs/octane) | 7 | [01](01-os-linux.md) [05](05-php-laravel.md) [08](08-oop-design.md) [13](13-concurrency.md) [15](15-architecture.md) [17](17-performance.md) [19](19-devops-cloud.md) |
| [Task Scheduling](https://laravel.com/docs/scheduling) | 7 | [01](01-os-linux.md) [05](05-php-laravel.md) [12](12-messaging.md) [16](16-system-design.md) [17](17-performance.md) [19](19-devops-cloud.md) [22](22-practical-data.md) |
| [Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter) | 6 | [02](02-networking.md) [09](09-api-design.md) [14](14-distributed-systems.md) [17](17-performance.md) [18](18-reliability-observability.md) [23](23-ai-llm-backend.md) |
| [Deployment](https://laravel.com/docs/deployment) | 5 | [02](02-networking.md) [05](05-php-laravel.md) [17](17-performance.md) [18](18-reliability-observability.md) [19](19-devops-cloud.md) |
| [HTTP Client](https://laravel.com/docs/http-client) | 5 | [05](05-php-laravel.md) [09](09-api-design.md) [17](17-performance.md) [20](20-testing-quality.md) [23](23-ai-llm-backend.md) |
| [Configuration](https://laravel.com/docs/configuration) | 4 | [05](05-php-laravel.md) [10](10-security.md) [15](15-architecture.md) [22](22-practical-data.md) |
| [Events](https://laravel.com/docs/events) | 4 | [05](05-php-laravel.md) [08](08-oop-design.md) [15](15-architecture.md) [20](20-testing-quality.md) |
| [Feature Toggles](https://martinfowler.com/articles/feature-toggles.html) | 4 | [15](15-architecture.md) [19](19-devops-cloud.md) [20](20-testing-quality.md) [24](24-senior-leadership.md) |
| [Implementing Stripe-like Idempotency Keys in Postgres](https://brandur.org/idempotency-keys) | 4 | [09](09-api-design.md) [13](13-concurrency.md) [16](16-system-design.md) [22](22-practical-data.md) |
| [laravel.com/docs/helpers](https://laravel.com/docs/helpers) | 4 | [05](05-php-laravel.md) [08](08-oop-design.md) [11](11-cache.md) [22](22-practical-data.md) |
| [Mutators & Casting](https://laravel.com/docs/eloquent-mutators) | 4 | [05](05-php-laravel.md) [10](10-security.md) [15](15-architecture.md) [22](22-practical-data.md) |
| [OPcache configuration](https://www.php.net/manual/en/opcache.configuration.php) | 4 | [01](01-os-linux.md) [05](05-php-laravel.md) [17](17-performance.md) [19](19-devops-cloud.md) |
| [444 Virtual Threads](https://openjdk.org/jeps/444) | 3 | [01](01-os-linux.md) [06](06-java-spring.md) [13](13-concurrency.md) |
| [491 Synchronize Virtual Threads without Pinning](https://openjdk.org/jeps/491) | 3 | [01](01-os-linux.md) [06](06-java-spring.md) [13](13-concurrency.md) |
| [A Guide to the Go Garbage Collector](https://go.dev/doc/gc-guide) | 3 | [01](01-os-linux.md) [07](07-go.md) [17](17-performance.md) |
| [Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures) | 3 | [14](14-distributed-systems.md) [17](17-performance.md) [18](18-reliability-observability.md) |
| [adr.github.io](https://adr.github.io) | 3 | [15](15-architecture.md) [20](20-testing-quality.md) [24](24-senior-leadership.md) |
| [Baseline](https://phpstan.org/user-guide/baseline) | 3 | [05](05-php-laravel.md) [08](08-oop-design.md) [20](20-testing-quality.md) |
| [Cache](https://laravel.com/docs/cache) | 3 | [05](05-php-laravel.md) [11](11-cache.md) [13](13-concurrency.md) |
| [Cluster specification](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec) | 3 | [04](04-nosql-search-storage.md) [14](14-distributed-systems.md) [21](21-dsa.md) |
| [Container-aware GOMAXPROCS](https://go.dev/blog/container-aware-gomaxprocs) | 3 | [01](01-os-linux.md) [07](07-go.md) [19](19-devops-cloud.md) |
| [Data Race Detector](https://go.dev/doc/articles/race_detector) | 3 | [07](07-go.md) [13](13-concurrency.md) [20](20-testing-quality.md) |
| [Designing robust and predictable APIs with idempotency](https://stripe.com/blog/idempotency) | 3 | [09](09-api-design.md) [12](12-messaging.md) [16](16-system-design.md) |
| [Diagnosing latency](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency) | 3 | [01](01-os-linux.md) [04](04-nosql-search-storage.md) [11](11-cache.md) |
| [Effective Go](https://go.dev/doc/effective_go) | 3 | [07](07-go.md) [08](08-oop-design.md) [13](13-concurrency.md) |
| [Eloquent Relationships](https://laravel.com/docs/eloquent-relationships) | 3 | [03](03-database-sql.md) [05](05-php-laravel.md) [17](17-performance.md) |
| [HikariCP: About Pool Sizing](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing) | 3 | [06](06-java-spring.md) [13](13-concurrency.md) [17](17-performance.md) |
| [Horizon](https://laravel.com/docs/horizon) | 3 | [05](05-php-laravel.md) [12](12-messaging.md) [18](18-reliability-observability.md) |
| [Idempotent requests](https://docs.stripe.com/api/idempotent_requests) | 3 | [09](09-api-design.md) [13](13-concurrency.md) [22](22-practical-data.md) |
| [laravel.com/docs/responses](https://laravel.com/docs/responses) | 3 | [11](11-cache.md) [22](22-practical-data.md) [23](23-ai-llm-backend.md) |
| [Paging Through Results](https://use-the-index-luke.com/sql/partial-results/fetch-next-page) | 3 | [03](03-database-sql.md) [09](09-api-design.md) [17](17-performance.md) |
| [Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle) | 3 | [01](01-os-linux.md) [02](02-networking.md) [19](19-devops-cloud.md) |
| [Pulse](https://laravel.com/docs/pulse) | 3 | [05](05-php-laravel.md) [17](17-performance.md) [18](18-reliability-observability.md) |
| [Rate Limiting](https://laravel.com/docs/rate-limiting) | 3 | [09](09-api-design.md) [10](10-security.md) [16](16-system-design.md) |
| [Rector documentation](https://getrector.com/documentation) | 3 | [05](05-php-laravel.md) [08](08-oop-design.md) [20](20-testing-quality.md) |
| [RFC 9562](https://www.rfc-editor.org/rfc/rfc9562) | 3 | [03](03-database-sql.md) [14](14-distributed-systems.md) [22](22-practical-data.md) |
| [Routing](https://laravel.com/docs/routing) | 3 | [05](05-php-laravel.md) [09](09-api-design.md) [16](16-system-design.md) |
| [Saga](https://microservices.io/patterns/data/saga.html) | 3 | [12](12-messaging.md) [14](14-distributed-systems.md) [15](15-architecture.md) |
| [Sanctum](https://laravel.com/docs/sanctum) | 3 | [05](05-php-laravel.md) [09](09-api-design.md) [10](10-security.md) |
| [Service Container](https://laravel.com/docs/container) | 3 | [05](05-php-laravel.md) [06](06-java-spring.md) [08](08-oop-design.md) |
| [Sorted sets](https://redis.io/docs/latest/develop/data-types/sorted-sets) | 3 | [04](04-nosql-search-storage.md) [16](16-system-design.md) [21](21-dsa.md) |
| [Strangler Fig Application](https://martinfowler.com/bliki/StranglerFigApplication.html) | 3 | [15](15-architecture.md) [20](20-testing-quality.md) [24](24-senior-leadership.md) |
| [Telescope](https://laravel.com/docs/telescope) | 3 | [05](05-php-laravel.md) [17](17-performance.md) [18](18-reliability-observability.md) |
| [Using load shedding to avoid overload](https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload) | 3 | [14](14-distributed-systems.md) [17](17-performance.md) [18](18-reliability-observability.md) |

## 4. Chỉ mục theo module

Bấm vào từng chủ đề để mở danh sách.

### Nền tảng

<details>
<summary><strong>01. Hệ điều hành và Linux</strong> (15 module, 85 link)</summary>

Học chi tiết: [01-os-linux.md](01-os-linux.md)

**1.1 Process và thread**

- man: [clone(2)](https://man7.org/linux/man-pages/man2/clone.2.html) (bảng cờ `CLONE_*`), [fork(2)](https://man7.org/linux/man-pages/man2/fork.2.html), [wait(2)](https://man7.org/linux/man-pages/man2/wait.2.html)
- man: [proc(5)](https://man7.org/linux/man-pages/man5/proc.5.html), mục `/proc/pid/status` và `/proc/pid/stat` (ý nghĩa các ký tự trạng thái)
- OSTEP: chương *Processes*, *Process API*, *Concurrency and Threads*

**1.2 Bộ nhớ cơ bản**

- Kernel docs: [Memory Management Concepts](https://docs.kernel.org/admin-guide/mm/concepts.html)
- man: [proc(5)](https://man7.org/linux/man-pages/man5/proc.5.html), mục `/proc/pid/smaps` (RSS, PSS, shared/private)
- OSTEP: các chương *Address Spaces*, *Paging: Introduction*, *Paging: Faster Translations (TLBs)*, *Swapping: Mechanisms*

**1.3 File system và permission**

- man: [inode(7)](https://man7.org/linux/man-pages/man7/inode.7.html), [symlink(7)](https://man7.org/linux/man-pages/man7/symlink.7.html), [path_resolution(7)](https://man7.org/linux/man-pages/man7/path_resolution.7.html) (quyền `x` trên thư mục)
- OSTEP: chương *Files and Directories*

**1.4 Linux thực hành**

- [The Art of Command Line](https://github.com/jlevy/the-art-of-command-line): lướt một lượt, đánh dấu lệnh chưa biết
- man: [ss(8)](https://man7.org/linux/man-pages/man8/ss.8.html), [lsof(8)](https://man7.org/linux/man-pages/man8/lsof.8.html), [vmstat(8)](https://man7.org/linux/man-pages/man8/vmstat.8.html), [iostat(1)](https://man7.org/linux/man-pages/man1/iostat.1.html), [journalctl(1)](https://man7.org/linux/man-pages/man1/journalctl.1.html)
- OpenSSH: [ssh(1)](https://man.openbsd.org/ssh) (mục `-J`, `-L`), [ssh_config(5)](https://man.openbsd.org/ssh_config)

**2.1 Scheduling và mô hình chạy của runtime**

- man: [sched(7)](https://man7.org/linux/man-pages/man7/sched.7.html); kernel docs: [EEVDF Scheduler](https://docs.kernel.org/scheduler/sched-eevdf.html)
- [JEP 444: Virtual Threads](https://openjdk.org/jeps/444) (mục *Pinning*), [JEP 491](https://openjdk.org/jeps/491)
- Laravel: [Octane](https://laravel.com/docs/octane), mục [Dependency Injection and Octane](https://laravel.com/docs/octane#dependency-injection-and-octane) và [Managing Memory Leaks](https://laravel.com/docs/octane#managing-memory-leaks)
- OSTEP: chương *Scheduling: Introduction*, *Multi-level Feedback*, *Proportional Share*
- Đối chiếu concurrency: [13-concurrency.md](13-concurrency.md)

**2.2 File descriptor và I/O**

- man: [epoll(7)](https://man7.org/linux/man-pages/man7/epoll.7.html) (đọc kỹ mục edge-triggered và Q&A cuối trang), [select(2)](https://man7.org/linux/man-pages/man2/select.2.html)
- systemd: [systemd.exec(5)](https://man7.org/linux/man-pages/man5/systemd.exec.5.html), mục `LimitNOFILE=`
- *Systems Performance*: chương *Operating Systems* (phần I/O models)

**2.3 Signal và graceful shutdown**

- man: [signal(7)](https://man7.org/linux/man-pages/man7/signal.7.html) (bảng action mặc định), [logrotate(8)](https://man7.org/linux/man-pages/man8/logrotate.8.html) (mục `copytruncate`, `postrotate`)
- PHP-FPM: [man page php-fpm(8)](https://github.com/php/php-src/blob/master/sapi/fpm/php-fpm.8.in) (mục *SIGNALS*), [`process_control_timeout`](https://www.php.net/manual/en/install.fpm.configuration.php)
- Kubernetes: [Pod termination](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination)
- Laravel: [Queue Workers and Deployment](https://laravel.com/docs/queues#queue-workers-and-deployment), [Job Expirations and Timeouts](https://laravel.com/docs/queues#job-expirations-and-timeouts)
- Chi tiết trong bối cảnh deploy: [19-devops-cloud.md](19-devops-cloud.md)

**2.4 Bộ nhớ khi vận hành: swap, OOM, leak**

- Kernel docs: [sysctl/vm](https://docs.kernel.org/admin-guide/sysctl/vm.html) (mục `swappiness`, `overcommit_memory`, `oom_kill_allocating_task`)
- Kubernetes: [Swap memory management](https://kubernetes.io/docs/concepts/cluster-administration/swap-memory-management/), blog [Tuning Linux Swap for Kubernetes](https://kubernetes.io/blog/2025/08/19/tuning-linux-swap-for-kubernetes-a-deep-dive/)
- PHP: [`memory_limit`](https://www.php.net/manual/en/ini.core.php#ini.memory-limit), [Garbage Collection](https://www.php.net/manual/en/features.gc.php) (refcount và cycle collector)

**2.5 systemd, cron, shell script**

- man: [systemd.service(5)](https://man7.org/linux/man-pages/man5/systemd.service.5.html) (mục `Restart=`, `Type=`), [systemd.timer(5)](https://man7.org/linux/man-pages/man5/systemd.timer.5.html), [crontab(5)](https://man7.org/linux/man-pages/man5/crontab.5.html), [flock(1)](https://man7.org/linux/man-pages/man1/flock.1.html), [rm(1)](https://man7.org/linux/man-pages/man1/rm.1.html) (`--preserve-root`)
- [BashFAQ/105](https://mywiki.wooledge.org/BashFAQ/105): vì sao `set -e` không làm điều bạn nghĩ
- [ShellCheck](https://www.shellcheck.net/)
- Laravel: [Preventing Task Overlaps](https://laravel.com/docs/scheduling#preventing-task-overlaps), [Running Tasks on One Server](https://laravel.com/docs/scheduling#running-tasks-on-one-server)

**2.6 Tầng PHP: PHP-FPM nhìn từ OS**

- PHP: [FPM configuration](https://www.php.net/manual/en/install.fpm.configuration.php), đọc các mục [`pm`](https://www.php.net/manual/en/install.fpm.configuration.php#pm), [`pm.max-children`](https://www.php.net/manual/en/install.fpm.configuration.php#pm.max-children), [`request_terminate_timeout`](https://www.php.net/manual/en/install.fpm.configuration.php#request-terminate-timeout), `pm.status_path`, `slowlog`
- PHP: [`max_execution_time`](https://www.php.net/manual/en/info.configuration.php#ini.max-execution-time) (đọc ghi chú về non-Windows), [OPcache configuration](https://www.php.net/manual/en/opcache.configuration.php) (mục [`validate_timestamps`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.validate-timestamps), [`memory_consumption`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.memory-consumption))
- [cachetool](https://github.com/gordalina/cachetool): reset OPcache của FPM từ dòng lệnh
- Chi tiết runtime PHP và Laravel: [05-php-laravel.md](05-php-laravel.md)

**3.1 Container: cgroup, namespace, PID 1**

- Kernel docs: [Control Group v2](https://docs.kernel.org/admin-guide/cgroup-v2.html), mục *Memory* (`memory.max`, `memory.high`, `memory.stat`) và *CPU*
- man: [namespaces(7)](https://man7.org/linux/man-pages/man7/namespaces.7.html), [pid_namespaces(7)](https://man7.org/linux/man-pages/man7/pid_namespaces.7.html) (mục về init process và signal)
- Docker: [Shell and exec form](https://docs.docker.com/reference/dockerfile/#shell-and-exec-form), [`--init`](https://docs.docker.com/reference/cli/docker/container/run/#init); [tini](https://github.com/krallin/tini) README
- Go blog: [Container-aware GOMAXPROCS](https://go.dev/blog/container-aware-gomaxprocs); [Go GC guide](https://go.dev/doc/gc-guide) (mục memory limit)
- Kubernetes: [Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)

**3.2 CPU khi vận hành: load average, steal, throttling**

- Brendan Gregg: [Linux Load Averages: Solving the Mystery](https://www.brendangregg.com/blog/2017-08-08/linux-load-averages.html), [The USE Method](https://www.brendangregg.com/usemethod.html)
- Kernel docs: [CFS Bandwidth Control](https://docs.kernel.org/scheduler/sched-bwc.html)
- *Systems Performance*: chương *CPUs*

**3.3 I/O nâng cao: fsync, zero-copy, io_uring**

- man: [fsync(2)](https://man7.org/linux/man-pages/man2/fsync.2.html), [rename(2)](https://man7.org/linux/man-pages/man2/rename.2.html), [sendfile(2)](https://man7.org/linux/man-pages/man2/sendfile.2.html), [io_uring(7)](https://man7.org/linux/man-pages/man7/io_uring.7.html)
- LWN: [Ensuring data reaches disk](https://lwn.net/Articles/457667/)
- Dan Luu: [Files are hard](https://danluu.com/file-consistency/): vì sao ghi file bền vững khó hơn tưởng

**3.4 Copy-on-write, fork và huge page**

- man: [fork(2)](https://man7.org/linux/man-pages/man2/fork.2.html) (mục copy-on-write)
- Kernel docs: [Transparent Hugepage Support](https://docs.kernel.org/admin-guide/mm/transhuge.html)
- Redis: [Administration](https://redis.io/docs/latest/operate/oss_and_stack/management/admin/) (overcommit, THP), [Diagnosing latency](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/) (mục fork và THP)
- MongoDB: [TCMalloc Performance Optimization](https://www.mongodb.com/docs/manual/administration/tcmalloc-performance/)

**3.5 Debug production có phương pháp**

- Brendan Gregg: [Linux perf examples](https://www.brendangregg.com/perf.html), [eBPF tools](https://www.brendangregg.com/ebpf.html), [Flame Graphs](https://www.brendangregg.com/flamegraphs.html)
- man: [strace(1)](https://man7.org/linux/man-pages/man1/strace.1.html), [pidstat(1)](https://man7.org/linux/man-pages/man1/pidstat.1.html)
- *Systems Performance*: chương *Methodologies* và *Observability Tools*

</details>

<details>
<summary><strong>02. Mạng: TCP, DNS, HTTP, TLS, proxy, load balancer</strong> (18 module, 77 link)</summary>

Học chi tiết: [02-networking.md](02-networking.md)

**1.1 Tầng mạng, TCP và UDP**

- HPBN: chương [Building Blocks of TCP](https://hpbn.co/building-blocks-of-tcp/) (handshake, slow start, head-of-line blocking)
- [RFC 9293](https://www.rfc-editor.org/rfc/rfc9293) (TCP): mục 3.5 (connection establishment), tra cứu khi cần
- Kurose & Ross: chương 3, phần 3.5 (TCP)

**1.2 DNS cơ bản**

- [Julia Evans: A DNS resolver in 80 lines of Go](https://jvns.ca/blog/2022/02/01/a-dns-resolver-in-80-lines-of-go/): hiểu phân giải đệ quy bằng cách viết một cái
- `man dig`; thử `dig +trace example.com`

**1.3 HTTP cơ bản**

- MDN: [HTTP request methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods), [Idempotent](https://developer.mozilla.org/en-US/docs/Glossary/Idempotent), [Status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status), [Cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies)
- RFC 9110: mục [9.2.1 Safe Methods](https://www.rfc-editor.org/rfc/rfc9110#section-9.2.1) và [9.2.2 Idempotent Methods](https://www.rfc-editor.org/rfc/rfc9110#section-9.2.2)

**1.4 HTTPS cơ bản**

- HPBN: chương [Transport Layer Security](https://hpbn.co/transport-layer-security-tls/) (chain of trust, session resumption)
- [The Illustrated TLS 1.3 Connection](https://tls13.xargs.org/): lướt để thấy handshake thật trông thế nào

**1.5 Gõ URL rồi Enter**

- MDN: [How browsers work](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/How_browsers_work)
- [everything curl: write-out](https://everything.curl.dev/usingcurl/verbose/writeout.html): đo từng giai đoạn bằng `curl -w`

**2.1 TCP khi vận hành: đóng kết nối, keep-alive, pool**

- Vincent Bernat: [Coping with the TCP TIME-WAIT state on busy Linux servers](https://vincent.bernat.ch/en/blog/2014-tcp-time-wait-state-linux)
- man: [tcp(7)](https://man7.org/linux/man-pages/man7/tcp.7.html) (mục `tcp_tw_reuse`, `tcp_keepalive_time`)
- Cloudflare: [This is strictly a violation of the TCP specification](https://blog.cloudflare.com/this-is-strictly-a-violation-of-the-tcp-specification/) (một sự cố thật về `CLOSE_WAIT`)

**2.2 HTTP/1.1, HTTP/2, HTTP/3 và gRPC**

- HPBN: chương [HTTP/2](https://hpbn.co/http2/)
- [HTTP/3 explained](https://http3-explained.haxx.se/) (Daniel Stenberg, tác giả curl)
- gRPC: [Core concepts](https://grpc.io/docs/what-is-grpc/core-concepts/); Protobuf: [Overview](https://protobuf.dev/overview/)
- Tra cứu: [RFC 9113](https://www.rfc-editor.org/rfc/rfc9113) (HTTP/2), [RFC 9114](https://www.rfc-editor.org/rfc/rfc9114) (HTTP/3), [RFC 9000](https://www.rfc-editor.org/rfc/rfc9000) (QUIC)

**2.3 HTTP caching, compression, range, CORS**

- MDN: [HTTP caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching) (đọc hết), [CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)
- RFC 9111: mục [5.2 Cache-Control](https://www.rfc-editor.org/rfc/rfc9111#section-5.2)

**2.4 TLS nâng cao**

- [RFC 8446](https://www.rfc-editor.org/rfc/rfc8446) (TLS 1.3): mục 2 (protocol overview) và 8 (0-RTT and anti-replay)
- Cloudflare: [The state of the post-quantum Internet](https://blog.cloudflare.com/pq-2024/)
- Let's Encrypt: [Ending OCSP Support in 2025](https://letsencrypt.org/2024/12/05/ending-ocsp/), [OCSP Service Has Reached End of Life](https://letsencrypt.org/2025/08/06/ocsp-service-has-reached-end-of-life/)
- CA/B Forum: [Ballot SC-081v3](https://cabforum.org/2025/04/11/ballot-sc081v3-introduce-schedule-of-reducing-validity-and-data-reuse-periods/) (bảng lộ trình rút ngắn hạn cert)
- MDN: [Strict-Transport-Security](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Strict-Transport-Security); [hstspreload.org](https://hstspreload.org/) (đọc điều kiện và cách gỡ)

**2.5 Reverse proxy, Nginx, X-Forwarded-For**

- Nginx: [ngx_http_proxy_module](https://nginx.org/en/docs/http/ngx_http_proxy_module.html) (mục [`proxy_http_version`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_http_version), [`proxy_buffering`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_buffering), [`proxy_read_timeout`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_read_timeout)), [upstream `keepalive`](https://nginx.org/en/docs/http/ngx_http_upstream_module.html#keepalive), [realip](https://nginx.org/en/docs/http/ngx_http_realip_module.html), [limit_req](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html)
- Nginx blog: [Rate Limiting with NGINX](https://blog.nginx.org/blog/rate-limiting-nginx) (giải thích `burst` và `nodelay` bằng hình)
- Laravel: [Configuring Trusted Proxies](https://laravel.com/docs/requests#configuring-trusted-proxies)
- [RFC 7239](https://www.rfc-editor.org/rfc/rfc7239) (header `Forwarded` chuẩn hoá)

**2.6 Tầng PHP: Nginx + PHP-FPM qua FastCGI**

- Nginx: [ngx_http_fastcgi_module](https://nginx.org/en/docs/http/ngx_http_fastcgi_module.html) (mục [`fastcgi_read_timeout`](https://nginx.org/en/docs/http/ngx_http_fastcgi_module.html#fastcgi_read_timeout), [`fastcgi_keep_conn`](https://nginx.org/en/docs/http/ngx_http_fastcgi_module.html#fastcgi_keep_conn)), wiki [PHP FastCGI Example](https://www.nginx.com/resources/wiki/start/topics/examples/phpfcgi/) (đọc phần cảnh báo bảo mật)
- Laravel: [Deployment: Nginx](https://laravel.com/docs/deployment#nginx) (cấu hình mẫu chính thức)
- PHP: [FPM configuration](https://www.php.net/manual/en/install.fpm.configuration.php) (`listen`, `listen.backlog`, `request_terminate_timeout`)
- [FastCGI Specification](https://fastcgi-archives.github.io/FastCGI_Specification.html): lướt mục 3 (protocol basics) để biết record trông thế nào
- Chi tiết process model của FPM: [01-os-linux.md](01-os-linux.md), runtime PHP: [05-php-laravel.md](05-php-laravel.md)

**2.7 Load balancer, health check, CDN**

- gRPC blog: [gRPC Load Balancing](https://grpc.io/blog/grpc-load-balancing/)
- Nginx: [HTTP Load Balancing](https://docs.nginx.com/nginx/admin-guide/load-balancer/http-load-balancer/) (thuật toán, health check passive)
- AWS: [Application Load Balancer attributes](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html) (idle timeout, deregistration delay)
- Kubernetes: [Pod termination](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination) (vì sao cần `preStop`)

**2.8 Timeout và mã lỗi giữa proxy và app**

- AWS Builders' Library: [Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)
- Nginx: [`proxy_read_timeout`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_read_timeout), [`client_max_body_size`](https://nginx.org/en/docs/http/ngx_http_core_module.html#client_max_body_size)
- Resilience chi tiết: [18-reliability-observability.md](18-reliability-observability.md)

**3.1 TCP chuyên sâu: hiệu năng, port exhaustion, SYN flood**

- HPBN: chương [Building Blocks of TCP](https://hpbn.co/building-blocks-of-tcp/) (flow control, slow start, BDP)
- Cloudflare: [SYN packet handling in the wild](https://blog.cloudflare.com/syn-packet-handling-in-the-wild/) (SYN queue, accept queue, SYN cookies, cách quan sát)
- [RFC 4987](https://www.rfc-editor.org/rfc/rfc4987): TCP SYN flooding attacks and common mitigations
- Kernel docs: [ip-sysctl](https://docs.kernel.org/networking/ip-sysctl.html) (`tcp_syncookies`, `ip_local_port_range`, `tcp_max_syn_backlog`, `somaxconn`)

**3.2 DNS chuyên sâu**

- [RFC 2308](https://www.rfc-editor.org/rfc/rfc2308) (negative caching): mục 5
- [JEP 486: Permanently Disable the Security Manager](https://openjdk.org/jeps/486)
- Kubernetes: [DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/), mục [Pod's DNS Config](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/#pod-dns-config)

**3.3 HTTP request smuggling và desync**

- PortSwigger: [HTTP request smuggling](https://portswigger.net/web-security/request-smuggling) (làm các lab cơ bản)
- PortSwigger Research: [HTTP/1.1 must die](https://portswigger.net/research/http1-must-die) (2025, vì sao vấn đề chưa hết)
- RFC 9112: mục [6.3 Message Body Length](https://www.rfc-editor.org/rfc/rfc9112#section-6.3)

**3.4 Realtime: SSE, WebSocket và scale**

- MDN: [Using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events), [WebSockets API](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
- Nginx: [WebSocket proxying](https://nginx.org/en/docs/http/websocket.html)
- [RFC 6455](https://www.rfc-editor.org/rfc/rfc6455) (WebSocket): mục 1.3 (opening handshake), 5.5.2 (ping/pong)
- Messaging và pub/sub: [12-messaging.md](12-messaging.md)

**3.5 Mạng cloud, container, anycast**

- AWS: [What is Amazon VPC?](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html), [Infrastructure security](https://docs.aws.amazon.com/vpc/latest/userguide/infrastructure-security.html) (so sánh security group và NACL)
- Kubernetes: [Service](https://kubernetes.io/docs/concepts/services-networking/service/), [DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/#services)
- Cloudflare: [The Road to QUIC](https://blog.cloudflare.com/the-road-to-quic/) (có phần về anycast và vì sao QUIC hợp với edge)

</details>

<details>
<summary><strong>21. Cấu trúc dữ liệu và thuật toán</strong> (17 module, 75 link)</summary>

Học chi tiết: [21-dsa.md](21-dsa.md)

**1.1 Big-O và ràng buộc đầu vào**

- Algorithms 4th: [1.4 Analysis of Algorithms](https://algs4.cs.princeton.edu/14analysis/)
- [Big-O Cheat Sheet](https://www.bigocheatsheet.com/): bảng độ phức tạp của cấu trúc và sort, in ra để dò
- CLRS ch.3 (Characterizing Running Times) và ch.16 (Amortized Analysis) nếu cần chặt chẽ

**1.2 Array, string, hash map/set**

- Tech Interview Handbook: [Array](https://www.techinterviewhandbook.org/algorithms/array/), [Hash table](https://www.techinterviewhandbook.org/algorithms/hash-table/), [String](https://www.techinterviewhandbook.org/algorithms/string/)
- Algorithms 4th: [3.4 Hash Tables](https://algs4.cs.princeton.edu/34hash/) (separate chaining, linear probing)
- VisuAlgo: [Hash Table](https://visualgo.net/en/hashtable)

**1.3 Stack, queue, deque, linked list**

- Algorithms 4th: [1.3 Bags, Queues, and Stacks](https://algs4.cs.princeton.edu/13stacks/)
- Tech Interview Handbook: [Linked list](https://www.techinterviewhandbook.org/algorithms/linked-list/)
- VisuAlgo: [Linked List, Stack, Queue, Deque](https://visualgo.net/en/list)
- PHP: [SplStack](https://www.php.net/manual/en/class.splstack.php), [SplQueue](https://www.php.net/manual/en/class.splqueue.php), [array_shift](https://www.php.net/manual/en/function.array-shift.php)

**1.4 Sort và binary search**

- Algorithms 4th: [ch.2 Sorting](https://algs4.cs.princeton.edu/20sorting/) (2.1 elementary, 2.2 mergesort, 2.3 quicksort)
- VisuAlgo: [Sorting](https://visualgo.net/en/sorting)
- Tech Interview Handbook: [Sorting and searching](https://www.techinterviewhandbook.org/algorithms/sorting-searching/)
- PHP: [RFC Make sorting stable](https://wiki.php.net/rfc/stable_sorting) (PHP 8.0), [usort](https://www.php.net/manual/en/function.usort.php)
- Go: [package slices](https://pkg.go.dev/slices) (mục `Sort`, `SortStableFunc`)
- Code trong repo: `dsa/go/searching/`, `dsa/java/BinarySearch.java` (có `lowerBound`)

**1.5 Quy trình làm bài và edge case**

- Tech Interview Handbook: [Coding interview techniques](https://www.techinterviewhandbook.org/coding-interview-techniques/) và [Coding interview cheatsheet](https://www.techinterviewhandbook.org/coding-interview-cheatsheet/)
- PHP: [Integers](https://www.php.net/manual/en/language.types.integer.php) (mục integer overflow), [mb_strlen](https://www.php.net/manual/en/function.mb-strlen.php)

**2.1 Two pointers, sliding window, prefix sum**

- Tech Interview Handbook: [Array](https://www.techinterviewhandbook.org/algorithms/array/) (mục techniques: sliding window, two pointers, prefix sum)
- NeetCode Roadmap: nhánh *Two Pointers*, *Sliding Window*

**2.2 Monotonic stack và deque**

- Tech Interview Handbook: [Queue](https://www.techinterviewhandbook.org/algorithms/queue/) và [Stack](https://www.techinterviewhandbook.org/algorithms/stack/)
- NeetCode Roadmap: nhánh *Stack*

**2.3 Tree: DFS, BFS, BST, trie**

- Algorithms 4th: [3.2 Binary Search Trees](https://algs4.cs.princeton.edu/32bst/), [3.3 Balanced Search Trees](https://algs4.cs.princeton.edu/33balanced/) (2-3 tree và red-black), [5.2 Tries](https://algs4.cs.princeton.edu/52trie/)
- VisuAlgo: [BST / AVL](https://visualgo.net/en/bst)
- Tech Interview Handbook: [Tree](https://www.techinterviewhandbook.org/algorithms/tree/), [Trie](https://www.techinterviewhandbook.org/algorithms/trie/)
- Linux: [EEVDF Scheduler](https://docs.kernel.org/scheduler/sched-eevdf.html) (đọc đoạn đầu để biết mốc 6.6)

**2.4 Heap, top-K, interval**

- Algorithms 4th: [2.4 Priority Queues](https://algs4.cs.princeton.edu/24pq/)
- VisuAlgo: [Binary Heap](https://visualgo.net/en/heap)
- Tech Interview Handbook: [Heap](https://www.techinterviewhandbook.org/algorithms/heap/), [Interval](https://www.techinterviewhandbook.org/algorithms/interval/)
- PHP: [SplPriorityQueue](https://www.php.net/manual/en/class.splpriorityqueue.php), [SplMinHeap](https://www.php.net/manual/en/class.splminheap.php)

**2.5 Graph: BFS/DFS, topological sort, union-find, shortest path**

- Algorithms 4th: [4.1 Undirected Graphs](https://algs4.cs.princeton.edu/40graphs/), [4.2 Directed Graphs](https://algs4.cs.princeton.edu/42digraph/) (topological sort), [1.5 Union-Find](https://algs4.cs.princeton.edu/15uf/), [4.4 Shortest Paths](https://algs4.cs.princeton.edu/44sp/)
- cp-algorithms: [Disjoint Set Union](https://cp-algorithms.com/data_structures/disjoint_set_union.html), [Dijkstra](https://cp-algorithms.com/graph/dijkstra.html), [Topological sort](https://cp-algorithms.com/graph/topological-sort.html)
- VisuAlgo: [DFS/BFS](https://visualgo.net/en/dfsbfs), [Union-Find](https://visualgo.net/en/ufds), [SSSP](https://visualgo.net/en/sssp)
- Tech Interview Handbook: [Graph](https://www.techinterviewhandbook.org/algorithms/graph/)

**2.6 Backtracking và greedy**

- Tech Interview Handbook: [Recursion](https://www.techinterviewhandbook.org/algorithms/recursion/)
- VisuAlgo: [Recursion Tree](https://visualgo.net/en/recursion)
- NeetCode Roadmap: nhánh *Backtracking*, *Greedy*

**2.7 Dynamic programming**

- Tech Interview Handbook: [Dynamic programming](https://www.techinterviewhandbook.org/algorithms/dynamic-programming/)
- [MIT 6.006 Spring 2020](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/): các lecture về dynamic programming (khung SRTBOT)
- NeetCode Roadmap: nhánh *1-D DP*, *2-D DP*
- CLRS ch.14 (Dynamic Programming): rod cutting và LCS

**2.8 Bit, matrix, thiết kế cấu trúc dữ liệu, cấu trúc có sẵn trong PHP**

- Tech Interview Handbook: [Binary](https://www.techinterviewhandbook.org/algorithms/binary/), [Matrix](https://www.techinterviewhandbook.org/algorithms/matrix/)
- PHP: [Arrays](https://www.php.net/manual/en/language.types.array.php) (mục key casts), [SPL Data Structures](https://www.php.net/manual/en/spl.datastructures.php), [SplFixedArray](https://www.php.net/manual/en/class.splfixedarray.php), [SplObjectStorage](https://www.php.net/manual/en/class.splobjectstorage.php), [Data Structures (ds)](https://www.php.net/manual/en/book.ds.php), [php-ds/ext-ds](https://github.com/php-ds/ext-ds)
- Nikita Popov: [PHP's new hashtable implementation](https://www.npopov.com/2014/12/22/PHPs-new-hashtable-implementation.html) (cấu trúc bên trong của array PHP 7+, packed array)

**3.1 Cấu trúc dữ liệu bên trong hệ thống thật**

- Redis: [Sorted sets](https://redis.io/docs/latest/develop/data-types/sorted-sets/)
- Go blog: [Faster Go maps with Swiss Tables](https://go.dev/blog/swisstable)
- Java: [HashMap](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/HashMap.html) (phần implementation notes về treeified bin)
- cp-algorithms: [Segment Tree](https://cp-algorithms.com/data_structures/segment_tree.html), [Fenwick Tree](https://cp-algorithms.com/data_structures/fenwick.html) (chỉ đọc nếu còn thời gian)
- DDIA (Kleppmann, số chương theo bản 1) ch.3 *Storage and Retrieval*: hash index, SSTable/LSM, B-tree

**3.2 Cấu trúc xác suất và consistent hashing**

- Redis: [HyperLogLog](https://redis.io/docs/latest/develop/data-types/probabilistic/hyperloglogs/), [Bloom filter](https://redis.io/docs/latest/develop/data-types/probabilistic/bloom-filter/), [Count-min sketch](https://redis.io/docs/latest/develop/data-types/probabilistic/count-min-sketch/), [Cluster specification](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/) (mục key distribution model)
- [Bloom filter calculator](https://hur.st/bloomfilter/): nhập n và tỉ lệ false positive để ra số bit và số hash
- DDIA ch.6 *Partitioning*: phần hash partitioning và vì sao không dùng `hash % N`

**3.3 Dữ liệu không vừa một máy**

- Algorithms 4th: [2.4 Priority Queues](https://algs4.cs.princeton.edu/24pq/) (multiway merge)
- DDIA ch.10 *Batch Processing*: sort-merge join, broadcast join, xử lý key lệch
- Xem thêm [14-distributed-systems.md](14-distributed-systems.md) và [16-system-design.md](16-system-design.md)

**3.4 Nối thuật toán với bài toán backend**

- Redis: [Sorted sets](https://redis.io/docs/latest/develop/data-types/sorted-sets/) (mục leaderboard, rate limiter)
- [11-cache.md](11-cache.md), [04-nosql-search-storage.md](04-nosql-search-storage.md), [16-system-design.md](16-system-design.md)

</details>

### Dữ liệu

<details>
<summary><strong>03. Database quan hệ và SQL</strong> (19 module, 100 link)</summary>

Học chi tiết: [03-database-sql.md](03-database-sql.md)

**1.1 SQL viết tay**

- [SQLBolt](https://sqlbolt.com/): bài tập tương tác, nếu cần ôn lại cú pháp
- [modern-sql.com](https://modern-sql.com/): cách SQL chuẩn hoạt động và mức hỗ trợ của từng DB
- MySQL: [SQL mode](https://dev.mysql.com/doc/refman/8.4/en/sql-mode.html) (`ONLY_FULL_GROUP_BY`, strict mode)

**1.2 Index cơ bản**

- Use The Index, Luke: [Anatomy of an Index](https://use-the-index-luke.com/sql/anatomy) và [Concatenated Keys](https://use-the-index-luke.com/sql/where-clause/the-equals-operator/concatenated-keys)
- MySQL: [Multiple-Column Indexes](https://dev.mysql.com/doc/refman/8.4/en/multiple-column-indexes.html)

**1.3 Transaction cơ bản**

- Laravel: [Database Transactions](https://laravel.com/docs/database#database-transactions)
- DDIA ch.7, phần đầu (ACID)

**1.4 Kiểu dữ liệu và schema cơ bản**

- MySQL: [Fixed-Point Types](https://dev.mysql.com/doc/refman/8.4/en/fixed-point-types.html), [DATETIME/TIMESTAMP](https://dev.mysql.com/doc/refman/8.4/en/datetime.html), [utf8mb4](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-utf8mb4.html)
- [PostgreSQL wiki: Don't Do This](https://wiki.postgresql.org/wiki/Don%27t_Do_This): danh sách anti-pattern ngắn, đa số áp dụng được cho cả MySQL

**2.1 InnoDB lưu dữ liệu thế nào**

- MySQL: [Clustered and Secondary Indexes](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html)
- Jeremy Cole: [B+Tree index structures in InnoDB](https://blog.jcole.us/2013/01/10/btree-index-structures-in-innodb/)
- [RFC 9562](https://www.rfc-editor.org/rfc/rfc9562) (UUID): đọc phần 5.7 (UUIDv7) và phần 6
- Postgres: [Heap-Only Tuples](https://www.postgresql.org/docs/current/storage-hot.html)

**2.2 Index nâng cao**

- MySQL: [Index Condition Pushdown](https://dev.mysql.com/doc/refman/8.4/en/index-condition-pushdown-optimization.html), [ORDER BY Optimization](https://dev.mysql.com/doc/refman/8.4/en/order-by-optimization.html), [Range Optimization](https://dev.mysql.com/doc/refman/8.4/en/range-optimization.html) (có mục skip scan), [CREATE INDEX](https://dev.mysql.com/doc/refman/8.4/en/create-index.html) (functional key parts, multi-valued index), [Invisible Indexes](https://dev.mysql.com/doc/refman/8.4/en/invisible-indexes.html)
- Postgres: [Index Types](https://www.postgresql.org/docs/current/indexes-types.html), [Partial Indexes](https://www.postgresql.org/docs/current/indexes-partial.html), [Index-Only Scans](https://www.postgresql.org/docs/current/indexes-index-only-scans.html)
- Use The Index, Luke: các chương *The Where Clause*, *Sorting and Grouping*, *Partial Results*

**2.3 Đọc EXPLAIN và xử lý query chậm**

- MySQL: [EXPLAIN Output Format](https://dev.mysql.com/doc/refman/8.4/en/explain-output.html), [EXPLAIN ANALYZE](https://dev.mysql.com/doc/refman/8.4/en/explain.html), [Optimizer Statistics / Histogram](https://dev.mysql.com/doc/refman/8.4/en/optimizer-statistics.html), [Hash Joins](https://dev.mysql.com/doc/refman/8.4/en/hash-joins.html), [Slow Query Log](https://dev.mysql.com/doc/refman/8.4/en/slow-query-log.html)
- [pt-query-digest](https://docs.percona.com/percona-toolkit/pt-query-digest.html): tổng hợp slow log
- Use The Index, Luke: [We need tool support for keyset pagination](https://use-the-index-luke.com/no-offset) và [Paging Through Results](https://use-the-index-luke.com/sql/partial-results/fetch-next-page)
- Đối chiếu Postgres: [Using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html), [pgMustard: đọc EXPLAIN](https://www.pgmustard.com/docs/explain), [explain.dalibo.com](https://explain.dalibo.com/) (vẽ plan thành hình)

**2.4 SQL nâng cao**

- MySQL: [Window Functions](https://dev.mysql.com/doc/refman/8.4/en/window-functions.html), [WITH (CTE)](https://dev.mysql.com/doc/refman/8.4/en/with.html), [INSERT ... ON DUPLICATE KEY UPDATE](https://dev.mysql.com/doc/refman/8.4/en/insert-on-duplicate.html)
- [modern-sql.com](https://modern-sql.com/): các bài về `OVER`, `WITH RECURSIVE`

**2.5 Isolation level và anomaly**

- MySQL: [Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html), [Consistent Nonlocking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html)
- Postgres: [Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
- [Hermitage](https://github.com/ept/hermitage): bảng thực nghiệm anomaly nào xảy ra ở DB nào, level nào, kèm script tái hiện
- 🔴 [A Critique of ANSI SQL Isolation Levels](https://www.microsoft.com/en-us/research/publication/a-critique-of-ansi-sql-isolation-levels/) (Berenson và cộng sự, 1995): bài gốc định nghĩa lại các anomaly
- 🔴 [Serializable Snapshot Isolation in PostgreSQL](https://arxiv.org/abs/1208.4179) (Ports, Grittner)
- 🔴 [Jepsen: Consistency Models](https://jepsen.io/consistency): bản đồ các mô hình consistency
- DDIA ch.7: *Weak Isolation Levels* và *Serializability*. Phần quan trọng nhất của cả file này

**2.6 Lock thực dụng**

- MySQL: [Locking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html) (có mục `NOWAIT`/`SKIP LOCKED`), [Deadlocks in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks.html) và [How to Minimize and Handle Deadlocks](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks-handling.html)
- [Brandur: Postgres Job Queues & Failure By MVCC](https://brandur.org/postgres-queues): vì sao job queue bằng DB có thể tự làm mình chậm dần
- Laravel: [Pessimistic Locking](https://laravel.com/docs/queries#pessimistic-locking)

**2.7 Tầng PHP: PDO và Laravel**

- PHP: [PDO](https://www.php.net/manual/en/book.pdo.php), [PDO_MYSQL](https://www.php.net/manual/en/ref.pdo-mysql.php) (ghi chú emulate prepare, buffered query), [PDO::setAttribute](https://www.php.net/manual/en/pdo.setattribute.php), [Persistent Connections](https://www.php.net/manual/en/features.persistent-connections.php), [Buffered and Unbuffered queries](https://www.php.net/manual/en/mysqlinfo.concepts.buffering.php)
- [Read & Write Connections / sticky](https://laravel.com/docs/database#read-and-write-connections)
- [Handling Deadlocks](https://laravel.com/docs/database#handling-deadlocks)
- [Implicit Commits](https://laravel.com/docs/database#implicit-commits-in-transactions)
- [Monitoring Cumulative Query Time](https://laravel.com/docs/database#monitoring-cumulative-query-time)
- [Chunking](https://laravel.com/docs/queries#chunking-results)
- [Eager Loading](https://laravel.com/docs/eloquent-relationships#eager-loading)
- [Preventing Lazy Loading](https://laravel.com/docs/eloquent-relationships#preventing-lazy-loading)
- [Automatic Eager Loading](https://laravel.com/docs/eloquent-relationships#automatic-eager-loading)
- [Eloquent Strictness](https://laravel.com/docs/eloquent#configuring-eloquent-strictness)
- [Jobs & Database Transactions](https://laravel.com/docs/queues#jobs-and-database-transactions)
- Laravel:
- Chi tiết về runtime PHP-FPM: [05-php-laravel.md](05-php-laravel.md)

**2.8 Thiết kế schema nâng cao**

- MySQL: [JSON Data Type](https://dev.mysql.com/doc/refman/8.4/en/json.html)
- Laravel: [Polymorphic Relationships](https://laravel.com/docs/eloquent-relationships#polymorphic-relationships)
- *High Performance MySQL*: chương *Schema Design and Management*
- *SQL Antipatterns* (Bill Karwin): EAV, polymorphic association, naive tree. Đọc các chương về những chủ đề này

**3.1 Bên trong InnoDB: log, bộ nhớ, MVCC**

- [InnoDB Architecture](https://dev.mysql.com/doc/refman/8.4/en/innodb-architecture.html) (xem hình trước)
- [Buffer Pool](https://dev.mysql.com/doc/refman/8.4/en/innodb-buffer-pool.html)
- [Redo Log](https://dev.mysql.com/doc/refman/8.4/en/innodb-redo-log.html)
- [Undo Logs](https://dev.mysql.com/doc/refman/8.4/en/innodb-undo-logs.html)
- [Multi-Versioning](https://dev.mysql.com/doc/refman/8.4/en/innodb-multi-versioning.html)
- [Doublewrite Buffer](https://dev.mysql.com/doc/refman/8.4/en/innodb-doublewrite-buffer.html)
- [Binary Log](https://dev.mysql.com/doc/refman/8.4/en/binary-log.html)
- [Replication Formats](https://dev.mysql.com/doc/refman/8.4/en/replication-formats.html)
- Postgres: [WAL](https://www.postgresql.org/docs/current/wal-intro.html), [MVCC](https://www.postgresql.org/docs/current/mvcc-intro.html), [Routine Vacuuming](https://www.postgresql.org/docs/current/routine-vacuuming.html) (có mục wraparound)
- MySQL:
- DDIA ch.3 (B-tree so với LSM)
- CMU 15-445: các bài về logging & recovery và multi-version concurrency control

**3.2 Lock chuyên sâu**

- [InnoDB Locking](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html)
- [Locks Set by Different SQL Statements](https://dev.mysql.com/doc/refman/8.4/en/innodb-locks-set.html)
- [AUTO_INCREMENT Handling](https://dev.mysql.com/doc/refman/8.4/en/innodb-auto-increment-handling.html)
- [Metadata Locking](https://dev.mysql.com/doc/refman/8.4/en/metadata-locking.html)
- Postgres: [Explicit Locking](https://www.postgresql.org/docs/current/explicit-locking.html) (bảng xung đột giữa các table lock, và vì sao `ALTER TABLE` chặn cả `SELECT`)
- MySQL:

**3.3 Thay đổi schema online và migration không downtime**

- MySQL: [Online DDL Operations](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html): **bảng tra cứu quan trọng nhất** của module này
- [gh-ost](https://github.com/github/gh-ost): README và thư mục `doc/` (đặc biệt phần so sánh với cách dùng trigger)
- [pt-online-schema-change](https://docs.percona.com/percona-toolkit/pt-online-schema-change.html)
- Martin Fowler: [Parallel Change](https://martinfowler.com/bliki/ParallelChange.html)
- Laravel: [Migrations](https://laravel.com/docs/migrations)

**3.4 Replication và failover**

- MySQL: [Replication](https://dev.mysql.com/doc/refman/8.4/en/replication.html), [Semisynchronous Replication](https://dev.mysql.com/doc/refman/8.4/en/replication-semisync.html)
- DDIA ch.5
- Phần hệ phân tán: [14-distributed-systems.md](14-distributed-systems.md)

**3.5 Backup, PITR, RPO/RTO**

- MySQL: [Point-in-Time Recovery](https://dev.mysql.com/doc/refman/8.4/en/point-in-time-recovery.html)
- [18-reliability-observability.md](18-reliability-observability.md) (RPO/RTO, DR)

**3.6 Scale: partitioning, sharding, archiving**

- MySQL: [Partitioning](https://dev.mysql.com/doc/refman/8.4/en/partitioning.html), [Restrictions and Limitations](https://dev.mysql.com/doc/refman/8.4/en/partitioning-limitations.html)
- [Vitess docs](https://vitess.io/docs/): phần *Concepts* (keyspace, vindex, resharding)
- [Notion: Sharding Postgres](https://www.notion.com/blog/sharding-postgres-at-notion) (chọn shard key, shard logic, migration)
- [Figma: How Figma's databases team lived to tell the scale](https://www.figma.com/blog/how-figmas-databases-team-lived-to-tell-the-scale/) (tách theo chiều dọc rồi mới shard ngang)
- [Shopify Ghostferry](https://github.com/shopify/ghostferry) (di chuyển dữ liệu giữa các shard MySQL online)
- DDIA ch.6
- Case study:

**3.7 MySQL so với Postgres**

- [Uber: Why Uber Engineering Switched from Postgres to MySQL](https://www.uber.com/us/en/blog/postgres-to-mysql-migration/) (2016). Đọc kèm phản biện từ cộng đồng Postgres để thấy cả hai phía; một số điểm đã cũ
- [PgBouncer features](https://www.pgbouncer.org/features.html) (bảng tính năng theo từng pooling mode)
- Postgres [release notes 18](https://www.postgresql.org/docs/current/release-18.html): lướt để biết cái mới (async I/O, `uuidv7()`, skip scan)

</details>

<details>
<summary><strong>04. NoSQL, search và storage</strong> (20 module, 93 link)</summary>

Học chi tiết: [04-nosql-search-storage.md](04-nosql-search-storage.md)

**1.1 Redis: kiểu dữ liệu và use case**

- Redis: [Data types](https://redis.io/docs/latest/develop/data-types/) (đọc phần giới thiệu từng kiểu), [Sorted sets](https://redis.io/docs/latest/develop/data-types/sorted-sets/), [HyperLogLog](https://redis.io/docs/latest/develop/data-types/probabilistic/hyperloglogs/)
- Redis: [What's new in 8.0](https://redis.io/docs/latest/develop/whats-new/8-0/): lướt để biết các kiểu dữ liệu mới được gộp vào

**1.2 Bức tranh NoSQL**

- MongoDB: [Data Modeling](https://www.mongodb.com/docs/manual/data-modeling/) (phần mở đầu, để thấy tư duy aggregate)
- DDIA ch.2 (*Data Models and Query Languages*): relational, document, graph

**1.3 Search cơ bản**

- Elastic: [Text analysis](https://www.elastic.co/docs/manage-data/data-store/text-analysis) (phần khái niệm: anatomy of an analyzer), [Mapping](https://www.elastic.co/docs/manage-data/data-store/mapping)
- Postgres: [Full Text Search](https://www.postgresql.org/docs/current/textsearch.html) (chương 12.1 Introduction), [pg_trgm](https://www.postgresql.org/docs/current/pgtrgm.html)

**1.4 Object storage cơ bản**

- S3: [Uploading objects with presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedUrlUploadObject.html)
- Laravel: [Temporary URLs](https://laravel.com/docs/filesystem#temporary-urls) và [Temporary Upload URLs](https://laravel.com/docs/filesystem#temporary-upload-urls)

**2.1 Redis: mô hình thực thi và lệnh nguy hiểm**

- Redis: [Diagnosing latency issues](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/) (phần single-threaded nature, slow commands, fork), [SCAN](https://redis.io/docs/latest/commands/scan/) (mục guarantees), [ACL](https://redis.io/docs/latest/operate/oss_and_stack/management/security/acl/)

**2.2 Redis: persistence, TTL, eviction**

- Redis: [Persistence](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/) (đọc hết, phần RDB vs AOF), [EXPIRE](https://redis.io/docs/latest/commands/expire/) (mục *How Redis expires keys*), [Key eviction](https://redis.io/docs/latest/develop/reference/eviction/), [HEXPIRE](https://redis.io/docs/latest/commands/hexpire/)

**2.3 Redis: pipeline, transaction, Lua, messaging**

- Redis: [Pipelining](https://redis.io/docs/latest/develop/using-commands/pipelining/), [Transactions](https://redis.io/docs/latest/develop/using-commands/transactions/) (mục *Errors inside a transaction* và *Optimistic locking using check-and-set*), [Scripting with Lua](https://redis.io/docs/latest/develop/programmability/eval-intro/), [Pub/Sub](https://redis.io/docs/latest/develop/pubsub/), [Streams](https://redis.io/docs/latest/develop/data-types/streams/) (phần consumer group)

**2.4 Redis: use case kinh điển**

- Redis: [Distributed Locks with Redis](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/), [SET](https://redis.io/docs/latest/commands/set/) (các option `NX`, `PX`, `KEEPTTL`, `GET`)
- Martin Kleppmann: [How to do distributed locking](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html) (bắt buộc đọc trước khi trả lời câu về Redlock)

**2.5 MongoDB**

- MongoDB: [Data Model Design](https://www.mongodb.com/docs/manual/core/data-model-design/), [ESR Guideline](https://www.mongodb.com/docs/manual/tutorial/equality-sort-range-guideline/), [Aggregation](https://www.mongodb.com/docs/manual/aggregation/), [Transactions](https://www.mongodb.com/docs/manual/core/transactions/) (mục production considerations), [Write Concern](https://www.mongodb.com/docs/manual/reference/write-concern/), [Read Concern](https://www.mongodb.com/docs/manual/reference/read-concern/), [Read Preference](https://www.mongodb.com/docs/manual/core/read-preference/), [Change Streams](https://www.mongodb.com/docs/manual/changestreams/) (mục resume a change stream)

**2.6 Elasticsearch/OpenSearch: analyzer, mapping, tiếng Việt, relevance**

- Elastic: [Text analysis](https://www.elastic.co/docs/manage-data/data-store/text-analysis) (phần test analyzer, index/search analyzer), [ASCII folding token filter](https://www.elastic.co/docs/reference/text-analysis/analysis-asciifolding-tokenfilter), [Multi-fields](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/multi-fields), [Near real-time search](https://www.elastic.co/docs/manage-data/data-store/near-real-time-search), [Similarity settings](https://www.elastic.co/docs/reference/elasticsearch/index-settings/similarity) (BM25), [Paginate search results](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/paginate-search-results)

**2.7 Đồng bộ dữ liệu từ DB sang search**

- DynamoDB: [Change data capture for DynamoDB Streams](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html) (đối chiếu cách một DB managed cung cấp CDC)
- Laravel: [Scout: Indexing](https://laravel.com/docs/scout#indexing) và [Queueing](https://laravel.com/docs/scout#queueing)
- DDIA ch.11, mục *Change Data Capture* và *Keeping Systems in Sync* (bản 1)

**2.8 Object storage nâng cao**

- S3: [Multipart upload](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html), [Conditional requests](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-requests.html) và [Conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html), [S3 consistency](https://aws.amazon.com/s3/consistency/), [Lifecycle](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html), [Versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html), [Block Public Access](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html), [Optimizing performance](https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html)

**2.9 Tầng PHP: Redis client, Laravel Redis, Scout, Elasticsearch client, S3**

- Laravel: [Redis](https://laravel.com/docs/redis) (mục [phpredis](https://laravel.com/docs/redis#phpredis), [Predis](https://laravel.com/docs/redis#predis), [clusters](https://laravel.com/docs/redis#clusters), [pipelining](https://laravel.com/docs/redis#pipelining-commands)), [Scout](https://laravel.com/docs/scout), [Filesystem: S3](https://laravel.com/docs/filesystem#s3-driver-configuration) và [Automatic streaming](https://laravel.com/docs/filesystem#automatic-streaming)
- [phpredis](https://github.com/phpredis/phpredis) (README: persistent connection, serializer), [Predis](https://github.com/predis/predis)
- Elastic: [PHP client](https://www.elastic.co/docs/reference/elasticsearch/clients/php); driver cộng đồng [elastic-scout-driver](https://github.com/babenkoivan/elastic-scout-driver)
- Runtime PHP-FPM: [05-php-laravel.md](05-php-laravel.md)

**3.1 Bên trong Redis: encoding**

- Redis: [Memory optimization](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/memory-optimization/) (phần special encoding of small aggregate data types)
- Skip list và độ phức tạp: [21-dsa.md](21-dsa.md)

**3.2 Redis HA: replication, Sentinel, Cluster, license**

- Redis: [Replication](https://redis.io/docs/latest/operate/oss_and_stack/management/replication/), [Sentinel](https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/), [Scale with Redis Cluster](https://redis.io/docs/latest/operate/oss_and_stack/management/scaling/), [Cluster specification](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/) (mục key distribution, hash tags, redirection)
- License: [Redis licenses](https://redis.io/legal/licenses/), [Redis is now available under AGPLv3](https://redis.io/blog/agplv3/), [antirez: Redis is open source again](https://antirez.com/news/151), [Linux Foundation launches Valkey](https://www.linuxfoundation.org/press/linux-foundation-launches-open-source-valkey-community)

**3.3 MongoDB sharding và CAP**

- MongoDB: [Sharding](https://www.mongodb.com/docs/manual/sharding/), [Choose a Shard Key](https://www.mongodb.com/docs/manual/core/sharding-choose-a-shard-key/)
- DDIA ch.6 (partitioning) và ch.9 (phần về CAP)

**3.4 Wide-column (Cassandra) và DynamoDB**

- Cassandra: [Data Modeling](https://cassandra.apache.org/doc/latest/cassandra/developing/data-modeling/index.html) (đọc hết loạt bài, có ví dụ từ query tới bảng)
- DynamoDB: [NoSQL design](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html), [Partition key design](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html), [GSI](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html), [Read consistency](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html), [Throughput capacity](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/capacity-mode.html) (so sánh [on-demand](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/on-demand-capacity-mode.html) và [provisioned](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/provisioned-capacity-mode.html))
- *The DynamoDB Book*: các chương về single-table design và strategy cho one-to-many
- DDIA ch.3 (LSM) và ch.5 (leaderless replication, quorum)

**3.5 Vận hành search: shard, reindex, license**

- Elastic: [Aliases](https://www.elastic.co/docs/manage-data/data-store/aliases), [Reindex examples](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reindex-indices), [Size your shards](https://www.elastic.co/docs/deploy-manage/production-guidance/optimize-performance/size-shards)
- [Elastic: Elasticsearch is open source again](https://www.elastic.co/blog/elasticsearch-is-open-source-again) (2024)

**3.6 Time-series, OLAP, data warehouse**

- Prometheus: [Metric and label naming](https://prometheus.io/docs/practices/naming/) (mục labels, cảnh báo cardinality)
- ClickHouse: [Asynchronous inserts](https://clickhouse.com/docs/optimize/asynchronous-inserts)
- Kimball: [Star schema](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/star-schema-olap-cube/)
- DDIA ch.3, mục *Transaction Processing or Analytics?* và *Column-Oriented Storage*

**3.7 Vector DB và graph DB**

- [pgvector README](https://github.com/pgvector/pgvector) (mục HNSW, IVFFlat, filtering)
- [HNSW paper](https://arxiv.org/abs/1603.09320) (Malkov, Yashunin): đọc phần giới thiệu và hình minh hoạ
- [Neo4j: Getting started](https://neo4j.com/docs/getting-started/) (phần graph database concepts)

</details>

<details>
<summary><strong>11. Cache</strong> (13 module, 38 link)</summary>

Học chi tiết: [11-cache.md](11-cache.md)

**1.1 Các tầng cache**

- MDN: [HTTP caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching) (đọc hết), [Cache-Control](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control)
- [RFC 5861](https://www.rfc-editor.org/rfc/rfc5861): `stale-while-revalidate` và `stale-if-error`, nguồn gốc của pattern SWR ở module 2.3
- Laravel: [Cache-Control middleware](https://laravel.com/docs/responses#cache-control-middleware) (`cache.headers`)

**1.2 Cache-aside và TTL**

- AWS: [Caching best practices](https://aws.amazon.com/caching/best-practices/) (mục lazy caching, write-through, TTL)
- Laravel: [Retrieve & Store](https://laravel.com/docs/cache#retrieve-store)

**1.3 Eviction cơ bản**

- Redis: [Key eviction](https://redis.io/docs/latest/develop/reference/eviction/) (mục approximated LRU và LFU)
- Caffeine: [Efficiency](https://github.com/ben-manes/caffeine/wiki/Efficiency) (biểu đồ hit ratio của các policy trên trace thật)

**2.1 Pattern đọc/ghi**

- AWS whitepaper: [Database Caching Strategies Using Redis](https://docs.aws.amazon.com/whitepapers/latest/database-caching-strategies-using-redis/welcome.html) (phần caching patterns)

**2.2 Invalidation và race condition**

- Laravel: [Jobs & Database Transactions](https://laravel.com/docs/queues#jobs-and-database-transactions) (cùng vấn đề "chạy trước khi commit")
- Scaling Memcache at Facebook: mục 3.2.1 (leases) và 4.1 (invalidation qua commit log)
- DDIA ch.5, mục *Problems with Replication Lag*

**2.3 Stampede, penetration, avalanche**

- Vattani, Chierichetti, Lowenstein: [Optimal Probabilistic Cache Stampede Prevention](https://cseweb.ucsd.edu/~avattani/papers/cache_stampede.pdf) (VLDB 2015): paper gốc của XFetch, đọc mục 1–3
- Go: [singleflight](https://pkg.go.dev/golang.org/x/sync/singleflight)
- Scaling Memcache at Facebook: mục 3.2.1, phần lease dùng để chống thundering herd

**2.4 Hot key, big key và Redis làm cache**

- Redis: [Key eviction](https://redis.io/docs/latest/develop/reference/eviction/) (mục chọn policy), [HEXPIRE](https://redis.io/docs/latest/commands/hexpire/), [Diagnosing latency](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/)
- Valkey: [Introducing Hash Field Expirations](https://valkey.io/blog/hash-fields-expiration/)
- License: [Redis licenses](https://redis.io/legal/licenses/)

**2.5 Vận hành cache**

- Redis: [Pipelining](https://redis.io/docs/latest/develop/using-commands/pipelining/)
- AWS: [Caching best practices](https://aws.amazon.com/caching/best-practices/) (mục evictions, the thundering herd, cache (almost) everything)
- Hiệu năng nói chung, đo trước khi cache: [17-performance.md](17-performance.md)

**2.6 Cài LRU O(1)**

- LeetCode 146 *LRU Cache* (luyện viết không cần IDE)
- Thuật toán và cấu trúc dữ liệu liên quan: [21-dsa.md](21-dsa.md)

**2.7 Cache trong PHP/Laravel**

- Laravel: [Cache](https://laravel.com/docs/cache) (các mục [Stale While Revalidate](https://laravel.com/docs/cache#swr), [Cache Memoization](https://laravel.com/docs/cache#cache-memoization), [Cache Tags](https://laravel.com/docs/cache#cache-tags), [Atomic Locks](https://laravel.com/docs/cache#atomic-locks), [Managing Locks Across Processes](https://laravel.com/docs/cache#managing-locks-across-processes), [Cache Failover](https://laravel.com/docs/cache#cache-failover)), helper [`once()`](https://laravel.com/docs/helpers#method-once)
- PHP: [APCu](https://www.php.net/manual/en/book.apcu.php), [OPcache](https://www.php.net/manual/en/book.opcache.php)
- [phpredis](https://github.com/phpredis/phpredis) (mục serializer, compression, persistent connection), [Predis](https://github.com/predis/predis)
- Spring: [Cache Abstraction](https://docs.spring.io/spring-framework/reference/integration/cache.html) (đối chiếu)
- Runtime PHP-FPM và Octane: [05-php-laravel.md](05-php-laravel.md)

**3.1 Multi-level cache (L1 + L2)**

- Redis: [Client-side caching reference](https://redis.io/docs/latest/develop/reference/client-side-caching/) (mục tracking, broadcasting mode, và phần race giữa đọc và invalidation)
- Redis: [Pub/Sub](https://redis.io/docs/latest/develop/pubsub/) (mục delivery semantics)

**3.2 Nhất quán cache ở quy mô lớn: lease, CDC**

- [Scaling Memcache at Facebook](https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala): đọc mục 3.2.1 (leases), 4 (in a region), 5 (across regions)
- Meta Engineering: [Cache made consistent](https://engineering.fb.com/2022/06/08/core-infra/cache-made-consistent/) (2022)
- DDIA ch.11, mục *Change Data Capture*

**3.3 Khi cache trở thành phụ thuộc bắt buộc**

- Redis: [Sentinel](https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/), [Replication](https://redis.io/docs/latest/operate/oss_and_stack/management/replication/)
- Scaling Memcache at Facebook: mục 3.3 (gutter pool: nhóm máy dự phòng nhận tải khi máy cache chết)

</details>

<details>
<summary><strong>22. Dữ liệu thực tế: những thứ "đời thường" hay gây bug production</strong> (15 module, 66 link)</summary>

Học chi tiết: [22-practical-data.md](22-practical-data.md)

**1.1 Thời gian cơ bản**

- [RFC 3339](https://www.rfc-editor.org/rfc/rfc3339) (mục 5.6 Internet Date/Time Format)
- Jon Skeet: [Storing UTC is not a silver bullet](https://codeblog.jonskeet.uk/2019/03/27/storing-utc-is-not-a-silver-bullet/): khi nào lưu UTC là sai (sự kiện tương lai theo giờ địa phương)
- [Falsehoods programmers believe about time](https://infiniteundo.com/post/25326999628/falsehoods-programmers-believe-about-time): danh sách ngắn, đọc để biết mình đang giả định gì

**1.2 Tiền cơ bản**

- MySQL: [Fixed-Point Types](https://dev.mysql.com/doc/refman/8.4/en/fixed-point-types.html)
- Martin Fowler: [Money](https://martinfowler.com/eaaCatalog/money.html) (pattern `Money(amount, currency)`)

**1.3 Chuỗi và UTF-8 cơ bản**

- MySQL: [The utf8mb4 Character Set](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-utf8mb4.html), [Unicode Character Sets](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-sets.html)
- Laravel: [`Str::slug`](https://laravel.com/docs/strings#method-str-slug)

**1.4 Thông báo qua queue**

- Laravel: [Queueing Mail](https://laravel.com/docs/mail#queueing-mail), [Queued Mailables and Database Transactions](https://laravel.com/docs/mail#queued-mailables-and-database-transactions), [Mail and Local Development](https://laravel.com/docs/mail#mail-and-local-development)

**2.1 Timezone, DST, kiểu cột, cron, báo cáo**

- MySQL: [DATETIME, DATE, TIMESTAMP](https://dev.mysql.com/doc/refman/8.4/en/datetime.html), [Time Zone Support](https://dev.mysql.com/doc/refman/8.4/en/time-zone-support.html) (mục nạp bảng timezone, `time_zone` per session), [Date and Time Functions](https://dev.mysql.com/doc/refman/8.4/en/date-and-time-functions.html) (`CONVERT_TZ`)
- Postgres: [Date/Time Types](https://www.postgresql.org/docs/current/datatype-datetime.html) (mục 8.5.1.3 và 8.5.3 time zones)
- [IANA Time Zone Database](https://www.iana.org/time-zones)
- Laravel: [Scheduling: Timezones](https://laravel.com/docs/scheduling#timezones)

**2.2 Tiền: làm tròn, đa tiền tệ, chia tiền**

- [moneyphp/money](https://github.com/moneyphp/money) (README, mục allocation): đọc để thấy thư viện giải bài chia tiền thế nào, kể cả khi không dùng
- Martin Fowler: [Money](https://martinfowler.com/eaaCatalog/money.html) (phần allocate)

**2.3 Unicode và tiếng Việt**

- [UAX #15: Unicode Normalization Forms](https://unicode.org/reports/tr15/) (mục 1, hình ví dụ canonical equivalence)
- [UAX #29: Text Segmentation](https://unicode.org/reports/tr29/) (mục grapheme cluster boundaries)
- MySQL: [Unicode Character Sets](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-sets.html) (mục collation `_0900_`, pad attribute)
- Postgres: [unaccent](https://www.postgresql.org/docs/current/unaccent.html)

**2.4 Số và ID**

- [RFC 9562](https://www.rfc-editor.org/rfc/rfc9562) (UUID): mục 5.7 UUIDv7 và mục 6 best practices
- MySQL: [Integer Types](https://dev.mysql.com/doc/refman/8.4/en/integer-types.html)
- PHP: [ramsey/uuid](https://github.com/ramsey/uuid) (UUIDv7); Laravel có `HasUuids`/`HasUlids` cho model

**2.5 File: upload, import, export**

- OWASP: [CSV Injection](https://owasp.org/www-community/attacks/CSV_Injection) (đọc hết, ngắn), [File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [tus.io](https://tus.io/) (giao thức resumable upload)

**2.6 Email, SMS, OTP**

- [DMARC overview](https://dmarc.org/overview/)
- Google: [Email sender guidelines](https://support.google.com/a/answer/81126)
- OTP và xác thực: [10-security.md](10-security.md)

**2.7 Tầng PHP: thời gian, tiền, chuỗi, file lớn**

- [DateTimeImmutable](https://www.php.net/manual/en/class.datetimeimmutable.php), [Date/Time configuration](https://www.php.net/manual/en/datetime.configuration.php) (`date.timezone`), [hrtime](https://www.php.net/manual/en/function.hrtime.php)
- [BCMath](https://www.php.net/manual/en/book.bc.php), [BcMath\Number](https://www.php.net/manual/en/class.bcmath-number.php), [round](https://www.php.net/manual/en/function.round.php), [RoundingMode](https://www.php.net/manual/en/enum.roundingmode.php)
- [mbstring](https://www.php.net/manual/en/book.mbstring.php), [Normalizer](https://www.php.net/manual/en/class.normalizer.php), [Transliterator](https://www.php.net/manual/en/class.transliterator.php), [Grapheme functions](https://www.php.net/manual/en/ref.intl.grapheme.php), [NumberFormatter](https://www.php.net/manual/en/class.numberformatter.php)
- [SplFileObject](https://www.php.net/manual/en/class.splfileobject.php), [fgetcsv](https://www.php.net/manual/en/function.fgetcsv.php), [Generators](https://www.php.net/manual/en/language.generators.overview.php), [Fileinfo](https://www.php.net/manual/en/book.fileinfo.php)
- [Carbon](https://carbon.nesbot.com/)
- Laravel: [Date Casting and Timezones](https://laravel.com/docs/eloquent-mutators#date-casting-and-timezones), [Date Serialization](https://laravel.com/docs/eloquent-serialization#date-serialization), [Streamed Downloads](https://laravel.com/docs/responses#streamed-downloads), [`Number::currency`](https://laravel.com/docs/helpers#method-number-currency), [`Str::ascii`](https://laravel.com/docs/strings#method-str-ascii)
- PhpSpreadsheet: [Memory saving](https://phpspreadsheet.readthedocs.io/en/latest/topics/memory_saving/); [OpenSpout](https://github.com/openspout/openspout); Laravel Excel: [Chunk reading](https://docs.laravel-excel.com/3.1/imports/chunk-reading.html), [Queued exports](https://docs.laravel-excel.com/3.1/exports/queued.html)
- PHP:

**3.1 Ledger và bút toán kép**

- Modern Treasury: [Accounting for Developers, Part I](https://www.moderntreasury.com/journal/accounting-for-developers-part-i) (và các phần tiếp theo)
- Lock và lost update: [03-database-sql.md](03-database-sql.md) module 2.5–2.6

**3.2 Thanh toán qua cổng**

- Stripe: [Webhooks](https://docs.stripe.com/webhooks) (mục verify signature, retry, xử lý trùng), [Idempotent requests](https://docs.stripe.com/api/idempotent_requests)
- Brandur: [Implementing Stripe-like Idempotency Keys in Postgres](https://brandur.org/idempotency-keys): thiết kế idempotency key ở phía mình, áp dụng được cho MySQL
- Tài liệu tích hợp của cổng bạn đang dùng (VNPay, Momo): đọc mục IPN và API truy vấn giao dịch

**3.3 State machine và audit trail**

- Laravel: [Enum Casting](https://laravel.com/docs/eloquent-mutators#enum-casting)
- Thiết kế pattern State: [08-oop-design.md](08-oop-design.md)

**3.4 i18n, soft delete, vệ sinh dữ liệu, cô lập môi trường**

- Laravel: [Soft Deleting](https://laravel.com/docs/eloquent#soft-deleting), [Pluralization](https://laravel.com/docs/localization#pluralization), [Environment Configuration](https://laravel.com/docs/configuration#environment-configuration)
- PHP: [NumberFormatter](https://www.php.net/manual/en/class.numberformatter.php) (parse và format theo locale)

</details>

### Ngôn ngữ và thiết kế code

<details>
<summary><strong>05. PHP và Laravel</strong> (22 module, 197 link)</summary>

Học chi tiết: [05-php-laravel.md](05-php-laravel.md)

**1.1 Type system và so sánh**

- PHP: [Type declarations](https://www.php.net/manual/en/language.types.declarations.php) (mục [Strict typing](https://www.php.net/manual/en/language.types.declarations.php#language.types.declarations.strict)), [Type juggling](https://www.php.net/manual/en/language.types.type-juggling.php), [Comparison operators](https://www.php.net/manual/en/language.operators.comparison.php), [Type comparison tables](https://www.php.net/manual/en/types.comparisons.php), [`match`](https://www.php.net/manual/en/control-structures.match.php)
- RFC: [Saner string to number comparisons](https://wiki.php.net/rfc/string_to_number_comparison) (bảng so sánh PHP 7 và PHP 8), [Deprecate implicitly nullable parameter types](https://wiki.php.net/rfc/deprecate-implicitly-nullable-types)

**1.2 Array, reference và object handle**

- PHP: [Arrays](https://www.php.net/manual/en/language.types.array.php) (phần key casting), [References Explained](https://www.php.net/manual/en/language.references.php), [foreach](https://www.php.net/manual/en/control-structures.foreach.php) (cảnh báo về reference), [Objects and references](https://www.php.net/manual/en/language.oop5.references.php), [Object Cloning](https://www.php.net/manual/en/language.oop5.cloning.php)

**1.3 OOP trong PHP**

- PHP: [Interfaces](https://www.php.net/manual/en/language.oop5.interfaces.php), [Traits](https://www.php.net/manual/en/language.oop5.traits.php), [Late Static Bindings](https://www.php.net/manual/en/language.oop5.late-static-bindings.php), [Magic Methods](https://www.php.net/manual/en/language.oop5.magic.php), [Anonymous functions](https://www.php.net/manual/en/functions.anonymous.php), [Arrow Functions](https://www.php.net/manual/en/functions.arrow.php), [First class callable syntax](https://www.php.net/manual/en/functions.first_class_callable_syntax.php)
- Nguyên lý thiết kế chung (SOLID, composition): [08-oop-design.md](08-oop-design.md)

**1.4 Exception và xử lý lỗi**

- PHP: [Exceptions](https://www.php.net/manual/en/language.exceptions.php), [Errors in PHP 7](https://www.php.net/manual/en/language.errors.php7.php)
- Laravel: [Error Handling](https://laravel.com/docs/errors)

**1.5 Composer và PSR**

- Composer: [Basic usage](https://getcomposer.org/doc/01-basic-usage.md) (phần lock file), [Versions and constraints](https://getcomposer.org/doc/articles/versions.md), [Autoloader optimization](https://getcomposer.org/doc/articles/autoloader-optimization.md) (so sánh level 1, 2/A, 2/B)
- PHP-FIG: [danh sách PSR](https://www.php-fig.org/psr/), [PSR-4](https://www.php-fig.org/psr/psr-4/), [PER Coding Style](https://www.php-fig.org/per/coding-style/)

**1.6 Laravel cơ bản**

- Laravel: [Directory Structure](https://laravel.com/docs/structure), [Routing](https://laravel.com/docs/routing) (mục [Route Model Binding](https://laravel.com/docs/routing#route-model-binding)), [Middleware](https://laravel.com/docs/middleware), [Validation](https://laravel.com/docs/validation) (mục [Form Request](https://laravel.com/docs/validation#form-request-validation)), [Eloquent: Mass Assignment](https://laravel.com/docs/eloquent#mass-assignment), [Installation](https://laravel.com/docs/installation) (phần *Databases and Migrations*)

**2.1 PHP hiện đại: 8.0 tới 8.5**

- PHP release page: [8.4](https://www.php.net/releases/8.4/en.php), [8.5](https://www.php.net/releases/8.5/en.php) (có ví dụ trước/sau cho từng tính năng)
- PHP.Watch: [PHP 8.4](https://php.watch/versions/8.4), [PHP 8.5](https://php.watch/versions/8.5) (đọc cả mục *Deprecations* để biết cái sẽ vỡ khi nâng cấp)
- PHP manual: [Enumerations](https://www.php.net/manual/en/language.enumerations.php), [Property Hooks](https://www.php.net/manual/en/language.oop5.property-hooks.php), [Asymmetric visibility](https://www.php.net/manual/en/language.oop5.visibility.php#language.oop5.visibility-members-aviz), [Lazy Objects](https://www.php.net/manual/en/language.oop5.lazy-objects.php), [Attributes](https://www.php.net/manual/en/language.attributes.php), [Generators](https://www.php.net/manual/en/language.generators.php), [Fibers](https://www.php.net/manual/en/language.fibers.php), [URI](https://www.php.net/manual/en/book.uri.php)
- RFC (đọc phần *Proposal* và *Rejected features*): [Property hooks](https://wiki.php.net/rfc/property-hooks), [Asymmetric visibility v2](https://wiki.php.net/rfc/asymmetric-visibility-v2), [Lazy objects](https://wiki.php.net/rfc/lazy-objects), [array_find](https://wiki.php.net/rfc/array_find), [#\[\Deprecated\]](https://wiki.php.net/rfc/deprecated_attribute), [new without parentheses](https://wiki.php.net/rfc/new_without_parentheses), [bcrypt cost](https://wiki.php.net/rfc/bcrypt_cost_2023), [Pipe operator v3](https://wiki.php.net/rfc/pipe-operator-v3), [Clone with v2](https://wiki.php.net/rfc/clone_with_v2), [#\[\NoDiscard\]](https://wiki.php.net/rfc/marking_return_value_as_important), [array_first/array_last](https://wiki.php.net/rfc/array_first_last), [URL parsing API](https://wiki.php.net/rfc/url_parsing_api), [Fibers](https://wiki.php.net/rfc/fibers), [Deprecate dynamic properties](https://wiki.php.net/rfc/deprecate_dynamic_properties)

**2.2 PHP-FPM và mô hình share-nothing**

- PHP: [FPM](https://www.php.net/manual/en/install.fpm.php), [FPM Configuration](https://www.php.net/manual/en/install.fpm.configuration.php) (mọi directive `pm.*`, `request_*`, `slowlog`), [FPM Status Page](https://www.php.net/manual/en/fpm.status.php)
- [`www.conf.in`](https://github.com/php/php-src/blob/master/sapi/fpm/www.conf.in) trong php-src: file mẫu có chú thích dài cho từng tham số, đọc kỹ phần `pm`
- PHP: [`max_execution_time`](https://www.php.net/manual/en/info.configuration.php#ini.max-execution-time) và ghi chú trong [set_time_limit](https://www.php.net/manual/en/function.set-time-limit.php), [`memory_limit`](https://www.php.net/manual/en/ini.core.php#ini.memory-limit)

**2.3 OPcache và deploy**

- PHP: [OPcache runtime configuration](https://www.php.net/manual/en/opcache.configuration.php) (các mục [`validate_timestamps`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.validate-timestamps), [`memory_consumption`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.memory-consumption), [`max_accelerated_files`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.max-accelerated-files)), [opcache_get_status](https://www.php.net/manual/en/function.opcache-get-status.php)
- RFC: [Make OPcache a non-optional part of PHP](https://wiki.php.net/rfc/make_opcache_required) (8.5)
- Laravel: [Deployment](https://laravel.com/docs/deployment) (mục [Optimization](https://laravel.com/docs/deployment#optimization)), [Configuration Caching](https://laravel.com/docs/configuration#configuration-caching), [Queue Workers and Deployment](https://laravel.com/docs/queues#queue-workers-and-deployment)
- Quy trình deploy tổng quát: [19-devops-cloud.md](19-devops-cloud.md)

**2.4 Lõi Laravel: lifecycle, container, provider, facade**

- Laravel: [Request Lifecycle](https://laravel.com/docs/lifecycle), [Service Container](https://laravel.com/docs/container) (đọc hết, đặc biệt [Contextual Binding](https://laravel.com/docs/container#contextual-binding) và [Binding Scoped](https://laravel.com/docs/container#binding-scoped)), [Service Providers](https://laravel.com/docs/providers), [Facades](https://laravel.com/docs/facades) (mục [How Facades Work](https://laravel.com/docs/facades#how-facades-work)), [Terminable Middleware](https://laravel.com/docs/middleware#terminable-middleware), [Deferred Functions](https://laravel.com/docs/helpers#deferred-functions)
- Source: [`Container.php`](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Container/Container.php) (hàm `build()` và `resolveDependencies()`), [`Facade.php`](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Support/Facades/Facade.php), [`Http/Kernel.php`](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Foundation/Http/Kernel.php), [`bootstrap/app.php`](https://github.com/laravel/laravel/blob/13.x/bootstrap/app.php) của skeleton
- PHP: [fastcgi_finish_request](https://www.php.net/manual/en/function.fastcgi-finish-request.php)

**2.5 Eloquent ở mức làm chủ**

- Laravel: [Eloquent Relationships](https://laravel.com/docs/eloquent-relationships) (mục [Eager Loading](https://laravel.com/docs/eloquent-relationships#eager-loading), [Automatic Eager Loading](https://laravel.com/docs/eloquent-relationships#automatic-eager-loading), [Custom Polymorphic Types](https://laravel.com/docs/eloquent-relationships#custom-polymorphic-types)), [Mutators & Casting](https://laravel.com/docs/eloquent-mutators), [Eloquent](https://laravel.com/docs/eloquent) (mục [Strictness](https://laravel.com/docs/eloquent#configuring-eloquent-strictness), [Mass Updates](https://laravel.com/docs/eloquent#mass-updates), [Global Scopes](https://laravel.com/docs/eloquent#global-scopes), [Observers](https://laravel.com/docs/eloquent#observers))
- Martin Fowler: [Active Record](https://martinfowler.com/eaaCatalog/activeRecord.html), [Data Mapper](https://martinfowler.com/eaaCatalog/dataMapper.html)

**2.6 Queue**

- Laravel: [Queues](https://laravel.com/docs/queues), đọc hết. Quan trọng nhất: [Max Attempts and Timeout](https://laravel.com/docs/queues#max-job-attempts-and-timeout), [Job Expiration and Timeouts](https://laravel.com/docs/queues#job-expirations-and-timeouts) (quan hệ `retry_after` và `timeout`), [Job Middleware](https://laravel.com/docs/queues#job-middleware), [Unique Jobs](https://laravel.com/docs/queues#unique-jobs), [Handling Relationships](https://laravel.com/docs/queues#handling-relationships), [Supervisor Configuration](https://laravel.com/docs/queues#supervisor-configuration)
- Laravel: [Horizon](https://laravel.com/docs/horizon) (mục [Balancing Strategies](https://laravel.com/docs/horizon#balancing-strategies), [Deploying Horizon](https://laravel.com/docs/horizon#deploying-horizon))

**2.7 Các thành phần khác của Laravel**

- Laravel: [Task Scheduling](https://laravel.com/docs/scheduling) (mục [Preventing Task Overlaps](https://laravel.com/docs/scheduling#preventing-task-overlaps), [Running Tasks on One Server](https://laravel.com/docs/scheduling#running-tasks-on-one-server)), [Cache](https://laravel.com/docs/cache) (mục [Stale While Revalidate](https://laravel.com/docs/cache#swr), [Atomic Locks](https://laravel.com/docs/cache#atomic-locks)), [Events](https://laravel.com/docs/events) (mục [Queued Event Listeners](https://laravel.com/docs/events#queued-event-listeners)), [Sanctum](https://laravel.com/docs/sanctum) (mục [How it Works](https://laravel.com/docs/sanctum#how-it-works)), [Authorization](https://laravel.com/docs/authorization), [Broadcasting](https://laravel.com/docs/broadcasting)
- Laravel: [Concurrency](https://laravel.com/docs/concurrency) (mục [How it Works](https://laravel.com/docs/concurrency#how-it-works)), [Context](https://laravel.com/docs/context), [HTTP Client: Concurrent Requests](https://laravel.com/docs/http-client#concurrent-requests), [Processes](https://laravel.com/docs/processes)
- Laravel: [Release Notes](https://laravel.com/docs/releases) (bảng support policy và tính năng 13), [Upgrade Guide](https://laravel.com/docs/upgrade)

**2.8 Chất lượng code PHP: PHPStan, Rector, Pint**

- PHPStan: [Rule Levels](https://phpstan.org/user-guide/rule-levels), [Baseline](https://phpstan.org/user-guide/baseline); [Larastan](https://github.com/larastan/larastan) (README, phần cấu hình); [phpstan-deprecation-rules](https://github.com/phpstan/phpstan-deprecation-rules)
- [Rector documentation](https://getrector.com/documentation) (phần *Set lists* và *PHP version upgrade*); [rector-laravel](https://github.com/driftingly/rector-laravel)
- Laravel: [Pint](https://laravel.com/docs/pint); [PHP-CS-Fixer](https://cs.symfony.com/); [Psalm](https://psalm.dev/)

**3.1 Bên trong Zend Engine: zval, refcount, copy-on-write**

- PHP Internals Book: [Zvals](https://www.phpinternalsbook.com/php7/zvals.html) → [Basic structure](https://www.phpinternalsbook.com/php7/zvals/basic_structure.html), [Memory management](https://www.phpinternalsbook.com/php7/zvals/memory_management.html) (refcount, COW, separation); [zend_string](https://www.phpinternalsbook.com/php7/internal_types/strings/zend_strings.html) (interned string)
- nikic: [Internal value representation in PHP 7, part 1](https://www.npopov.com/2015/05/05/Internal-value-representation-in-PHP-7-part-1.html) và [part 2](https://www.npopov.com/2015/06/19/Internal-value-representation-in-PHP-7-part-2.html), [PHP's new hashtable implementation](https://www.npopov.com/2014/12/22/PHPs-new-hashtable-implementation.html), [PHP 7 Virtual Machine](https://www.npopov.com/2017/04/14/PHP-7-Virtual-machine.html)
- Tham khảo source: [`Zend/zend_types.h`](https://github.com/php/php-src/blob/master/Zend/zend_types.h) (định nghĩa `zval`)

**3.2 Bộ nhớ và garbage collection**

- PHP: [Garbage Collection](https://www.php.net/manual/en/features.gc.php) → [Reference Counting Basics](https://www.php.net/manual/en/features.gc.refcounting-basics.php), [Collecting Cycles](https://www.php.net/manual/en/features.gc.collecting-cycles.php); [gc_status](https://www.php.net/manual/en/function.gc-status.php), [WeakMap](https://www.php.net/manual/en/class.weakmap.php), [WeakReference](https://www.php.net/manual/en/class.weakreference.php), [memory_get_usage](https://www.php.net/manual/en/function.memory-get-usage.php)

**3.3 OPcache chuyên sâu, preloading, JIT**

- PHP: [Preloading](https://www.php.net/manual/en/opcache.preloading.php), [`opcache.jit`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.jit), [`opcache.jit_buffer_size`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.jit-buffer-size), [`opcache.preload`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.preload)
- RFC: [Preloading](https://wiki.php.net/rfc/preload), [JIT](https://wiki.php.net/rfc/jit) (phần benchmark), [New JIT based on IR framework](https://wiki.php.net/rfc/jit-ir)
- PHP.Watch: [PHP 8.4 JIT INI changes](https://php.watch/versions/8.4/opcache-jit-ini-default-changes)
- Tideways: [What's new in PHP 8.5 for performance, debugging and operations](https://tideways.com/profiler/blog/whats-new-in-php-8-5-in-terms-of-performance-debugging-and-operations)

**3.4 PHP-FPM ở mức vận hành**

- PHP Internals Book: [Learning the PHP lifecycle](https://www.phpinternalsbook.com/php7/extensions_design/php_lifecycle.html)
- PHP: [FPM Status Page](https://www.php.net/manual/en/fpm.status.php) (ý nghĩa từng trường), [Persistent Connections](https://www.php.net/manual/en/features.persistent-connections.php)
- Phần Linux (process, memory, OOM killer): [01-os-linux.md](01-os-linux.md)

**3.5 Process sống lâu: queue worker, Octane, daemon**

- Laravel: [Octane](https://laravel.com/docs/octane), đọc kỹ [Dependency Injection and Octane](https://laravel.com/docs/octane#dependency-injection-and-octane) và [Managing Memory Leaks](https://laravel.com/docs/octane#managing-memory-leaks); [Queues: Resource Considerations](https://laravel.com/docs/queues#resource-considerations)
- [FrankenPHP worker mode](https://frankenphp.dev/docs/worker/), [RoadRunner docs](https://roadrunner.dev/docs)
- PHP: [PCNTL](https://www.php.net/manual/en/book.pcntl.php)

**3.6 Hiệu năng và profiling**

- [Xdebug profiler](https://xdebug.org/docs/profiler), [Blackfire docs](https://docs.blackfire.io/), [php-spx](https://github.com/NoiseByNorthwest/php-spx)
- Laravel: [Pulse](https://laravel.com/docs/pulse), [Telescope](https://laravel.com/docs/telescope)
- PHP: [SplFileObject](https://www.php.net/manual/en/class.splfileobject.php), [fgetcsv](https://www.php.net/manual/en/function.fgetcsv.php)

**3.7 Bảo mật đặc thù PHP**

- PHP: [unserialize](https://www.php.net/manual/en/function.unserialize.php) (khung cảnh báo đầu trang), [hash_equals](https://www.php.net/manual/en/function.hash-equals.php), [password_hash](https://www.php.net/manual/en/function.password-hash.php), [random_int](https://www.php.net/manual/en/function.random-int.php), [Handling file uploads](https://www.php.net/manual/en/features.file-upload.php)
- [phpggc](https://github.com/ambionics/phpggc): xem danh sách gadget chain để hiểu mức độ nghiêm trọng
- OWASP: [Laravel Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Laravel_Cheat_Sheet.html), [PHP Configuration Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/PHP_Configuration_Cheat_Sheet.html)
- Laravel: [Encryption](https://laravel.com/docs/encryption) (phần key rotation), [Hashing](https://laravel.com/docs/hashing)

**3.8 So sánh kiến trúc: Laravel, Symfony và ngôn ngữ khác**

- Symfony: [Service Container](https://symfony.com/doc/current/service_container.html), [Compiler Passes](https://symfony.com/doc/current/service_container/compiler_passes.html)
- Doctrine: [Unit of Work](https://www.doctrine-project.org/projects/doctrine-orm/en/current/reference/unitofwork.html)

</details>

<details>
<summary><strong>08. OOP, SOLID, design pattern và clean code</strong> (15 module, 65 link)</summary>

Học chi tiết: [08-oop-design.md](08-oop-design.md)

**1.1 Bốn tính chất OOP và composition over inheritance**

- GoF ch.1, mục *Inheritance versus Composition* và *Program to an interface, not an implementation*
- *Effective Java* item 18 (*Favor composition over inheritance*): ví dụ `InstrumentedHashSet` là minh hoạ fragile base class rõ nhất

**1.2 Interface, abstract class, trait; overloading và overriding**

- PHP: [Object Interfaces](https://www.php.net/manual/en/language.oop5.interfaces.php), [Class Abstraction](https://www.php.net/manual/en/language.oop5.abstract.php), [Traits](https://www.php.net/manual/en/language.oop5.traits.php), [`#[\Override]`](https://www.php.net/manual/en/class.override.php)
- Go: [Effective Go: Interfaces and embedding](https://go.dev/doc/effective_go#embedding)

**1.3 SOLID**

- Robert C. Martin: [The Single Responsibility Principle](https://blog.cleancoder.com/uncle-bob/2014/05/08/SingleReponsibilityPrinciple.html) (định nghĩa "lý do thay đổi" theo người yêu cầu)
- Laravel: [Contracts](https://laravel.com/docs/contracts), [Binding Interfaces to Implementations](https://laravel.com/docs/container#binding-interfaces-to-implementations), [Contextual Binding](https://laravel.com/docs/container#contextual-binding)

**1.4 DRY, KISS, YAGNI; cohesion và coupling**

- Sandi Metz: [The Wrong Abstraction](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction)
- *The Pragmatic Programmer*, 20th anniversary ed. (Thomas, Hunt): topic *The Evils of Duplication* và *Orthogonality*

**2.1 OOP hiện đại trong PHP**

- PHP: [Enumerations](https://www.php.net/manual/en/language.enumerations.php), [Readonly properties](https://www.php.net/manual/en/language.oop5.properties.php#language.oop5.properties.readonly-properties), [Readonly classes](https://www.php.net/manual/en/language.oop5.basic.php#language.oop5.basic.class.readonly), [First class callable syntax](https://www.php.net/manual/en/functions.first_class_callable_syntax.php), [Property Hooks](https://www.php.net/manual/en/language.oop5.property-hooks.php), [Asymmetric visibility](https://www.php.net/manual/en/language.oop5.visibility.php#language.oop5.visibility-members-aviz)
- Release notes: [PHP 8.4](https://www.php.net/releases/8.4/en.php), [PHP 8.5](https://www.php.net/releases/8.5/en.php) (pipe operator, clone with)

**2.2 Creational patterns**

- Refactoring.Guru: [Factory Method](https://refactoring.guru/design-patterns/factory-method), [Abstract Factory](https://refactoring.guru/design-patterns/abstract-factory), [Builder](https://refactoring.guru/design-patterns/builder), [Singleton](https://refactoring.guru/design-patterns/singleton)
- Laravel: [Binding Scoped Singletons](https://laravel.com/docs/container#binding-scoped), [Octane: Dependency Injection](https://laravel.com/docs/octane#dependency-injection-and-octane)
- Mã nguồn Laravel: `vendor/laravel/framework/src/Illuminate/Support/Manager.php` (method `createDriver()`)
- *Effective Java* item 1 (*Consider static factory methods instead of constructors*)

**2.3 Structural patterns**

- Refactoring.Guru: [Adapter](https://refactoring.guru/design-patterns/adapter), [Decorator](https://refactoring.guru/design-patterns/decorator), [Facade](https://refactoring.guru/design-patterns/facade), [Proxy](https://refactoring.guru/design-patterns/proxy), [Composite](https://refactoring.guru/design-patterns/composite)
- Laravel: [Facades](https://laravel.com/docs/facades) (đọc mục *How Facades Work* và *Facades vs. Dependency Injection*), [Extending Bindings](https://laravel.com/docs/container#extending-bindings)

**2.4 Behavioral patterns**

- Refactoring.Guru: [Strategy](https://refactoring.guru/design-patterns/strategy), [Observer](https://refactoring.guru/design-patterns/observer), [Command](https://refactoring.guru/design-patterns/command), [Chain of Responsibility](https://refactoring.guru/design-patterns/chain-of-responsibility), [Template Method](https://refactoring.guru/design-patterns/template-method), [State](https://refactoring.guru/design-patterns/state), [Visitor](https://refactoring.guru/design-patterns/visitor)
- Java: [JEP 409: Sealed Classes](https://openjdk.org/jeps/409), [JEP 441: Pattern Matching for switch](https://openjdk.org/jeps/441), [JEP 440: Record Patterns](https://openjdk.org/jeps/440)
- PHP: [`match`](https://www.php.net/manual/en/control-structures.match.php); [spatie/laravel-model-states](https://spatie.be/docs/laravel-model-states); [nikic/PHP-Parser](https://github.com/nikic/PHP-Parser) (đọc phần *Node traversation* trong docs)
- Laravel: [Pipeline](https://laravel.com/docs/helpers#pipeline), [Events](https://laravel.com/docs/events)

**2.5 Pattern tầng dữ liệu**

- PoEAA catalog: [Active Record](https://martinfowler.com/eaaCatalog/activeRecord.html), [Data Mapper](https://martinfowler.com/eaaCatalog/dataMapper.html), [Repository](https://martinfowler.com/eaaCatalog/repository.html), [Unit of Work](https://martinfowler.com/eaaCatalog/unitOfWork.html)
- Laravel: [Query Scopes](https://laravel.com/docs/eloquent#query-scopes)

**2.6 DI, IoC container và Service Locator**

- Martin Fowler: [Inversion of Control Containers and the Dependency Injection pattern](https://martinfowler.com/articles/injection.html) (có phần so sánh với Service Locator)
- Laravel: [Service Container](https://laravel.com/docs/container) (đọc hết), [Facades vs. Dependency Injection](https://laravel.com/docs/facades#facades-vs-dependency-injection)
- [PSR-11: Container interface](https://www.php-fig.org/psr/psr-11/) (đọc phần meta về việc không dùng container như service locator)

**2.7 Value object, immutability, Law of Demeter**

- Martin Fowler: [Value Object](https://martinfowler.com/bliki/ValueObject.html), [Tell Don't Ask](https://martinfowler.com/bliki/TellDontAsk.html)
- *Effective Java* item 17 (*Minimize mutability*)

**3.1 Clean code và code smell**

- *Refactoring* 2nd ed., ch.3 *Bad Smells in Code*; Refactoring.Guru: [Code Smells](https://refactoring.guru/refactoring/smells)
- *Clean Code* (Robert C. Martin): ch.2 (tên), ch.3 (hàm). Đọc có phê phán: một số lời khuyên (hàm cực ngắn) bị tranh cãi nhiều

**3.2 Refactoring và code legacy**

- *Refactoring* 2nd ed., ch.1–2 (ví dụ mở đầu và nguyên tắc) và [catalog](https://refactoring.com/catalog/)
- Martin Fowler: [Branch By Abstraction](https://martinfowler.com/bliki/BranchByAbstraction.html)
- [Rector](https://getrector.com/documentation), [PHPStan: The Baseline](https://phpstan.org/user-guide/baseline)
- *Working Effectively with Legacy Code*: ch.2 (*Working with Feedback*), ch.4 (*The Seam Model*), ch.13 (*I Need to Make a Change, but I Don't Know What Tests to Write*: characterization test)

**3.3 Anti-pattern và over-engineering**

- Martin Fowler: [Anemic Domain Model](https://martinfowler.com/bliki/AnemicDomainModel.html), [Yagni](https://martinfowler.com/bliki/Yagni.html)
- Sandi Metz: [The Wrong Abstraction](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction) (đọc lại với góc nhìn "tháo abstraction sai")
- Phần DDD và mức đầu tư kiến trúc: [15-architecture.md](15-architecture.md)

**3.4 Đối chiếu thiết kế giữa PHP, Java và Go**

- Go: [Code Review Comments: Interfaces](https://go.dev/wiki/CodeReviewComments#interfaces)
- Refactoring.Guru: mỗi trang pattern có ví dụ Go, đọc để thấy pattern co lại thế nào khi không có kế thừa
- Phần ngôn ngữ: [05-php-laravel.md](05-php-laravel.md), [06-java-spring.md](06-java-spring.md), [07-go.md](07-go.md)

</details>

<details>
<summary><strong>06. Java, JVM và Spring</strong> (17 module, 77 link)</summary>

Học chi tiết: [06-java-spring.md](06-java-spring.md)

**1.1 Ngôn ngữ cốt lõi**

- dev.java: [Getting started / Language basics](https://dev.java/learn/) (mục *Classes and Objects*, *Numbers and Strings*, *Interfaces*)
- Repo: [java/01-basics/Basics.java](../java/01-basics/Basics.java) (`==` và `equals`, collection, exception)
- *Effective Java*: Item 10–11 (`equals`, `hashCode`), Item 17 (immutability)

**1.2 Exception, lambda, Stream, Optional**

- dev.java: [Exceptions](https://dev.java/learn/exceptions/), [Lambda Expressions](https://dev.java/learn/lambdas/), [Collections and Streams](https://dev.java/learn/api/collections-and-streams/)
- Javadoc: [java.util.stream package summary](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/stream/package-summary.html) (mục *Non-interference*, *Stateless behaviors*)

**1.3 Collections cơ bản**

- Repo (bản dịch dev.java): [Collections](../java/03-collections/README.md), đặc biệt [List](../java/03-collections/05-list.md), [Map](../java/03-collections/09-map.md), [Chọn key immutable](../java/03-collections/13-chon-key-immutable.md), [ArrayList vs LinkedList](../java/03-collections/14-arraylist-vs-linkedlist.md)

**1.4 Spring và Spring Boot cơ bản**

- Spring: [The IoC Container](https://docs.spring.io/spring-framework/reference/core/beans.html) (đọc *Dependencies*, *Bean Scopes*)
- Boot: [Auto-configuration](https://docs.spring.io/spring-boot/reference/using/auto-configuration.html), [Creating Your Own Auto-configuration](https://docs.spring.io/spring-boot/reference/features/developing-auto-configuration.html) (mục *Condition Annotations*), [Externalized Configuration](https://docs.spring.io/spring-boot/reference/features/external-config.html), [Profiles](https://docs.spring.io/spring-boot/reference/features/profiles.html)

**1.5 Đối chiếu với PHP/Laravel**

- PHP: [FPM configuration](https://www.php.net/manual/en/install.fpm.configuration.php) (`pm.*`); Laravel: [Service Container](https://laravel.com/docs/container) (binding, singleton, scoped); Spring: [Bean Scopes](https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html)

**2.1 Generics và Java hiện đại (17 → 25)**

- Oracle tutorial: [Generics](https://docs.oracle.com/javase/tutorial/java/generics/index.html) (mục *Wildcards*, *Type Erasure*)
- JEP: [395 Records](https://openjdk.org/jeps/395), [409 Sealed Classes](https://openjdk.org/jeps/409), [440 Record Patterns](https://openjdk.org/jeps/440), [441 Pattern Matching for switch](https://openjdk.org/jeps/441), [485 Stream Gatherers](https://openjdk.org/jeps/485), [513 Flexible Constructor Bodies](https://openjdk.org/jeps/513), [512 Compact Source Files](https://openjdk.org/jeps/512)
- Danh sách JEP theo bản: [JDK 25](https://openjdk.org/projects/jdk/25/), [JDK 27](https://openjdk.org/projects/jdk/27/)

**2.2 Collections bên trong**

- Source: [HashMap.java](https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/util/HashMap.java) (đọc comment *Implementation notes* ở đầu class)
- Javadoc: [ConcurrentHashMap](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html)
- dev.java: [Collections Framework](https://dev.java/learn/api/collections-framework/)

**2.3 Concurrency trong Java**

- [JSR-133 FAQ](https://www.cs.umd.edu/~pugh/java/memoryModel/jsr-133-faq.html): JMM ngắn gọn; nâng cao: [Shipilëv: JMM Pragmatics](https://shipilev.net/blog/2014/jmm-pragmatics/)
- Javadoc: [ThreadPoolExecutor](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html) (mục *Queuing*, *Rejected tasks*)
- *Java Concurrency in Practice*: ch.3 (visibility), ch.8 (thread pool)

**2.4 Spring bên trong: lifecycle, proxy, transaction, async**

- Spring: [Customizing the Nature of a Bean](https://docs.spring.io/spring-framework/reference/core/beans/factory-nature.html), [Proxying Mechanisms](https://docs.spring.io/spring-framework/reference/core/aop/proxying.html) (mục *Understanding AOP Proxies*, có ví dụ self-invocation)
- Transaction: [Declarative Transaction Management](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative.html), [Propagation](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/tx-propagation.html), [Rolling Back](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/rolling-back.html), [Transaction-bound Events](https://docs.spring.io/spring-framework/reference/data-access/transaction/event.html)
- Boot: [Task Execution and Scheduling](https://docs.spring.io/spring-boot/reference/features/task-execution-and-scheduling.html)
- Spring: [Resilience Features](https://docs.spring.io/spring-framework/reference/core/resilience.html)

**2.5 JPA/Hibernate**

- Boot: [Open EntityManager in View](https://docs.spring.io/spring-boot/reference/data/sql.html#data.sql.jpa-and-spring-data.open-entity-manager-in-view)
- Spring Data JPA: [Query Methods](https://docs.spring.io/spring-data/jpa/reference/jpa/query-methods.html) (mục projection, entity graph)
- Vlad Mihalcea: [N+1 query problem](https://vladmihalcea.com/n-plus-1-query-problem/), [The Open Session in View Anti-Pattern](https://vladmihalcea.com/the-open-session-in-view-anti-pattern/)
- HikariCP: [About Pool Sizing](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing)
- Hibernate User Guide: chương *Persistence Contexts*, *Fetching*, *Batching*, *Locking*

**2.6 Web: MVC, WebFlux, Security, API versioning**

- Spring: [Spring Web MVC](https://docs.spring.io/spring-framework/reference/web/webmvc.html), [WebFlux](https://docs.spring.io/spring-framework/reference/web/webflux.html) (mục *Overview*, *Concurrency Model*), [API Versioning](https://docs.spring.io/spring-framework/reference/web/webmvc-versioning.html)
- Spring Security: [Servlet Architecture](https://docs.spring.io/spring-security/reference/servlet/architecture.html), [OAuth 2.0 Resource Server JWT](https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/jwt.html)

**2.7 Testing trong Spring**

- Boot: [Testing](https://docs.spring.io/spring-boot/reference/testing/index.html), [Testing Spring Boot Applications](https://docs.spring.io/spring-boot/reference/testing/spring-boot-applications.html) (mục *Auto-configured Tests*), [Testcontainers](https://docs.spring.io/spring-boot/reference/testing/testcontainers.html)
- Spring: [TestContext Framework](https://docs.spring.io/spring-framework/reference/testing/testcontext-framework.html) (mục *Context Caching*)
- [Testcontainers for Java](https://java.testcontainers.org/), [JMH](https://github.com/openjdk/jmh)

**3.1 Bộ nhớ JVM và GC**

- Oracle: [HotSpot GC Tuning Guide (JDK 25)](https://docs.oracle.com/en/java/javase/25/gctuning/) (đọc *Ergonomics*, *Garbage-First Garbage Collector*, *The Z Garbage Collector*)
- JEP: [474 ZGC generational mặc định](https://openjdk.org/jeps/474), [490 bỏ non-generational ZGC](https://openjdk.org/jeps/490), [519 Compact Object Headers](https://openjdk.org/jeps/519), [534 Compact Object Headers by Default](https://openjdk.org/jeps/534), [523 G1 mặc định mọi môi trường](https://openjdk.org/jeps/523)

**3.2 JIT, class loading, khởi động**

- JEP: [483 AOT Class Loading & Linking](https://openjdk.org/jeps/483), [514 AOT Command-Line Ergonomics](https://openjdk.org/jeps/514), [515 AOT Method Profiling](https://openjdk.org/jeps/515)
- Boot: [GraalVM Native Images](https://docs.spring.io/spring-boot/reference/packaging/native-image/index.html) (mục *Key Differences with JVM Deployments*)

**3.3 Chẩn đoán production và JVM trong container**

- Oracle: [Troubleshooting Guide (JDK 25)](https://docs.oracle.com/en/java/javase/25/troubleshoot/) (chương *Diagnostic Tools*, *Troubleshoot Memory Leaks*)
- dev.java: [JDK Flight Recorder](https://dev.java/learn/jvm/jfr/)
- [async-profiler](https://github.com/async-profiler/async-profiler), [Eclipse MAT](https://eclipse.dev/mat/)

**3.4 Virtual thread, structured concurrency, scoped values**

- JEP: [444 Virtual Threads](https://openjdk.org/jeps/444), [491 Synchronize Virtual Threads without Pinning](https://openjdk.org/jeps/491), [506 Scoped Values](https://openjdk.org/jeps/506), [533 Structured Concurrency (Seventh Preview)](https://openjdk.org/jeps/533)
- dev.java: [Virtual Threads](https://dev.java/learn/new-features/virtual-threads/)
- Boot: [SpringApplication](https://docs.spring.io/spring-boot/reference/features/spring-application.html) (mục *Virtual Threads*)

**3.5 Nâng cấp Spring Boot 4 / Spring Framework 7**

- [Spring Boot 4.0.0 available now](https://spring.io/blog/2025/11/20/spring-boot-4-0-0-available-now/)
- [Spring Boot 4.0 Release Notes](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Release-Notes), [Migration Guide](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide)
- Spring: [Null-safety](https://docs.spring.io/spring-framework/reference/core/null-safety.html)

</details>

<details>
<summary><strong>07. Go</strong> (18 module, 82 link)</summary>

Học chi tiết: [07-go.md](07-go.md)

**1.1 Slice, map, string**

- Go blog: [Slices intro](https://go.dev/blog/slices-intro), [Arrays, slices and strings](https://go.dev/blog/slices), [Maps in action](https://go.dev/blog/maps), [Strings, bytes, runes](https://go.dev/blog/strings), [Swiss Tables](https://go.dev/blog/swisstable)
- Repo: [go/01-basics/main.go](../go/01-basics/main.go) (phần slice và map)

**1.2 Struct, method, interface**

- Effective Go: [Interfaces](https://go.dev/doc/effective_go#interfaces), [Embedding](https://go.dev/doc/effective_go#embedding)

**1.3 Error, panic, defer**

- Go blog: [Working with Errors in Go 1.13](https://go.dev/blog/go1.13-errors), [Errors are values](https://go.dev/blog/errors-are-values), [Defer, Panic, and Recover](https://go.dev/blog/defer-panic-and-recover)
- Package [errors](https://pkg.go.dev/errors)

**1.4 Goroutine, channel, sync cơ bản**

- Effective Go: [Concurrency](https://go.dev/doc/effective_go#concurrency)
- Package [sync](https://pkg.go.dev/sync) (đọc [WaitGroup.Go](https://pkg.go.dev/sync#WaitGroup.Go))

**1.5 Testing cơ bản**

- Package [testing](https://pkg.go.dev/testing) (mục [Subtests and Sub-benchmarks](https://pkg.go.dev/testing#hdr-Subtests_and_Sub_benchmarks))
- Wiki: [TableDrivenTests](https://go.dev/wiki/TableDrivenTests); Go blog: [Using Subtests and Sub-benchmarks](https://go.dev/blog/subtests)
- Package [net/http/httptest](https://pkg.go.dev/net/http/httptest)

**1.6 Đối chiếu với PHP**

- PHP: [FPM configuration](https://www.php.net/manual/en/install.fpm.configuration.php)
- Go: [net/http Server](https://pkg.go.dev/net/http#Server) (mỗi connection một goroutine)

**2.1 Interface sâu, generics, ngữ nghĩa vòng lặp**

- FAQ: [Why is my nil error value not equal to nil?](https://go.dev/doc/faq#nil_error)
- Spec: [Method sets](https://go.dev/ref/spec#Method_sets)
- Go blog: [When To Use Generics](https://go.dev/blog/when-generics), [Fixing For Loops in Go 1.22](https://go.dev/blog/loopvar-preview), [Range Over Function Types](https://go.dev/blog/range-functions), [Generic Methods](https://go.dev/blog/generic-methods)

**2.2 context, errgroup, pattern, goroutine leak**

- Go blog: [Go Concurrency Patterns: Context](https://go.dev/blog/context), [Pipelines and cancellation](https://go.dev/blog/pipelines)
- Package [context](https://pkg.go.dev/context), [errgroup](https://pkg.go.dev/golang.org/x/sync/errgroup)
- Release notes 1.23: [Timer changes](https://go.dev/doc/go1.23#timer-changes)

**2.3 Memory model, atomic, race**

- [The Go Memory Model](https://go.dev/ref/mem) (phần *Advice* ở đầu và *Synchronization*)
- [Data Race Detector](https://go.dev/doc/articles/race_detector)
- Package [sync/atomic](https://pkg.go.dev/sync/atomic)

**2.4 net/http production**

- Package [net/http](https://pkg.go.dev/net/http) (đọc type `Server`, `Client`, `Transport`)
- Go blog: [Routing Enhancements for Go 1.22](https://go.dev/blog/routing-enhancements)
- Cloudflare: [The complete guide to Go net/http timeouts](https://blog.cloudflare.com/the-complete-guide-to-golang-net-http-timeouts/) (có sơ đồ timeout nào tính từ lúc nào)

**2.5 database/sql và JSON**

- [Accessing relational databases](https://go.dev/doc/database/), [Managing connections](https://go.dev/doc/database/manage-connections)
- Package [database/sql](https://pkg.go.dev/database/sql), [encoding/json](https://pkg.go.dev/encoding/json), [encoding/json/v2](https://pkg.go.dev/encoding/json/v2)
- Go blog: [A new experimental Go API for JSON](https://go.dev/blog/jsonv2-exp)

**2.6 Testing nâng cao**

- Package [testing](https://pkg.go.dev/testing) (mục [Benchmarks](https://pkg.go.dev/testing#hdr-Benchmarks), [Fuzzing](https://pkg.go.dev/testing#hdr-Fuzzing))
- Go blog: [More predictable benchmarking with testing.B.Loop](https://go.dev/blog/testing-b-loop), [Testing concurrent code with testing/synctest](https://go.dev/blog/synctest)
- [Go Fuzzing](https://go.dev/doc/security/fuzz/), [Tutorial: Getting started with fuzzing](https://go.dev/doc/tutorial/fuzz)
- Package [testing/synctest](https://pkg.go.dev/testing/synctest), [goleak](https://github.com/uber-go/goleak), [Coverage for integration tests](https://go.dev/doc/build-cover)

**2.7 Logging với log/slog**

- Go blog: [Structured Logging with slog](https://go.dev/blog/slog)
- Package [log/slog](https://pkg.go.dev/log/slog)

**2.8 Project layout và module**

- [Organizing a Go module](https://go.dev/doc/modules/layout)
- [cmd/go: Internal packages](https://pkg.go.dev/cmd/go#hdr-Internal_packages)
- [Go Modules Reference](https://go.dev/ref/mod) (mục [MVS](https://go.dev/ref/mod#minimal-version-selection), [Major version suffixes](https://go.dev/ref/mod#major-version-suffixes)); [Go Toolchains](https://go.dev/doc/toolchain)
- Russ Cox: [Minimal Version Selection](https://research.swtch.com/vgo-mvs)

**3.1 Scheduler G-M-P**

- Ardan Labs: [Scheduling In Go, Part I (OS)](https://www.ardanlabs.com/blog/2018/08/scheduling-in-go-part1.html), [Part II (Go Scheduler)](https://www.ardanlabs.com/blog/2018/08/scheduling-in-go-part2.html)
- 🔴 Dmitry Vyukov: [Scalable Go Scheduler Design Doc](https://golang.org/s/go11sched)

**3.2 Bộ nhớ: escape analysis và GC**

- [A Guide to the Go Garbage Collector](https://go.dev/doc/gc-guide) (mục [GOGC](https://go.dev/doc/gc-guide#GOGC), [Memory limit](https://go.dev/doc/gc-guide#Memory_limit), [Eliminating heap allocations](https://go.dev/doc/gc-guide#Eliminating_heap_allocations)). Đọc phần có hình tương tác
- Go blog: [The Green Tea Garbage Collector](https://go.dev/blog/greenteagc)
- Release notes 1.26: [Runtime](https://go.dev/doc/go1.26#runtime)

**3.3 Profiling và chẩn đoán**

- [Diagnostics](https://go.dev/doc/diagnostics) (mục [Profiling](https://go.dev/doc/diagnostics#profiling))
- Package [net/http/pprof](https://pkg.go.dev/net/http/pprof), [runtime/pprof](https://pkg.go.dev/runtime/pprof)
- Go blog: [Profiling Go Programs](https://go.dev/blog/pprof), [Flight Recorder in Go 1.25](https://go.dev/blog/flight-recorder)
- [Profile-guided optimization](https://go.dev/doc/pgo)

**3.4 Go trong container**

- Go blog: [Container-aware GOMAXPROCS](https://go.dev/blog/container-aware-gomaxprocs)
- Release notes: [Go 1.25](https://go.dev/doc/go1.25)
- [automaxprocs](https://github.com/uber-go/automaxprocs) (bối cảnh cho bản Go cũ)

</details>

### Giao tiếp giữa các hệ thống

<details>
<summary><strong>09. Thiết kế API</strong> (15 module, 73 link)</summary>

Học chi tiết: [09-api-design.md](09-api-design.md)

**1.1 Resource và method semantics**

- RFC 9110: [Section 9: Methods](https://www.rfc-editor.org/rfc/rfc9110#section-9) (đọc 9.2 *Common Method Properties*)
- [RFC 7396](https://www.rfc-editor.org/rfc/rfc7396) (Merge Patch, ngắn), [RFC 6902](https://www.rfc-editor.org/rfc/rfc6902) (JSON Patch)
- Google AIP: [AIP-136 Custom methods](https://google.aip.dev/136)
- Martin Fowler: [Richardson Maturity Model](https://martinfowler.com/articles/richardsonMaturityModel.html)

**1.2 Status code**

- RFC 9110: [Section 15: Status Codes](https://www.rfc-editor.org/rfc/rfc9110#section-15)
- [RFC 6585](https://www.rfc-editor.org/rfc/rfc6585) (`428`, `429`)
- [MDN: HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status) để tra nhanh

**1.3 Format lỗi thống nhất**

- [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457): đọc section 3 (members) và 4 (định nghĩa problem type mới)
- Zalando: [chương HTTP status codes and errors](https://opensource.zalando.com/restful-api-guidelines/#http-status-codes-and-errors)
- Laravel: [Rendering Exceptions](https://laravel.com/docs/errors#rendering-exceptions)

**1.4 Filtering, sorting, pagination**

- Google AIP: [AIP-158 Pagination](https://google.aip.dev/158)
- Use The Index, Luke: [Paging Through Results](https://use-the-index-luke.com/sql/partial-results/fetch-next-page)
- [RFC 8288](https://www.rfc-editor.org/rfc/rfc8288) (Web Linking), lướt section 3
- Laravel: [Cursor Pagination](https://laravel.com/docs/pagination#cursor-pagination)

**2.1 Idempotency key và retry an toàn**

- Stripe: [Idempotent requests](https://docs.stripe.com/api/idempotent_requests), [Designing robust and predictable APIs with idempotency](https://stripe.com/blog/idempotency)
- Brandur: [Implementing Stripe-like Idempotency Keys in Postgres](https://brandur.org/idempotency-keys): thiết kế đầy đủ với recovery point, đọc kỹ
- AWS Builders' Library: [Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)
- [draft-ietf-httpapi-idempotency-key-header](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/) (bản draft cuối, tham khảo ngữ nghĩa)

**2.2 Ghi đồng thời, bulk, long-running operation**

- RFC 9110: [Section 13: Conditional Requests](https://www.rfc-editor.org/rfc/rfc9110#section-13), [Section 8.8.3: ETag](https://www.rfc-editor.org/rfc/rfc9110#section-8.8.3)
- Google AIP: [AIP-151 Long-running operations](https://google.aip.dev/151), [AIP-233 Batch create](https://google.aip.dev/233)
- Zalando: [chương HTTP status codes and errors](https://opensource.zalando.com/restful-api-guidelines/#http-status-codes-and-errors) (quy tắc dùng `207` cho batch/bulk request)

**2.3 Rate limiting, auth và CORS**

- [draft-ietf-httpapi-ratelimit-headers](https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/)
- [MDN: CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS) (đọc hết, có sơ đồ preflight)
- [OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)

**2.4 Webhook**

- [Standard Webhooks specification](https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md): tên header (`webhook-id`, `webhook-timestamp`, `webhook-signature`), cách ký, retry
- Stripe: [Receive webhook events](https://docs.stripe.com/webhooks) (đọc phần *Best practices*)

**2.5 Gọi API bên thứ ba**

- AWS Builders' Library: [Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)
- Laravel: [HTTP Client: Timeout](https://laravel.com/docs/http-client#timeout), [Retries](https://laravel.com/docs/http-client#retries), [Testing / Faking](https://laravel.com/docs/http-client#testing)
- Martin Fowler: [Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html)
- Resilience pattern chi tiết: [14-distributed-systems.md](14-distributed-systems.md)

**2.6 Tầng Laravel cho API**

- Laravel: [Eloquent API Resources](https://laravel.com/docs/eloquent-resources), [Form Request Validation](https://laravel.com/docs/validation#form-request-validation), [Sanctum](https://laravel.com/docs/sanctum), [Passport](https://laravel.com/docs/passport) (đọc mục *Passport or Sanctum?*), [Rate Limiting (routing)](https://laravel.com/docs/routing#rate-limiting), [Rate Limiting (RateLimiter)](https://laravel.com/docs/rate-limiting)
- Laravel: [Mass Assignment](https://laravel.com/docs/eloquent#mass-assignment)

**2.7 Serialization**

- PHP: [json_encode](https://www.php.net/manual/en/function.json-encode.php), [JSON constants](https://www.php.net/manual/en/json.constants.php)
- Protobuf: [ProtoJSON Format](https://protobuf.dev/programming-guides/json/) (bảng mapping, int64 thành string)
- [RFC 3339](https://www.rfc-editor.org/rfc/rfc3339) (section 5.6)

**3.1 Tiến hoá API: versioning, deprecation, backward compatibility**

- [RFC 9745: The Deprecation HTTP Response Header Field](https://www.rfc-editor.org/rfc/rfc9745), [RFC 8594: The Sunset HTTP Header Field](https://www.rfc-editor.org/rfc/rfc8594)
- Google AIP: [AIP-180 Backwards compatibility](https://google.aip.dev/180) (bảng thay đổi nào là breaking, rất đáng đọc)
- Stripe: [APIs as infrastructure: future-proofing Stripe with versioning](https://stripe.com/blog/api-versioning)
- Zalando: [chương Compatibility](https://opensource.zalando.com/restful-api-guidelines/#compatibility) và [Deprecation](https://opensource.zalando.com/restful-api-guidelines/#deprecation)
- Martin Fowler: [Tolerant Reader](https://martinfowler.com/bliki/TolerantReader.html)

**3.2 GraphQL**

- [GraphQL Learn](https://graphql.org/learn/): đọc hết phần *Learn*, đặc biệt *Best Practices* (pagination, authorization, caching)
- [graphql/dataloader](https://github.com/graphql/dataloader): README
- Lighthouse: [The N+1 Query Problem](https://lighthouse-php.com/master/performance/n-plus-one.html), [Resource Exhaustion](https://lighthouse-php.com/master/security/resource-exhaustion.html) (depth, complexity)

**3.3 gRPC và Protobuf**

- gRPC: [Core concepts](https://grpc.io/docs/what-is-grpc/core-concepts/), [Deadlines](https://grpc.io/docs/guides/deadlines/), [Status codes](https://grpc.io/docs/guides/status-codes/), [PHP](https://grpc.io/docs/languages/php/)
- Protobuf: [Language Guide (proto3)](https://protobuf.dev/programming-guides/proto3/) (mục *Updating A Message Type*), [Proto Best Practices](https://protobuf.dev/best-practices/dos-donts/)
- [buf breaking](https://buf.build/docs/breaking/)
- Kubernetes blog: [gRPC Load Balancing on Kubernetes without Tears](https://kubernetes.io/blog/2018/11/07/grpc-load-balancing-on-kubernetes-without-tears/)

**3.4 Contract, tài liệu và hạ tầng API**

- [OpenAPI 3.2.0](https://spec.openapis.org/oas/v3.2.0.html), [OpenAPI 3.1.1](https://spec.openapis.org/oas/v3.1.1.html); [learn.openapis.org](https://learn.openapis.org/) để học từ đầu
- [Spectral](https://github.com/stoplightio/spectral), [oasdiff](https://github.com/oasdiff/oasdiff)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/): section 3 (`traceparent`, `tracestate`)
- Sam Newman: [Backends For Frontends](https://samnewman.io/patterns/architectural/bff/)
- [Pact docs](https://docs.pact.io/)

</details>

<details>
<summary><strong>10. Bảo mật</strong> (20 module, 125 link)</summary>

Học chi tiết: [10-security.md](10-security.md)

**1.1 Lưu password**

- OWASP: [Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) (tham số argon2id/bcrypt khuyến nghị), [Forgot Password Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html)
- NIST SP 800-63B-4: mục về password (memorized secret) trong [phần Authenticators](https://pages.nist.gov/800-63-4/sp800-63b/authenticators/)
- [Have I Been Pwned: Pwned Passwords API](https://haveibeenpwned.com/API/v3#PwnedPasswords) (cơ chế k-anonymity)
- PortSwigger: [Password reset poisoning](https://portswigger.net/web-security/host-header/exploiting/password-reset-poisoning)

**1.2 Session và cookie**

- OWASP: [Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- MDN: [Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie) (mục cookie prefixes và `SameSite`)
- Chromium: [SameSite Updates](https://www.chromium.org/updates/same-site/) (lịch sử Lax-by-default và Lax+POST)
- PortSwigger: [Bypassing SameSite cookie restrictions](https://portswigger.net/web-security/csrf/bypassing-samesite-restrictions)
- Laravel: [Regenerating the Session ID](https://laravel.com/docs/session#regenerating-the-session-id)

**1.3 Injection, XSS, CSRF**

- OWASP: [SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html), [XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html), [CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- PortSwigger: [SQL injection](https://portswigger.net/web-security/sql-injection), [Cross-site scripting](https://portswigger.net/web-security/cross-site-scripting), [CSRF](https://portswigger.net/web-security/csrf). Làm ít nhất 3 lab mỗi chủ đề
- Laravel: [CSRF Protection](https://laravel.com/docs/csrf), [Blade: Displaying Unescaped Data](https://laravel.com/docs/blade#displaying-unescaped-data)

**1.4 Crypto cơ bản**

- OWASP: [Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- PHP: [random_bytes](https://www.php.net/manual/en/function.random-bytes.php), [hash_hmac](https://www.php.net/manual/en/function.hash-hmac.php), [hash_equals](https://www.php.net/manual/en/function.hash-equals.php)
- *Serious Cryptography*: ch.1 (encryption), ch.2 (randomness), ch.6 (hash), ch.7 (MAC)

**1.5 Authentication, authorization và IDOR**

- OWASP: [Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html), [IDOR Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html)
- OWASP API Top 10: [API1:2023 BOLA](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/)
- PortSwigger: [Access control](https://portswigger.net/web-security/access-control)

**2.1 JWT**

- [RFC 8725: JWT Best Current Practices](https://www.rfc-editor.org/rfc/rfc8725): đọc hết mục 2 và 3, ngắn
- [RFC 9068: JWT Profile for OAuth 2.0 Access Tokens](https://www.rfc-editor.org/rfc/rfc9068)
- PortSwigger: [JWT attacks](https://portswigger.net/web-security/jwt) và [Algorithm confusion](https://portswigger.net/web-security/jwt/algorithm-confusion), làm lab
- [jwt.io introduction](https://jwt.io/introduction)

**2.2 Vòng đời token: revocation, refresh, nơi lưu, BFF**

- [RFC 10017: OAuth 2.0 for Browser-Based Applications](https://www.rfc-editor.org/rfc/rfc10017): mục 5 (mối đe doạ từ JavaScript độc) và mục 6 (BFF, token-mediating backend, browser-based client)
- RFC 9700: [mục 4.14 Refresh Token Protection](https://www.rfc-editor.org/rfc/rfc9700#section-4.14)
- [Auth0: Refresh Token Rotation](https://auth0.com/docs/secure/tokens/refresh-tokens/refresh-token-rotation) (có mục reuse detection)
- OWASP: [JSON Web Token Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_Cheat_Sheet.html): phần token sidejacking và revocation

**2.3 OAuth 2.0 và OIDC**

- [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700): mục 2 (khuyến nghị tóm tắt) là bắt buộc; mục 4 đọc theo từng tấn công
- [RFC 7636: PKCE](https://www.rfc-editor.org/rfc/rfc7636)
- [OAuth 2.0 Simplified](https://www.oauth.com/) (Aaron Parecki): cách dễ đọc nhất để nắm các flow
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html): mục 2 (ID Token) và 3.1 (Authorization Code Flow)
- PortSwigger: [OAuth 2.0 authentication vulnerabilities](https://portswigger.net/web-security/oauth)
- OWASP: [OAuth 2.0 Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/OAuth2_Cheat_Sheet.html)
- Laravel: [Passport or Sanctum?](https://laravel.com/docs/passport#passport-or-sanctum), [Passport PKCE](https://laravel.com/docs/passport#code-grant-pkce)

**2.4 MFA và passkey**

- [passkeys.dev](https://passkeys.dev/): hướng dẫn triển khai cho developer
- [W3C WebAuthn Level 3](https://www.w3.org/TR/webauthn-3/): đọc phần giới thiệu và các use case, không cần đọc hết
- OWASP: [Multifactor Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html)
- [RFC 6238: TOTP](https://www.rfc-editor.org/rfc/rfc6238)
- PHP: [web-auth/webauthn-framework](https://github.com/web-auth/webauthn-framework) (thư viện WebAuthn cho PHP)

**2.5 Authorization: mô hình và tầng kiểm tra**

- OWASP: [Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [Zanzibar: Google's Consistent, Global Authorization System](https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/) (paper, 2019): đọc mục 2 về mô hình dữ liệu
- [OpenFGA concepts](https://openfga.dev/docs/concepts)
- Laravel: [Authorization](https://laravel.com/docs/authorization) (Gates, Policies, `before` filter)

**2.6 Lỗ hổng web và API theo OWASP**

- [OWASP Top 10:2025](https://owasp.org/Top10/2025/): đọc trang giới thiệu (thay đổi so với 2021) và trang của A01, A03, A10
- [OWASP API Security Top 10 2023](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)
- OWASP cheat sheets: [SSRF](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html), [XXE](https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html), [Deserialization](https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html), [Mass Assignment](https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html), [File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html), [OS Command Injection](https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html), [Unvalidated Redirects](https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html)
- PortSwigger (làm lab): [SSRF](https://portswigger.net/web-security/ssrf), [XXE](https://portswigger.net/web-security/xxe), [Path traversal](https://portswigger.net/web-security/file-path-traversal), [OS command injection](https://portswigger.net/web-security/os-command-injection), [Insecure deserialization](https://portswigger.net/web-security/deserialization), [File upload](https://portswigger.net/web-security/file-upload)
- PHP: [unserialize](https://www.php.net/manual/en/function.unserialize.php) (đọc khung cảnh báo), [escapeshellarg](https://www.php.net/manual/en/function.escapeshellarg.php)

**2.7 Header bảo mật, CSRF hiện đại, CORS**

- [web.dev: Protect your resources with Fetch Metadata](https://web.dev/articles/fetch-metadata)
- OWASP: [CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) (mục Fetch Metadata), [HTTP Headers Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html), [Content Security Policy Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)
- PortSwigger: [CORS](https://portswigger.net/web-security/cors), [Clickjacking](https://portswigger.net/web-security/clickjacking)
- Laravel: [CSRF: Origin Verification](https://laravel.com/docs/csrf#origin-verification)
- [Mozilla HTTP Observatory](https://developer.mozilla.org/en-US/observatory): quét header của site thật

**2.8 Tầng PHP/Laravel**

- PHP: [password_hash](https://www.php.net/manual/en/function.password-hash.php), [password_needs_rehash](https://www.php.net/manual/en/function.password-needs-rehash.php), [PHP 8.4: Other Changes](https://www.php.net/manual/en/migration84.other-changes.php) (bcrypt cost), [Sodium](https://www.php.net/manual/en/book.sodium.php)
- [Hashing](https://laravel.com/docs/hashing), [Encryption: rotating keys](https://laravel.com/docs/encryption#gracefully-rotating-encryption-keys), [Encrypted Casting](https://laravel.com/docs/eloquent-mutators#encrypted-casting)
- [Sanctum: How it Works](https://laravel.com/docs/sanctum#how-it-works), [SPA Authentication](https://laravel.com/docs/sanctum#spa-authentication), [Token Expiration](https://laravel.com/docs/sanctum#token-expiration)
- [Mass Assignment](https://laravel.com/docs/eloquent#mass-assignment), [Rate Limiting](https://laravel.com/docs/rate-limiting)
- [Configuration: Debug Mode](https://laravel.com/docs/configuration#debug-mode)
- OWASP: [Laravel Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Laravel_Cheat_Sheet.html), [PHP Configuration Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/PHP_Configuration_Cheat_Sheet.html)
- [Composer 2.9 release](https://blog.packagist.com/composer-2-9/) (automatic security blocking)
- Paragon IE: [Using Encryption and Authentication Correctly](https://paragonie.com/blog/2015/05/using-encryption-and-authentication-correctly) (bài cũ nhưng giải thích rất rõ vì sao encrypt phải kèm authenticate)
- Laravel:

**2.9 Chống lạm dụng: rate limit, brute force, bot**

- OWASP: [Credential Stuffing Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Credential_Stuffing_Prevention_Cheat_Sheet.html), [Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html) (mục account lockout và error messages)
- OWASP API Top 10: [API6:2023 Unrestricted Access to Sensitive Business Flows](https://owasp.org/API-Security/editions/2023/en/0xa6-unrestricted-access-to-sensitive-business-flows/)
- Laravel: [Rate Limiting](https://laravel.com/docs/rate-limiting)

**3.1 OAuth nâng cao: token gắn người giữ, PAR, SSO**

- [RFC 9449: DPoP](https://www.rfc-editor.org/rfc/rfc9449): mục 1 (vấn đề), 4 (DPoP proof), 7 (resource server kiểm tra gì)
- [RFC 8705: OAuth 2.0 Mutual-TLS](https://www.rfc-editor.org/rfc/rfc8705): mục 3 (certificate-bound token)
- [RFC 9126: PAR](https://www.rfc-editor.org/rfc/rfc9126)
- RFC 9700: [mục 2.2 Token Replay Prevention](https://www.rfc-editor.org/rfc/rfc9700#section-2.2)
- [OWASP SAML Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SAML_Security_Cheat_Sheet.html)

**3.2 Multi-tenant isolation**

- Postgres: [Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- Laravel: [Global Scopes](https://laravel.com/docs/eloquent#global-scopes)
- AWS: [SaaS Tenant Isolation Strategies](https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/saas-tenant-isolation-strategies.html) (whitepaper): silo, pool, bridge

**3.3 Crypto ứng dụng và quản lý key**

- AWS KMS: [Envelope encryption](https://docs.aws.amazon.com/kms/latest/developerguide/kms-cryptography.html#enveloping)
- OWASP: [Key Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html)
- [Google Tink](https://developers.google.com/tink): xem cách một thư viện cấp cao thiết kế API để khó dùng sai
- [CipherSweet](https://ciphersweet.paragonie.com/) (Paragon IE): blind index cho PHP, đọc phần giải thích thiết kế
- *Serious Cryptography*: ch.4 (block cipher modes), ch.8 (authenticated encryption)

**3.4 Secret và supply chain**

- OWASP: [Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [OWASP Top 10:2025 A03 Software Supply Chain Failures](https://owasp.org/Top10/2025/A03_2025-Software_Supply_Chain_Failures/)
- [SLSA](https://slsa.dev/): trang "About" và các level
- [CycloneDX](https://cyclonedx.org/), [Sigstore](https://www.sigstore.dev/)
- [gitleaks](https://github.com/gitleaks/gitleaks), GitHub: [Secret scanning](https://docs.github.com/en/code-security/secret-scanning/introduction/about-secret-scanning)

**3.5 Dữ liệu cá nhân và pháp lý**

- OWASP: [Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) (mục data to exclude)
- [Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15](https://chinhphu.vn/?pageid=27160&docid=214590&classid=1&typegroupid=3): lướt mục lục, đọc chương về quyền của chủ thể dữ liệu
- [GDPR: Art. 17 Right to erasure](https://gdpr-info.eu/art-17-gdpr/) và [Art. 33 Notification of breach](https://gdpr-info.eu/art-33-gdpr/)

**3.6 Nguyên tắc, threat modeling, phát hiện**

- [Threat Modeling Manifesto](https://www.threatmodelingmanifesto.org/)
- OWASP: [Threat Modeling Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html)
- Microsoft: [Threat Modeling Tool threats (STRIDE)](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats)
- [OWASP Top 10:2025 A10 Mishandling of Exceptional Conditions](https://owasp.org/Top10/2025/A10_2025-Mishandling_of_Exceptional_Conditions/)
- *Threat Modeling: Designing for Security* (Adam Shostack; Wiley 2014): phần I

</details>

<details>
<summary><strong>12. Messaging, event-driven, background job</strong> (19 module, 106 link)</summary>

Học chi tiết: [12-messaging.md](12-messaging.md)

**1.1 Vì sao cần queue, các mô hình cơ bản**

- EIP: [Point-to-Point Channel](https://www.enterpriseintegrationpatterns.com/patterns/messaging/PointToPointChannel.html), [Publish-Subscribe Channel](https://www.enterpriseintegrationpatterns.com/patterns/messaging/PublishSubscribeChannel.html), [Competing Consumers](https://www.enterpriseintegrationpatterns.com/patterns/messaging/CompetingConsumers.html)
- Martin Fowler: [What do you mean by "Event-Driven"?](https://martinfowler.com/articles/201701-event-driven.html)
- Kafka design: [Push vs. pull](https://kafka.apache.org/43/design/design/#push-vs-pull)

**1.2 Delivery semantics và idempotent consumer**

- microservices.io: [Idempotent Consumer](https://microservices.io/patterns/communication-style/idempotent-consumer.html)
- Kafka design: [Message Delivery Semantics](https://kafka.apache.org/43/design/design/#message-delivery-semantics)
- Stripe: [Designing robust and predictable APIs with idempotency](https://stripe.com/blog/idempotency)
- DDIA ch.11: *Fault tolerance*, và ch.12: *The end-to-end argument for databases*

**1.3 Ack, retry, DLQ, poison message**

- EIP: [Dead Letter Channel](https://www.enterpriseintegrationpatterns.com/patterns/messaging/DeadLetterChannel.html)
- AWS: [Exponential Backoff And Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)

**1.4 Laravel Queue cơ bản**

- Laravel: [Queues](https://laravel.com/docs/queues) phần *Introduction*, *Creating Jobs*, *Dispatching Jobs*, [Jobs & Database Transactions](https://laravel.com/docs/queues#jobs-and-database-transactions), [Supervisor Configuration](https://laravel.com/docs/queues#supervisor-configuration), [Dealing With Failed Jobs](https://laravel.com/docs/queues#dealing-with-failed-jobs)

**2.1 Kafka: mô hình, partition, producer**

- Kafka 4.3: [Introduction](https://kafka.apache.org/43/getting-started/introduction/), Design: [The Producer](https://kafka.apache.org/43/design/design/#the-producer), [Availability and Durability Guarantees](https://kafka.apache.org/43/design/design/#availability-and-durability-guarantees)
- [Producer configs](https://kafka.apache.org/43/configuration/producer-configs/): đọc `acks`, `enable.idempotence`, `linger.ms`, `delivery.timeout.ms`
- *Kafka: The Definitive Guide*: ch.3 (producer), ch.7 (reliable data delivery)
- Jay Kreps: *The Log: What every software engineer should know about real-time data's unifying abstraction* (LinkedIn Engineering, 2013; bản sách mở rộng *I Heart Logs*, O'Reilly 2014): bài gốc giải thích vì sao lại là log

**2.2 Kafka: consumer, offset, rebalance**

- Kafka design: [Consumer Position](https://kafka.apache.org/43/design/design/#consumer-position), [Static Membership](https://kafka.apache.org/43/design/design/#static-membership), [Log Compaction](https://kafka.apache.org/43/design/design/#log-compaction)
- [Consumer configs](https://kafka.apache.org/43/configuration/consumer-configs/): `enable.auto.commit`, `auto.offset.reset`, `max.poll.interval.ms`, `max.poll.records`, `group.protocol`
- Confluent: [Kafka Consumer Design](https://docs.confluent.io/kafka/design/consumer-design.html)
- *Kafka: The Definitive Guide*: ch.4 (consumer)

**2.3 RabbitMQ**

- RabbitMQ: [Tutorials](https://www.rabbitmq.com/tutorials) 1–5 (nếu chưa dùng bao giờ), [Exchanges](https://www.rabbitmq.com/docs/exchanges), [Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms), [Consumer Prefetch](https://www.rabbitmq.com/docs/consumer-prefetch), [Delivery Acknowledgement Timeout](https://www.rabbitmq.com/docs/consumers#acknowledgement-timeout)
- [Dead Letter Exchanges](https://www.rabbitmq.com/docs/dlx), [TTL](https://www.rabbitmq.com/docs/ttl), [Quorum Queues](https://www.rabbitmq.com/docs/quorum-queues) (mục poison message handling), [Reliability Guide](https://www.rabbitmq.com/docs/reliability)
- [RabbitMQ 4.3 highlights](https://www.rabbitmq.com/blog/2026/04/23/rabbitmq-4.3-release)

**2.4 SQS và SNS**

- SQS: [Visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html), [FIFO queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-fifo-queues.html), [Fair queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-fair-queues.html), [Dead-letter queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html), [Message quotas](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html), [Short and long polling](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-short-and-long-polling.html)
- [SQS tăng payload lên 1 MiB](https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-sqs-max-payload-size-1mib) (thông báo 08/2025)
- SNS: [Fanout to SQS](https://docs.aws.amazon.com/sns/latest/dg/sns-sqs-as-subscriber.html), [Message filtering](https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html)
- Lambda: [Handling errors for an SQS event source](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html) (partial batch response)

**2.5 Redis, NATS, database làm queue, và chọn broker**

- Redis: [Streams](https://redis.io/docs/latest/develop/data-types/streams/), [BLMOVE: pattern reliable queue](https://redis.io/docs/latest/commands/blmove/)
- NATS: [JetStream](https://docs.nats.io/nats-concepts/jetstream)
- Brandur: [Postgres Job Queues & Failure By MVCC](https://brandur.org/postgres-queues)
- DB queue bằng `SKIP LOCKED`: module 2.6 của [03-database-sql.md](03-database-sql.md)

**2.6 Transactional outbox và inbox**

- microservices.io: [Transactional outbox](https://microservices.io/patterns/data/transactional-outbox.html), [Polling publisher](https://microservices.io/patterns/data/polling-publisher.html), [Transaction log tailing](https://microservices.io/patterns/data/transaction-log-tailing.html)
- Debezium: [Outbox Event Router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html)
- DDIA ch.11: *Change Data Capture*

**2.7 Ordering, backpressure, kích thước, schema**

- EIP: [Claim Check](https://www.enterpriseintegrationpatterns.com/patterns/messaging/StoreInLibrary.html)
- Confluent: [Schema Evolution and Compatibility](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html)
- [CloudEvents spec](https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md): tham khảo cách chuẩn hoá envelope
- RabbitMQ: [Memory and Disk Alarms](https://www.rabbitmq.com/docs/alarms)

**2.8 Tầng PHP: Laravel Queue sâu và consumer chạy lâu**

- [Job Expirations and Timeouts](https://laravel.com/docs/queues#job-expirations-and-timeouts) (`retry_after` và `--timeout`)
- [Max Job Attempts and Timeout](https://laravel.com/docs/queues#max-job-attempts-and-timeout)
- [Unique Jobs](https://laravel.com/docs/queues#unique-jobs), [Debounced Jobs](https://laravel.com/docs/queues#debounced-jobs), [Preventing Job Overlaps](https://laravel.com/docs/queues#preventing-job-overlaps)
- [Job Chaining](https://laravel.com/docs/queues#job-chaining), [Job Batching](https://laravel.com/docs/queues#job-batching)
- [Encrypted Jobs](https://laravel.com/docs/queues#encrypted-jobs), [SQS Overflow Storage](https://laravel.com/docs/queues#sqs-overflow-storage), [Queue Failover](https://laravel.com/docs/queues#queue-failover)
- [Resource Considerations](https://laravel.com/docs/queues#resource-considerations), [Processing a Specified Number of Jobs](https://laravel.com/docs/queues#processing-a-specified-number-of-jobs), [Queue Workers and Deployment](https://laravel.com/docs/queues#queue-workers-and-deployment)
- Laravel: [Horizon](https://laravel.com/docs/horizon) (balancing strategies, deploying)
- [librdkafka CONFIGURATION.md](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md): tên cấu hình dùng trong php-rdkafka
- Laravel Queues:
- Runtime PHP-FPM và CLI: [05-php-laravel.md](05-php-laravel.md)

**2.9 Cron và scheduler nhiều instance**

- Laravel: [Preventing Task Overlaps](https://laravel.com/docs/scheduling#preventing-task-overlaps), [Running Tasks on One Server](https://laravel.com/docs/scheduling#running-tasks-on-one-server), [Background Tasks](https://laravel.com/docs/scheduling#background-tasks)
- Kubernetes: [CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) (mục job creation và limitations)

**3.1 Kafka bên trong: replication, lưu trữ, vì sao nhanh**

- Kafka design: [Persistence](https://kafka.apache.org/43/design/design/#persistence), [Efficiency](https://kafka.apache.org/43/design/design/#efficiency), [Replication](https://kafka.apache.org/43/design/design/#replication), [Unclean leader election](https://kafka.apache.org/43/design/design/#unclean-leader-election-what-if-they-all-die)
- Kafka 4.3: [Implementation: Log](https://kafka.apache.org/43/implementation/log/), [KRaft](https://kafka.apache.org/43/operations/kraft/), [Tiered Storage](https://kafka.apache.org/43/operations/tiered-storage/), [ZooKeeper to KRaft migration](https://kafka.apache.org/43/getting-started/zk2kraft/)
- *Kafka: The Definitive Guide*: ch.6 (Kafka internals)

**3.2 Kafka exactly-once, transaction và zombie fencing**

- Kafka design: [Using Transactions](https://kafka.apache.org/43/design/design/#using-transactions), [Transaction protocol](https://kafka.apache.org/43/operations/transaction-protocol/)
- Confluent: [Transactions in Apache Kafka](https://www.confluent.io/blog/transactions-apache-kafka/) (mục zombie fencing), [Exactly-once Semantics are Possible](https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/)
- [KIP-447: Producer scalability for exactly once semantics](https://cwiki.apache.org/confluence/display/KAFKA/KIP-447%3A+Producer+scalability+for+exactly+once+semantics)

**3.3 Kafka 4.x: consumer group protocol mới và share groups**

- Kafka 4.3: [Consumer Rebalance Protocol](https://kafka.apache.org/43/operations/consumer-rebalance-protocol/), Design: [The Share Consumer](https://kafka.apache.org/43/design/design/#the-share-consumer), [Upgrading](https://kafka.apache.org/43/getting-started/upgrade/)
- [KIP-848](https://cwiki.apache.org/confluence/display/KAFKA/KIP-848%3A+The+Next+Generation+of+the+Consumer+Rebalance+Protocol), [KIP-932](https://cwiki.apache.org/confluence/display/KAFKA/KIP-932%3A+Queues+for+Kafka): đọc phần Motivation
- Release notes: [Kafka 4.0](https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/), [Kafka 4.2](https://kafka.apache.org/blog/2026/02/17/apache-kafka-4.2.0-release-announcement/)

**3.4 Vận hành Kafka**

- Kafka 4.3: [Monitoring](https://kafka.apache.org/43/operations/monitoring/), Design: [Quotas](https://kafka.apache.org/43/design/design/#quotas), [Basic Kafka Operations](https://kafka.apache.org/43/operations/basic-kafka-operations/)
- *Kafka: The Definitive Guide*: ch.12–13 (administering, monitoring)

**3.5 Pattern event-driven: CDC, choreography, CQRS, event sourcing**

- Debezium: [Tutorial](https://debezium.io/documentation/reference/stable/tutorial.html), [MySQL connector](https://debezium.io/documentation/reference/stable/connectors/mysql.html) (phần snapshot)
- Martin Fowler: [CQRS](https://martinfowler.com/bliki/CQRS.html), [Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)
- microservices.io: [Saga](https://microservices.io/patterns/data/saga.html), [Event sourcing](https://microservices.io/patterns/data/event-sourcing.html)
- DDIA ch.11: *Databases and Streams*, *Event Sourcing*

**3.6 Job dài, batch, stream, workflow engine**

- Temporal: [Workflows](https://docs.temporal.io/workflows) (mục deterministic constraints), [PHP SDK](https://docs.temporal.io/develop/php)
- Laravel: [Job Batching](https://laravel.com/docs/queues#job-batching) cho job dài chia nhỏ
- DDIA ch.10 (batch) và ch.11 (stream): phần *Reasoning About Time*

</details>

### Hệ thống quy mô lớn

<details>
<summary><strong>13. Concurrency</strong> (16 module, 50 link)</summary>

Học chi tiết: [13-concurrency.md](13-concurrency.md)

**1.1 Concurrency, race condition, critical section**

- OSTEP: [Concurrency: An Introduction](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-intro.pdf)
- Go blog: [Concurrency is not parallelism](https://go.dev/blog/waza-talk) (video Rob Pike)

**1.2 Primitive đồng bộ cơ bản**

- OSTEP: [Locks](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-locks.pdf), [Condition Variables](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-cv.pdf), [Semaphores](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-sema.pdf)
- Go: [x/sync/semaphore](https://pkg.go.dev/golang.org/x/sync/semaphore)
- *Java Concurrency in Practice*: ch.5 (building blocks) và ch.14 (condition queue)

**1.3 Deadlock, livelock, starvation**

- OSTEP: [Common Concurrency Problems](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-bugs.pdf)
- MySQL: [Deadlocks in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks.html); module 2.6 và 3.2 của [03-database-sql.md](03-database-sql.md)
- Laravel: [Handling Deadlocks](https://laravel.com/docs/database#handling-deadlocks) (`DB::transaction($fn, $attempts)`)

**1.4 Race condition trong ứng dụng web**

- Laravel: [Pessimistic Locking](https://laravel.com/docs/queries#pessimistic-locking)
- DDIA ch.7: *Preventing Lost Updates* và *Write Skew and Phantoms*
- Module 2.6 của [03-database-sql.md](03-database-sql.md)

**2.1 Atomic, CAS và optimistic lock**

- Go: [sync/atomic](https://pkg.go.dev/sync/atomic)
- *Java Concurrency in Practice*: ch.15 (atomic variables và nonblocking synchronization)

**2.2 Lost update và isolation level**

- Postgres: [Repeatable Read Isolation Level](https://www.postgresql.org/docs/current/transaction-iso.html#XACT-REPEATABLE-READ)
- [Hermitage](https://github.com/ept/hermitage): kịch bản tái hiện lost update ở từng DB
- Module 2.5 của [03-database-sql.md](03-database-sql.md) (isolation và anomaly, bảng so sánh MySQL/Postgres)

**2.3 Double submit, idempotency key**

- [Brandur: Implementing Stripe-like Idempotency Keys in Postgres](https://brandur.org/idempotency-keys)
- Stripe: [Idempotent requests](https://docs.stripe.com/api/idempotent_requests)
- [09-api-design.md](09-api-design.md), [12-messaging.md](12-messaging.md)

**2.4 Thread pool, connection pool, Little's law**

- [HikariCP: About Pool Sizing](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing): vì sao pool nhỏ thường nhanh hơn
- [Little's law](https://en.wikipedia.org/wiki/Little%27s_law)
- *Java Concurrency in Practice*: ch.8 (*Sizing Thread Pools*)

**2.5 Pattern concurrency trong Go (và đối chiếu Java)**

- Go blog: [Pipelines and cancellation](https://go.dev/blog/pipelines), [Share Memory By Communicating](https://go.dev/blog/codelab-share), [Fixing For Loops in Go 1.22](https://go.dev/blog/loopvar-preview)
- Go: [errgroup](https://pkg.go.dev/golang.org/x/sync/errgroup), [WaitGroup.Go](https://pkg.go.dev/sync#WaitGroup.Go), [Go 1.25 release notes](https://go.dev/doc/go1.25)

**2.6 Mô hình chạy: process, thread, event loop, goroutine, virtual thread**

- JEP: [444 Virtual Threads](https://openjdk.org/jeps/444), [491 Synchronize Virtual Threads without Pinning](https://openjdk.org/jeps/491), [506 Scoped Values](https://openjdk.org/jeps/506)
- Node.js: [Don't Block the Event Loop](https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop)
- [What Color is Your Function?](https://journal.stuffwithstuff.com/2015/02/01/what-color-is-your-function/) (Bob Nystrom)

**2.7 Tầng PHP: FPM, Laravel, Octane, async**

- [Atomic Locks](https://laravel.com/docs/cache#atomic-locks)
- [Pessimistic Locking](https://laravel.com/docs/queries#pessimistic-locking)
- [Unique Jobs](https://laravel.com/docs/queues#unique-jobs), [Preventing Job Overlaps](https://laravel.com/docs/queues#preventing-job-overlaps), [Jobs & Database Transactions](https://laravel.com/docs/queues#jobs-and-database-transactions)
- [Octane](https://laravel.com/docs/octane) (mục dependency injection và memory leak), [Concurrency](https://laravel.com/docs/concurrency)
- PHP: [Fibers](https://www.php.net/manual/en/language.fibers.php), [session_write_close](https://www.php.net/manual/en/function.session-write-close.php), [flock](https://www.php.net/manual/en/function.flock.php)
- [ReactPHP](https://reactphp.org/), [OpenSwoole](https://openswoole.com/)
- Laravel:
- Runtime PHP chi tiết: [05-php-laravel.md](05-php-laravel.md)

**3.1 Memory model**

- [The Go Memory Model](https://go.dev/ref/mem)
- [JLS §17.4 Memory Model](https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html)
- Aleksey Shipilëv: [Java Memory Model Pragmatics](https://shipilev.net/blog/2014/jmm-pragmatics/) (dài, đọc phần đầu tới happens-before)
- *Java Concurrency in Practice*: ch.3 (visibility) và ch.16

**3.2 Lock-free, ABA, spinlock**

- *Java Concurrency in Practice*: ch.15
- *The Art of Multiprocessor Programming* (Herlihy, Shavit): nếu muốn đi sâu

**3.3 Priority inversion, bulkhead, actor model**

- [What really happened on Mars?](https://www.cs.cornell.edu/courses/cs614/1999sp/papers/pathfinder.html) (Glenn Reeves)
- Microsoft: [Bulkhead pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead)

**3.4 Tranh chấp cực cao: flash sale, hot row**

- Redis: [SET](https://redis.io/docs/latest/commands/set/) (`NX`, `PX`)
- [16-system-design.md](16-system-design.md) bài flash sale

**3.5 Kiểm thử và điều tra lỗi concurrency**

- Go: [Data Race Detector](https://go.dev/doc/articles/race_detector), [testing/synctest](https://pkg.go.dev/testing/synctest), blog [Testing concurrent code with testing/synctest](https://go.dev/blog/synctest)
- [jcstress](https://github.com/openjdk/jcstress): README và thư mục samples

</details>

<details>
<summary><strong>14. Hệ phân tán</strong> (18 module, 62 link)</summary>

Học chi tiết: [14-distributed-systems.md](14-distributed-systems.md)

**1.1 Bản chất: partial failure và "không biết request có thành công không"**

- [Fallacies of distributed computing](https://en.wikipedia.org/wiki/Fallacies_of_distributed_computing)
- Aphyr, Bailis: [The Network is Reliable](https://aphyr.com/posts/288-the-network-is-reliable) (tổng hợp sự cố mạng thật)
- DDIA ch.8: *Faults and Partial Failures*, *Unreliable Networks*

**1.2 Timeout, retry, backoff, jitter, idempotency**

- Amazon Builders' Library: [Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/), [Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)
- AWS Architecture Blog: [Exponential Backoff And Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/) (có biểu đồ so sánh các kiểu jitter)

**1.3 CAP và PACELC**

- Kleppmann: [Please stop calling databases CP or AP](https://martin.kleppmann.com/2015/05/11/please-stop-calling-databases-cp-or-ap.html)
- DDIA ch.9: *Linearizability* (mục *The Cost of Linearizability* nói về CAP)

**1.4 Replication cơ bản và replication lag**

- DDIA ch.5: *Leaders and Followers*, *Problems with Replication Lag*
- Module 3.4 của [03-database-sql.md](03-database-sql.md) (replication MySQL, read-your-writes với Laravel)

**2.1 Consistency model, linearizability và serializability**

- Peter Bailis: [Linearizability versus Serializability](https://www.bailis.org/blog/linearizability-versus-serializability/) (ngắn, đọc đầu tiên)
- Jepsen: [Consistency Models](https://jepsen.io/consistency), [Linearizable](https://jepsen.io/consistency/models/linearizable), [Serializable](https://jepsen.io/consistency/models/serializable)
- Aphyr: [Strong consistency models](https://aphyr.com/posts/313-strong-consistency-models)
- DDIA ch.9: *Linearizability* (có mục so sánh với serializability)

**2.2 Ba kiểu replication và quorum**

- [Dynamo paper](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf) (SOSP 2007): mục 4 (consistent hashing, vector clock, sloppy quorum)
- [Amazon DynamoDB paper](https://www.usenix.org/conference/atc22/presentation/elhemali) (USENIX ATC 2022): mục về replication bằng Multi-Paxos, để thấy DynamoDB khác Dynamo thế nào
- Cassandra: [Dynamo architecture](https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html)
- DDIA ch.5: *Multi-Leader Replication*, *Leaderless Replication*

**2.3 Partitioning, consistent hashing, rebalancing**

- Redis: [Cluster specification](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/) (phần hash slot)
- DDIA ch.6 (cả chương)
- Module 3.6 của [03-database-sql.md](03-database-sql.md) (sharding MySQL)

**2.4 Distributed transaction: 2PC, saga, outbox, TCC**

- [microservices.io: Saga](https://microservices.io/patterns/data/saga.html), [Transactional outbox](https://microservices.io/patterns/data/transactional-outbox.html)
- Microsoft: [Saga pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/saga)
- [Temporal docs: Workflows](https://docs.temporal.io/workflows)
- DDIA ch.9: *Distributed Transactions and Consensus* (2PC, XA)

**2.5 Distributed lock**

- Kleppmann: [How to do distributed locking](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html); antirez: [Is Redlock safe?](http://antirez.com/news/101). Đọc cả hai
- Redis: [Distributed Locks with Redis](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/)
- ZooKeeper: [Recipes](https://zookeeper.apache.org/doc/current/recipes.html) (mục Locks)
- DDIA ch.8: *The Truth Is Defined by the Majority* (fencing token)

**2.6 Resilience: circuit breaker, bulkhead, rate limit, load shedding**

- Martin Fowler: [CircuitBreaker](https://martinfowler.com/bliki/CircuitBreaker.html); Microsoft: [Circuit Breaker pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker), [Bulkhead pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead)
- Amazon Builders' Library: [Using load shedding to avoid overload](https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload/), [Avoiding fallback in distributed systems](https://aws.amazon.com/builders-library/avoiding-fallback-in-distributed-systems/)
- Google SRE: [Handling Overload](https://sre.google/sre-book/handling-overload/), [Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/)

**2.7 Sinh ID phân tán**

- [RFC 9562](https://www.rfc-editor.org/rfc/rfc9562): mục 5.7 (UUIDv7)
- [Twitter Snowflake](https://github.com/twitter-archive/snowflake) (README bản gốc)
- [Meituan Leaf](https://tech.meituan.com/2017/04/21/mt-leaf.html) (tiếng Trung, xem hình kiến trúc segment và snowflake)

**2.8 Service discovery, health check, graceful shutdown**

- Kubernetes: [Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/)
- [19-devops-cloud.md](19-devops-cloud.md), [18-reliability-observability.md](18-reliability-observability.md)

**3.1 Consensus và Raft**

- [Raft paper](https://raft.github.io/raft.pdf) (đọc hết), mô phỏng ở [raft.github.io](https://raft.github.io/) và [The Secret Lives of Data](https://thesecretlivesofdata.com/raft/)
- [Luận án Ongaro](https://github.com/ongardie/dissertation) mục 9.6 (pre-vote) và ch.4 (thay đổi thành viên cluster)
- [FLP paper](https://groups.csail.mit.edu/tds/papers/Lynch/jacm85.pdf) (đọc phần giới thiệu là đủ)
- Lamport: [Paxos Made Simple](https://lamport.azurewebsites.net/pubs/paxos-simple.pdf) (tuỳ chọn)
- [etcd docs](https://etcd.io/docs/), Jepsen: [etcd 3.4.3](https://jepsen.io/analyses/etcd-3.4.3)
- DDIA ch.9: *Fault-Tolerant Consensus*

**3.2 Thời gian và thứ tự sự kiện**

- Lamport: [Time, Clocks, and the Ordering of Events](https://lamport.azurewebsites.net/pubs/time-clocks.pdf) (paper kinh điển, ngắn)
- CockroachDB: [Living without atomic clocks](https://www.cockroachlabs.com/blog/living-without-atomic-clocks/)
- Google Cloud: [TrueTime and external consistency](https://cloud.google.com/spanner/docs/true-time-external-consistency)
- DDIA ch.8: *Unreliable Clocks*

**3.3 Transaction xuyên shard**

- [Percolator paper](https://research.google/pubs/large-scale-incremental-processing-using-distributed-transactions-and-notifications/) (OSDI 2010), TiKV: [Percolator](https://tikv.org/deep-dive/distributed-transaction/percolator/) (giải thích dễ hơn paper)
- [Spanner paper](https://research.google/pubs/spanner-googles-globally-distributed-database-2/) (OSDI 2012): mục 4 (concurrency control)
- CockroachDB: [Transaction Layer](https://www.cockroachlabs.com/docs/stable/architecture/transaction-layer), [Parallel Commits](https://www.cockroachlabs.com/blog/parallel-commits/)

**3.4 Conflict resolution**

- [crdt.tech](https://crdt.tech/): danh sách paper và bài giới thiệu
- DDIA ch.5: *Handling Write Conflicts*, *Detecting Concurrent Writes*

**3.5 Failure mode nâng cao**

- Dean, Barroso: [The Tail at Scale](https://research.google/pubs/the-tail-at-scale/)
- [Metastable Failures in Distributed Systems](https://sigops.org/s/conferences/hotos/2021/papers/hotos21-s11-bronson.pdf) (HotOS 2021, ngắn)
- Amazon Builders' Library: [Workload isolation using shuffle-sharding](https://aws.amazon.com/builders-library/workload-isolation-using-shuffle-sharding/)
- Postmortem thật: [AWS S3 us-east-1 2017](https://aws.amazon.com/message/41926/) (khởi động lại subsystem mất hàng giờ), [GitHub Oct 21 2018](https://github.blog/news-insights/company-news/oct21-post-incident-analysis/) (network partition, failover MySQL giữa hai DC)

**3.6 Membership, leader election, exactly-once**

- Amazon Builders' Library: [Leader election in distributed systems](https://aws.amazon.com/builders-library/leader-election-in-distributed-systems/)
- Kubernetes: [Leases](https://kubernetes.io/docs/concepts/architecture/leases/)
- [SWIM paper](https://www.cs.cornell.edu/projects/Quicksilver/public_pdfs/SWIM.pdf); HashiCorp: [Consul gossip](https://developer.hashicorp.com/consul/docs/architecture/gossip)
- [End-to-End Arguments in System Design](https://web.mit.edu/Saltzer/www/publications/endtoend/endtoend.pdf)
- Confluent: [Exactly-once Semantics Are Possible](https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/)

</details>

<details>
<summary><strong>15. Kiến trúc phần mềm</strong> (12 module, 53 link)</summary>

Học chi tiết: [15-architecture.md](15-architecture.md)

**1.1 Layered, MVC và nơi đặt logic nghiệp vụ**

- Martin Fowler: [PresentationDomainDataLayering](https://martinfowler.com/bliki/PresentationDomainDataLayering.html)
- [lorisleiva/laravel-actions](https://github.com/lorisleiva/laravel-actions): README, để thấy một cách tổ chức use case trong Laravel
- *Fundamentals of Software Architecture*: chương *Layered Architecture Style*

**1.2 Monolith, 12-factor và app stateless**

- [The Twelve-Factor App](https://12factor.net/): đọc hết, ngắn
- Laravel: [Octane](https://laravel.com/docs/octane) (mục *Dependency Injection and Octane*, *Managing Memory Leaks*)
- Martin Fowler: [MonolithFirst](https://martinfowler.com/bliki/MonolithFirst.html)

**1.3 Configuration và feature flag**

- Martin Fowler (Pete Hodgson): [Feature Toggles](https://martinfowler.com/articles/feature-toggles.html): đọc hết, có phân loại flag
- Laravel: [Configuration](https://laravel.com/docs/configuration) (mục *Configuration Caching*), [Pennant](https://laravel.com/docs/pennant)

**2.1 Hexagonal, Clean, Onion, vertical slice**

- Alistair Cockburn: [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/) (bài gốc)
- Robert C. Martin: [The Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- Jeffrey Palermo: [The Onion Architecture, part 1](https://jeffreypalermo.com/2008/07/the-onion-architecture-part-1/)
- Jimmy Bogard: [Vertical Slice Architecture](https://www.jimmybogard.com/vertical-slice-architecture/)

**2.2 DDD tactical và DDD trong Laravel**

- Vaughn Vernon: [Effective Aggregate Design](https://www.dddcommunity.org/library/vernon_2011/) (3 phần, PDF)
- Martin Fowler: [DDD Aggregate](https://martinfowler.com/bliki/DDD_Aggregate.html), [Value Object](https://martinfowler.com/bliki/ValueObject.html)
- Laravel: [Custom Casts](https://laravel.com/docs/eloquent-mutators#custom-casts), [Dispatching Events After Transactions](https://laravel.com/docs/events#dispatching-events-after-database-transactions)
- [spatie/laravel-event-sourcing](https://spatie.be/docs/laravel-event-sourcing): phần *Using aggregates*, để thấy aggregate trong một package PHP thật
- *Learning Domain-Driven Design*: phần II (tactical), đặc biệt chương về aggregate và domain event

**2.3 Modular monolith**

- Shopify Engineering: [Deconstructing the Monolith](https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity), [Under Deconstruction: The State of Shopify's Monolith](https://shopify.engineering/shopify-monolith)
- [Deptrac](https://deptrac.github.io/deptrac/): phần layers, rulesets
- [InterNACHI/modular](https://github.com/InterNACHI/modular): README (cách tổ chức module bằng package Composer trong Laravel)
- Đối chiếu: [Spring Modulith](https://docs.spring.io/spring-modulith/reference/)

**2.4 Microservices và giao tiếp giữa service**

- Martin Fowler: [Microservices](https://martinfowler.com/articles/microservices.html), [MicroservicePrerequisites](https://martinfowler.com/bliki/MicroservicePrerequisites.html)
- microservices.io: [Database per service](https://microservices.io/patterns/data/database-per-service.html)
- Istio: [Ambient mode overview](https://istio.io/latest/docs/ambient/overview/), [Ambient reaches GA](https://istio.io/latest/blog/2024/ambient-reaches-ga/)
- Case study ngược chiều: Segment: [Goodbye Microservices](https://segment.com/blog/goodbye-microservices/)
- *Building Microservices*: chương về communication styles và workflow (orchestration/choreography)

**2.5 Multi-tenancy**

- AWS: [SaaS Architecture Fundamentals](https://docs.aws.amazon.com/whitepapers/latest/saas-architecture-fundamentals/saas-architecture-fundamentals.html), [Silo, pool, and bridge models](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/silo-pool-and-bridge-models.html)
- Postgres: [Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- Laravel: [Global Scopes](https://laravel.com/docs/eloquent#global-scopes); [spatie/laravel-multitenancy](https://spatie.be/docs/laravel-multitenancy), [Tenancy for Laravel](https://tenancyforlaravel.com/docs/v3/)
- AWS Builders' Library: [Workload isolation using shuffle-sharding](https://aws.amazon.com/builders-library/workload-isolation-using-shuffle-sharding/) (noisy neighbor ở quy mô lớn)

**3.1 DDD strategic: tìm ranh giới**

- Martin Fowler: [BoundedContext](https://martinfowler.com/bliki/BoundedContext.html)
- DDD Crew: [Context Mapping](https://github.com/ddd-crew/context-mapping) (có cheat sheet các kiểu quan hệ), [DDD Starter Modelling Process](https://github.com/ddd-crew/ddd-starter-modelling-process)
- [EventStorming](https://www.eventstorming.com/)
- *Learning Domain-Driven Design*: phần I (strategic design)
- *Domain-Driven Design* (Evans): phần IV, chương *Maintaining Model Integrity*

**3.2 Tách service, strangler fig và dữ liệu xuyên service**

- Martin Fowler: [StranglerFigApplication](https://martinfowler.com/bliki/StranglerFigApplication.html), [CQRS](https://martinfowler.com/bliki/CQRS.html)
- microservices.io: [API Composition](https://microservices.io/patterns/data/api-composition.html), [Saga](https://microservices.io/patterns/data/saga.html)
- *Monolith to Microservices*: ch.3 (tách chức năng, strangler fig, branch by abstraction) và ch.4 (tách database)

**3.3 Tài liệu kiến trúc và ra quyết định**

- Michael Nygard: [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions); [adr.github.io](https://adr.github.io/) (các mẫu ADR)
- [C4 model](https://c4model.com/): phần *Diagrams* (system context, container)
- Amazon: [2016 Letter to Shareholders](https://www.aboutamazon.com/news/company-news/2016-letter-to-shareholders) (đoạn two-way door và ra quyết định với 70% thông tin)
- Thoughtworks: [Fitness function-driven development](https://www.thoughtworks.com/insights/articles/fitness-function-driven-development)
- *Fundamentals of Software Architecture*: phần về architecture characteristics và ADR

**3.4 Tổ chức: Conway's law và Team Topologies**

- Melvin Conway: [How Do Committees Invent?](https://www.melconway.com/Home/Committees_Paper.html) (1968, bài gốc, đọc cả ghi chú của tác giả ở đầu)
- [Jargon File: Conway's Law](http://www.catb.org/jargon/html/C/Conways-Law.html) (nguồn của câu "4-pass compiler")
- Martin Fowler: [Conway's Law](https://martinfowler.com/bliki/ConwaysLaw.html)
- [Team Topologies: Key Concepts](https://teamtopologies.com/key-concepts); sách *Team Topologies* (Skelton, Pais; 2019)

</details>

<details>
<summary><strong>16. System design</strong> (19 module, 53 link)</summary>

Học chi tiết: [16-system-design.md](16-system-design.md)

**1.1 Phương pháp làm bài 45–60 phút**

- Alex Xu vol 1, ch.3 *A Framework for System Design Interviews* ([bản online](https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews))
- [Hello Interview: System Design in a Hurry](https://www.hellointerview.com/learn/system-design/in-a-hurry/introduction): góc nhìn của người chấm

**1.2 Ước lượng back-of-envelope**

- Alex Xu vol 1, ch.2 *Back-of-the-envelope Estimation* ([bản online](https://bytebytego.com/courses/system-design-interview/back-of-the-envelope-estimation))
- [Latency Numbers Every Programmer Should Know (interactive)](https://colin-scott.github.io/personal_website/research/interactive_latency.html): con số theo năm
- PHP: [FPM configuration](https://www.php.net/manual/en/install.fpm.configuration.php) (`pm`, `pm.max_children`)
- Little's law: module 2.4 của [13-concurrency.md](13-concurrency.md)

**1.3 Building blocks và scale từ một server**

- Alex Xu vol 1, ch.1 *Scale from Zero to Millions of Users* ([bản online](https://bytebytego.com/courses/system-design-interview/scale-from-zero-to-millions-of-users))
- Laravel: [Session drivers](https://laravel.com/docs/session), [File Storage](https://laravel.com/docs/filesystem) (để app stateless)
- System Design Primer: các mục *Load balancer*, *Cache*, *Database*, *Asynchronism*

**1.4 Availability**

- Google SRE: [Embracing Risk](https://sre.google/sre-book/embracing-risk/), [Availability Table](https://sre.google/sre-book/availability-table/)
- Amazon Builders' Library: [Static stability using Availability Zones](https://aws.amazon.com/builders-library/static-stability-using-availability-zones/)
- [18-reliability-observability.md](18-reliability-observability.md) (SLO, RPO/RTO, DR)

**2.1 URL shortener**

- Alex Xu vol 1, ch.8 *Design a URL Shortener* ([bản online](https://bytebytego.com/courses/system-design-interview/design-a-url-shortener))

**2.2 Rate limiter**

- Alex Xu vol 1, ch.4 *Design a Rate Limiter* ([bản online](https://bytebytego.com/courses/system-design-interview/design-a-rate-limiter))
- Stripe: [Scaling your API with rate limiters](https://stripe.com/blog/rate-limiters); Cloudflare: [How we built rate limiting capable of scaling to millions of domains](https://blog.cloudflare.com/counting-things-a-lot-of-different-things/) (sliding window counter)
- IETF: [RateLimit header fields draft](https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/)
- Laravel: [Rate Limiting](https://laravel.com/docs/rate-limiting), [Route rate limiting](https://laravel.com/docs/routing#rate-limiting)

**2.3 Notification system**

- Laravel: [Notifications](https://laravel.com/docs/notifications) (mục queueing notifications)
- Alex Xu vol 1, ch.10 *Design a Notification System*

**2.4 News feed**

- Alex Xu vol 1, ch.11 *Design a News Feed System* ([bản online](https://bytebytego.com/courses/system-design-interview/design-a-news-feed-system))
- Facebook: [TAO: The power of the graph](https://engineering.fb.com/2013/06/25/core-infra/tao-the-power-of-the-graph/) (lưu và cache đồ thị xã hội)

**2.5 Chat / messenger**

- Alex Xu vol 1, ch.12 *Design a Chat System* ([bản online](https://bytebytego.com/courses/system-design-interview/design-a-chat-system))
- Discord: [How Discord Stores Trillions of Messages](https://discord.com/blog/how-discord-stores-trillions-of-messages) (Cassandra sang ScyllaDB, partition theo channel và bucket thời gian)
- Slack: [Real-time Messaging](https://slack.engineering/real-time-messaging/)
- Laravel: [Broadcasting](https://laravel.com/docs/broadcasting), [Reverb](https://laravel.com/docs/reverb)

**2.6 Đặt vé / đặt phòng**

- Alex Xu vol 2, ch.7 *Hotel Reservation System* ([bản online](https://bytebytego.com/courses/system-design-interview/hotel-reservation-system))
- Module 1.4 của [13-concurrency.md](13-concurrency.md), module 2.6 của [03-database-sql.md](03-database-sql.md)

**2.7 Leaderboard**

- Alex Xu vol 2, ch.10 *Real-time Gaming Leaderboard* ([bản online](https://bytebytego.com/courses/system-design-interview/real-time-gaming-leaderboard))
- Redis: [Sorted sets](https://redis.io/docs/latest/develop/data-types/sorted-sets/), [ZRANGE](https://redis.io/docs/latest/commands/zrange/)

**3.1 Thanh toán / ví điện tử**

- Stripe: [Designing robust and predictable APIs with idempotency](https://stripe.com/blog/idempotency)
- Modern Treasury: [Accounting for Developers, Part I](https://www.moderntreasury.com/journal/accounting-for-developers-part-i) (bút toán kép cho developer)
- [Brandur: Idempotency Keys](https://brandur.org/idempotency-keys)
- Alex Xu vol 2, ch.11 *Payment System* và ch.12 *Digital Wallet*

**3.2 Flash sale**

- Shopify: [Surviving Flashes of High-Write Traffic Using Scriptable Load Balancers](https://shopify.engineering/surviving-flashes-of-high-write-traffic-using-scriptable-load-balancers-part-i)
- Module 3.4 của [13-concurrency.md](13-concurrency.md)

**3.3 Distributed ID generator và key-value store**

- Alex Xu vol 1, ch.7 *Design a Unique ID Generator*, ch.5 *Consistent Hashing* ([bản online](https://bytebytego.com/courses/system-design-interview/design-consistent-hashing)), ch.6 *Design a Key-Value Store* ([bản online](https://bytebytego.com/courses/system-design-interview/design-a-key-value-store))
- [Dynamo paper](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf)
- DDIA ch.3 (LSM-tree)

**3.4 Web crawler và search autocomplete**

- Alex Xu vol 1, ch.9 *Design a Web Crawler* ([bản online](https://bytebytego.com/courses/system-design-interview/design-a-web-crawler)) và ch.13 *Design a Search Autocomplete System*

**3.5 File storage (Drive/Dropbox) và video streaming**

- Alex Xu vol 1, ch.15 *Design Google Drive* và ch.14 *Design YouTube* ([bản online](https://bytebytego.com/courses/system-design-interview/design-youtube))
- Dropbox: [Streaming File Synchronization](https://dropbox.tech/infrastructure/streaming-file-synchronization), [Rewriting the heart of our sync engine](https://dropbox.tech/infrastructure/rewriting-the-heart-of-our-sync-engine)
- AWS: [Uploading objects with presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedUrlUploadObject.html); Laravel: [Temporary Upload URLs](https://laravel.com/docs/filesystem#temporary-upload-urls)
- [RFC 8216](https://www.rfc-editor.org/rfc/rfc8216) (HLS): lướt mục 4 để biết manifest trông thế nào

**3.6 Ride-hailing / nearby search**

- [H3](https://h3geo.org/) (docs, mục introduction)
- Redis: [GEOSEARCH](https://redis.io/docs/latest/commands/geosearch/)
- Alex Xu vol 2, ch.1 *Proximity Service* và ch.2 *Nearby Friends*

**3.7 Distributed job scheduler**

- Laravel: [Running Tasks on One Server](https://laravel.com/docs/scheduling#running-tasks-on-one-server), [Preventing Task Overlaps](https://laravel.com/docs/scheduling#preventing-task-overlaps)
- Module 2.6 của [03-database-sql.md](03-database-sql.md) (`SKIP LOCKED`), module 3.6 của [14-distributed-systems.md](14-distributed-systems.md) (leader election)

**3.8 Metrics / logging system**

- Facebook: [Gorilla: A Fast, Scalable, In-Memory Time Series Database](https://www.vldb.org/pvldb/vol8/p1816-teller.pdf) (mục 4 về nén)
- Prometheus: [Overview](https://prometheus.io/docs/introduction/overview/), [Do not overuse labels](https://prometheus.io/docs/practices/instrumentation/#do-not-overuse-labels)
- Grafana: [Loki overview](https://grafana.com/docs/loki/latest/get-started/overview/), [Migrate from Promtail to Alloy](https://grafana.com/docs/alloy/latest/set-up/migrate/from-promtail/)
- Alex Xu vol 2, ch.5 *Metrics Monitoring and Alerting System*
- [18-reliability-observability.md](18-reliability-observability.md)

</details>

<details>
<summary><strong>17. Performance và scalability</strong> (15 module, 61 link)</summary>

Học chi tiết: [17-performance.md](17-performance.md)

**1.1 Latency, throughput, percentile**

- Brendan Gregg: [Latency heat maps](https://www.brendangregg.com/HeatMaps/latency.html) (vì sao phân phối quan trọng hơn một con số)
- DDIA ch.1: mục *Describing Performance*

**1.2 Quy trình tối ưu: đo trước, sửa sau**

- Brendan Gregg: [Performance Methodologies](https://www.brendangregg.com/methodology.html) (đọc phần anti-methodologies trước)
- [OpenTelemetry docs](https://opentelemetry.io/docs/): mục *Concepts* (trace, span, metric)
- Laravel: [Pulse](https://laravel.com/docs/pulse), [Telescope](https://laravel.com/docs/telescope)
- Observability chi tiết: [18-reliability-observability.md](18-reliability-observability.md)

**1.3 Nguyên nhân chậm thường gặp: DB và cache**

- Laravel: [Eager Loading](https://laravel.com/docs/eloquent-relationships#eager-loading), [Preventing Lazy Loading](https://laravel.com/docs/eloquent-relationships#preventing-lazy-loading)
- Use The Index, Luke: [Paging Through Results](https://use-the-index-luke.com/sql/partial-results/fetch-next-page)

**1.4 Scale cơ bản**

- Laravel: [Deployment](https://laravel.com/docs/deployment) (các bước optimize), [Running Tasks on One Server](https://laravel.com/docs/scheduling#running-tasks-on-one-server)
- System design tổng thể: [16-system-design.md](16-system-design.md)

**2.1 Little's law, Amdahl, queueing**

- Marc Brooker: [Little's Law](https://brooker.co.za/blog/2018/06/20/littles-law.html) (ngắn, có ví dụ hệ thống thật)
- Mor Harchol-Balter: [*Performance Modeling and Design of Computer Systems*](https://www.cs.cmu.edu/~harchol/PerformanceModeling/book.html), chương 6 (Little's law) và các chương M/M/1 nếu muốn đi sâu

**2.2 Profiling, flame graph, công cụ theo ngôn ngữ**

- Brendan Gregg: [Flame Graphs](https://www.brendangregg.com/flamegraphs.html), [Off-CPU Analysis](https://www.brendangregg.com/offcpuanalysis.html)
- Go: [Diagnostics](https://go.dev/doc/diagnostics), [net/http/pprof](https://pkg.go.dev/net/http/pprof)
- Java: [async-profiler](https://github.com/async-profiler/async-profiler) README, [JMH](https://github.com/openjdk/jmh)
- [Grafana Pyroscope](https://github.com/grafana/pyroscope) (continuous profiling mã nguồn mở)

**2.3 Tầng PHP: profiling, OPcache/JIT, tuning PHP-FPM**

- Profiler: [Xdebug Profiling](https://xdebug.org/docs/profiler), [SPX](https://github.com/NoiseByNorthwest/php-spx), [xhprof (PECL)](https://pecl.php.net/package/xhprof), [Blackfire docs](https://docs.blackfire.io/), [Tideways](https://tideways.com/)
- PHP: [OPcache configuration](https://www.php.net/manual/en/opcache.configuration.php) (mục [`opcache.jit`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.jit), [`memory_consumption`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.memory-consumption), [`validate_timestamps`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.validate-timestamps)), [Preloading](https://www.php.net/manual/en/opcache.preloading.php), [RFC: JIT](https://wiki.php.net/rfc/jit) (phần benchmark cho thấy khi nào có lợi)
- PHP-FPM: [configuration](https://www.php.net/manual/en/install.fpm.configuration.php), mục [`pm`](https://www.php.net/manual/en/install.fpm.configuration.php#pm), [`pm.max_children`](https://www.php.net/manual/en/install.fpm.configuration.php#pm.max-children), `pm.status_path`, `slowlog`
- Laravel: [Optimizing configuration loading](https://laravel.com/docs/deployment#optimizing-configuration-loading), [Concurrent Requests](https://laravel.com/docs/http-client#concurrent-requests), [Octane](https://laravel.com/docs/octane)
- [PHPBench](https://phpbench.readthedocs.io/)
- Runtime PHP chi tiết: [05-php-laravel.md](05-php-laravel.md); process model FPM ở mức OS: [01-os-linux.md](01-os-linux.md)

**2.4 Checklist tầng network, app code, serialization**

- Laravel: [Chunking Results](https://laravel.com/docs/eloquent#chunking-results), [Chunking Using Lazy Collections](https://laravel.com/docs/eloquent#chunking-using-lazy-collections)
- AWS Builders' Library: [Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)

**2.5 Connection pool**

- [HikariCP: About Pool Sizing](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing) (áp dụng được cho mọi DB, không chỉ Java)
- Tầng PHP và DB: module 2.7 của [03-database-sql.md](03-database-sql.md)

**2.6 Load testing**

- k6: [Load test types](https://grafana.com/docs/k6/latest/testing-guides/test-types/), [Thresholds](https://grafana.com/docs/k6/latest/using-k6/thresholds/), [Executors](https://grafana.com/docs/k6/latest/using-k6/scenarios/executors/)
- Gatling: [Create your first JavaScript-based simulation](https://docs.gatling.io/tutorials/test-as-code/javascript/running-your-first-simulation/)
- [wrk2](https://github.com/giltene/wrk2) README (đọc phần về constant throughput)

**3.1 Tail latency, fan-out, USL**

- [The Tail at Scale](https://research.google/pubs/the-tail-at-scale/): đọc hết
- Neil Gunther: [How to Quantify Scalability](http://www.perfdynamics.com/Manifesto/USLscalability.html)
- Marc Brooker: [Metastability and Distributed Systems](https://brooker.co.za/blog/2021/05/24/metastable.html)

**3.2 GC và lock contention**

- Go: [A Guide to the Go Garbage Collector](https://go.dev/doc/gc-guide)
- Cloudflare: [The story of one latency spike](https://blog.cloudflare.com/the-story-of-one-latency-spike/) (điều tra một đỉnh p99 tới tận kernel)
- MySQL lock: module 2.6 và 3.2 của [03-database-sql.md](03-database-sql.md)

**3.3 Load test không tự lừa mình: open/closed model, coordinated omission**

- k6: [Open and closed models](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/)
- Gil Tene: ["How NOT to Measure Latency"](https://www.youtube.com/watch?v=lJ8ydIuPFeU) (video, bài nói gốc về coordinated omission)
- [HdrHistogram](https://github.com/HdrHistogram/HdrHistogram) README

**3.4 Scale nâng cao: precompute và đánh đổi**

- PostgreSQL: [REFRESH MATERIALIZED VIEW](https://www.postgresql.org/docs/current/sql-refreshmaterializedview.html)
- DDIA ch.1 (ví dụ Twitter home timeline: fan-out lúc ghi hay lúc đọc) và ch.11 (derived data)

**3.5 Capacity planning, autoscaling, load shedding**

- Kubernetes: [Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/) (mục *stabilization window*, *scaling policies*), [KEDA](https://keda.sh/)
- Google SRE: [Handling Overload](https://sre.google/sre-book/handling-overload/), [Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/), Workbook [Managing Load](https://sre.google/workbook/managing-load/)
- AWS Builders' Library: [Using load shedding to avoid overload](https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload/)

</details>

### Vận hành và chất lượng

<details>
<summary><strong>18. Reliability và observability</strong> (18 module, 71 link)</summary>

Học chi tiết: [18-reliability-observability.md](18-reliability-observability.md)

**1.1 SLI, SLO, SLA**

- SRE book: [Service Level Objectives](https://sre.google/sre-book/service-level-objectives/), [Embracing Risk](https://sre.google/sre-book/embracing-risk/)
- SRE Workbook: [Implementing SLOs](https://sre.google/workbook/implementing-slos/) (phần chọn SLI và bảng SLI theo loại hệ thống)

**1.2 Redundancy và health check**

- [Amazon Builders' Library: Implementing health checks](https://aws.amazon.com/builders-library/implementing-health-checks/): đọc hết, có phần "fail open" khi mọi instance cùng báo hỏng
- Kubernetes: [Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- Laravel: [The Health Route](https://laravel.com/docs/deployment#the-health-route)

**1.3 Log có cấu trúc**

- Laravel: [Logging](https://laravel.com/docs/logging) (mục [Contextual Information](https://laravel.com/docs/logging#contextual-information)), [Context](https://laravel.com/docs/context)
- [Monolog](https://github.com/Seldaek/monolog): README, phần formatter và processor
- OpenTelemetry: [Logs](https://opentelemetry.io/docs/concepts/signals/logs/) (cách gắn trace id vào log)

**1.4 Quy trình sự cố cơ bản**

- SRE book: [Managing Incidents](https://sre.google/sre-book/managing-incidents/)
- [PagerDuty Incident Response](https://response.pagerduty.com/): phần *Before*, *During an Incident*

**2.1 Error budget**

- SRE Workbook: [Example Error Budget Policy](https://sre.google/workbook/error-budget-policy/)
- SRE book: [Embracing Risk](https://sre.google/sre-book/embracing-risk/) (phần *Motivation for Error Budgets*)

**2.2 Metric**

- Prometheus: [Metric types](https://prometheus.io/docs/concepts/metric_types/), [Histograms and summaries](https://prometheus.io/docs/practices/histograms/), [Metric and label naming](https://prometheus.io/docs/practices/naming/), [Instrumentation](https://prometheus.io/docs/practices/instrumentation/) (có mục cardinality)
- SRE book: [Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/) (four golden signals)
- Brendan Gregg: [The USE Method](https://www.brendangregg.com/usemethod.html)
- Grafana: [The RED Method](https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/)

**2.3 Tracing và OpenTelemetry**

- OpenTelemetry: [Traces](https://opentelemetry.io/docs/concepts/signals/traces/), [Context propagation](https://opentelemetry.io/docs/concepts/context-propagation/), [Collector](https://opentelemetry.io/docs/collector/), [Semantic conventions](https://opentelemetry.io/docs/specs/semconv/) (lướt)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/): phần định dạng header `traceparent`
- Grafana: [Exemplars](https://grafana.com/docs/grafana/latest/fundamentals/exemplars/)

**2.4 Alerting và on-call**

- SRE book: [Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/) (phần *Symptoms Versus Causes*), [Being On-Call](https://sre.google/sre-book/being-on-call/)
- SRE Workbook: [On-Call](https://sre.google/workbook/on-call/)
- Prometheus: [Alerting best practices](https://prometheus.io/docs/practices/alerting/), [Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/)
- Thông báo của vendor: [Grafana OnCall OSS maintenance mode](https://grafana.com/blog/grafana-oncall-maintenance-mode/), [Opsgenie migration](https://www.atlassian.com/software/opsgenie/migration)

**2.5 High availability và graceful degradation**

- SRE book: [Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/)
- Amazon Builders' Library: [Timeouts, retries and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/), [Using load shedding to avoid overload](https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload/)
- SRE Workbook: [Managing Load](https://sre.google/workbook/managing-load/)

**2.6 Backup, RPO và RTO**

- [AWS: Disaster Recovery of Workloads](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html): phần định nghĩa RPO/RTO
- MySQL PITR: xem module 3.5 của [03-database-sql.md](03-database-sql.md)

**2.7 Tầng PHP: quan sát PHP-FPM và Laravel**

- PHP: [FPM configuration](https://www.php.net/manual/en/install.fpm.configuration.php) (mục [pm.status_path](https://www.php.net/manual/en/install.fpm.configuration.php#pm.status-path), [ping.path](https://www.php.net/manual/en/install.fpm.configuration.php#ping.path), [request_slowlog_timeout](https://www.php.net/manual/en/install.fpm.configuration.php#request-slowlog-timeout))
- [php-fpm_exporter](https://github.com/hipages/php-fpm_exporter), [prometheus_client_php](https://github.com/PromPHP/prometheus_client_php) (phần storage adapter)
- OpenTelemetry: [PHP](https://opentelemetry.io/docs/languages/php/), [PHP zero-code instrumentation](https://opentelemetry.io/docs/zero-code/php/)
- Laravel: [Context](https://laravel.com/docs/context), [Pulse](https://laravel.com/docs/pulse), [Telescope](https://laravel.com/docs/telescope), [Horizon](https://laravel.com/docs/horizon)
- [Sentry for Laravel](https://docs.sentry.io/platforms/php/guides/laravel/)
- Runtime PHP-FPM: [05-php-laravel.md](05-php-laravel.md)

**2.8 Postmortem**

- SRE book: [Postmortem Culture](https://sre.google/sre-book/postmortem-culture/); SRE Workbook: [Postmortem Culture](https://sre.google/workbook/postmortem-culture/) (có ví dụ postmortem tốt và tồi)
- Atlassian: [Blameless postmortems](https://www.atlassian.com/incident-management/postmortem/blameless)
- [danluu/post-mortems](https://github.com/danluu/post-mortems): tuyển tập postmortem công khai, đọc 5–10 bài

**3.1 Burn rate alert**

- SRE Workbook: [Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/): **đọc hết**, đi qua 6 cách alert từ tồi tới tốt

**3.2 Chi phí và sampling của observability**

- OpenTelemetry: [Sampling](https://opentelemetry.io/docs/concepts/sampling/)
- Grafana Loki: [Label best practices](https://grafana.com/docs/loki/latest/get-started/labels/bp-labels/)
- *Observability Engineering*: các chương về structured event và sampling

**3.3 Disaster recovery và DR drill**

- [AWS: Disaster Recovery options in the cloud](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html): đọc hết, có hình từng mức

**3.4 Điều phối sự cố lớn**

- [PagerDuty Incident Response](https://response.pagerduty.com/): phần vai trò (*Incident Commander*, *Scribe*...) và *Being an Incident Commander*
- SRE Workbook: [Incident Response](https://sre.google/workbook/incident-response/)
- [Atlassian Incident Management Handbook](https://www.atlassian.com/incident-management/handbook)
- [incident.io guide](https://incident.io/guide)

**3.5 Resilience testing**

- [Principles of Chaos Engineering](https://principlesofchaos.org/)
- [Toxiproxy](https://github.com/Shopify/toxiproxy): README, thử với Redis/MySQL local
- [AWS Fault Injection Service](https://aws.amazon.com/fis/)

**3.6 Công cụ và kiến trúc observability stack**

- OpenTelemetry: [Collector](https://opentelemetry.io/docs/collector/) (phần deployment pattern: agent và gateway)
- Prometheus: [Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Grafana Cloud IRM](https://grafana.com/docs/grafana-cloud/alerting-and-irm/irm/)

</details>

<details>
<summary><strong>19. DevOps và Cloud</strong> (20 module, 111 link)</summary>

Học chi tiết: [19-devops-cloud.md](19-devops-cloud.md)

**1.1 Container và Docker cơ bản**

- Docker: [Building best practices](https://docs.docker.com/build/building/best-practices/), [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/), [Build cache](https://docs.docker.com/build/cache/)
- [distroless](https://github.com/GoogleContainerTools/distroless): README, phần chọn image
- Linux nền: [01-os-linux.md](01-os-linux.md) (namespace, cgroup)

**1.2 Dockerfile an toàn và chạy đúng**

- Docker: [Dockerfile reference](https://docs.docker.com/reference/dockerfile/) (mục [shell and exec form](https://docs.docker.com/reference/dockerfile/#shell-and-exec-form), [ENTRYPOINT](https://docs.docker.com/reference/dockerfile/#entrypoint), [HEALTHCHECK](https://docs.docker.com/reference/dockerfile/#healthcheck), [USER](https://docs.docker.com/reference/dockerfile/#user)), [Build secrets](https://docs.docker.com/build/building/secrets/), [Control startup order](https://docs.docker.com/compose/how-tos/startup-order/)
- Docker: [Engine security](https://docs.docker.com/engine/security/)

**1.3 CI/CD và chiến lược deploy**

- Martin Fowler: [BlueGreenDeployment](https://martinfowler.com/bliki/BlueGreenDeployment.html), [CanaryRelease](https://martinfowler.com/bliki/CanaryRelease.html), [Feature Toggles](https://martinfowler.com/articles/feature-toggles.html) (bài dài, đọc phần phân loại toggle)
- SRE Workbook: [Canarying Releases](https://sre.google/workbook/canarying-releases/)

**1.4 Môi trường, config, 12-factor**

- [The Twelve-Factor App](https://12factor.net/): đọc hết
- Laravel: [Deployment](https://laravel.com/docs/deployment) (phần [Optimization](https://laravel.com/docs/deployment#optimization))

**2.1 Workload trên Kubernetes**

- Kubernetes: [Pods](https://kubernetes.io/docs/concepts/workloads/pods/), [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/), [Sidecar Containers](https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/), [Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/), [CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) (mục [Time zones](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/#time-zones))
- [Debug Running Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/), [kubectl Quick Reference](https://kubernetes.io/docs/reference/kubectl/quick-reference/)
- [Helm docs](https://helm.sh/docs/), [Kustomize](https://kubectl.docs.kubernetes.io/)

**2.2 Service, Ingress, Gateway API**

- Kubernetes: [Service](https://kubernetes.io/docs/concepts/services-networking/service/), [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/), [Gateway API](https://kubernetes.io/docs/concepts/services-networking/gateway/)
- [Gateway API docs](https://gateway-api.sigs.k8s.io/): phần *Concepts*, [Migrating from Ingress](https://gateway-api.sigs.k8s.io/guides/getting-started/migrating-from-ingress/), [Implementations](https://gateway-api.sigs.k8s.io/implementations/)
- Kubernetes blog: [Ingress NGINX Retirement](https://kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/), [Statement from Steering and Security Response Committees](https://kubernetes.io/blog/2026/01/29/ingress-nginx-statement/)
- [ingress2gateway](https://github.com/kubernetes-sigs/ingress2gateway)

**2.3 ConfigMap và Secret**

- Kubernetes: [ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/), [Secrets](https://kubernetes.io/docs/concepts/configuration/secret/), [Good practices for Secrets](https://kubernetes.io/docs/concepts/security/secrets-good-practices/), [Encrypting data at rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)
- [External Secrets Operator](https://external-secrets.io/), [Secrets Store CSI Driver](https://secrets-store-csi-driver.sigs.k8s.io/)
- AWS: [EKS Pod Identity](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html)

**2.4 Probes**

- Kubernetes: [Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- Phần health check trong [18-reliability-observability.md](18-reliability-observability.md) (module 1.2)

**2.5 Resource, QoS và autoscaling**

- Kubernetes: [Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/), [Pod Quality of Service Classes](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/), [Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- Go blog: [Container-aware GOMAXPROCS](https://go.dev/blog/container-aware-gomaxprocs)
- [KEDA](https://keda.sh/), [Karpenter](https://karpenter.sh/)

**2.6 Rolling update và graceful shutdown**

- Kubernetes: [Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/) (mục [Termination of Pods](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination)), [Container Lifecycle Hooks](https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/) (mục [Hook handler implementations](https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/#hook-handler-implementations)), [Rolling Update Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-update-deployment)
- learnk8s: [Graceful shutdown in Kubernetes](https://learnk8s.io/graceful-shutdown): **đọc hết**, có hình dòng thời gian

**2.7 Tầng PHP: PHP-FPM, queue và runtime trong container**

- Docker Hub: [php official image](https://hub.docker.com/_/php) (phần *How to install more PHP extensions*, *Configuration*); [Dockerfile php-fpm](https://github.com/docker-library/php/blob/master/8.4/bookworm/fpm/Dockerfile) (xem dòng `STOPSIGNAL`)
- PHP: [OPcache configuration](https://www.php.net/manual/en/opcache.configuration.php) (mục [validate_timestamps](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.validate-timestamps)), [FPM configuration](https://www.php.net/manual/en/install.fpm.configuration.php) (mục [ping.path](https://www.php.net/manual/en/install.fpm.configuration.php#ping.path), [process_control_timeout](https://www.php.net/manual/en/install.fpm.configuration.php#process-control-timeout))
- [php-fpm-healthcheck](https://github.com/renatomefi/php-fpm-healthcheck)
- Laravel: [Queue workers and deployment](https://laravel.com/docs/queues#queue-workers-and-deployment), [Worker timeouts](https://laravel.com/docs/queues#worker-timeouts), [Supervisor configuration](https://laravel.com/docs/queues#supervisor-configuration), [Octane](https://laravel.com/docs/octane) (mục [Managing memory leaks](https://laravel.com/docs/octane#managing-memory-leaks)), [Scheduling](https://laravel.com/docs/scheduling)
- [FrankenPHP docs](https://frankenphp.dev/docs/) (mục [worker mode](https://frankenphp.dev/docs/worker/)), [RoadRunner docs](https://docs.roadrunner.dev/)
- Runtime PHP-FPM chi tiết: [05-php-laravel.md](05-php-laravel.md)

**2.8 CI nâng cao: cache, secret, quality gate**

- GitHub: [OpenID Connect](https://docs.github.com/en/actions/concepts/security/openid-connect), [Configuring OIDC in AWS](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws), [Security hardening for GitHub Actions](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions)

**2.9 Terraform và Ansible**

- Terraform: [State](https://developer.hashicorp.com/terraform/language/state), [State locking](https://developer.hashicorp.com/terraform/language/state/locking), [S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3) (mục [State Locking](https://developer.hashicorp.com/terraform/language/backend/s3#state-locking))
- [Ansible: Getting started](https://docs.ansible.com/ansible/latest/getting_started/index.html)
- *Terraform: Up & Running*, 3rd ed. (Yevgeniy Brikman, O'Reilly): chương về state và module

**3.1 Bảo mật Kubernetes**

- Kubernetes: [Security Context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/), [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/), [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/), [Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/), [RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/), [RBAC good practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/) (mục privilege escalation), [Service Accounts](https://kubernetes.io/docs/concepts/security/service-accounts/)
- [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets), [SOPS](https://github.com/getsops/sops)

**3.2 PodDisruptionBudget, StatefulSet, scheduling**

- Kubernetes: [Disruptions](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/), [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/), [Topology Spread Constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/)

**3.3 Migration khi deploy và rollback dữ liệu**

- Martin Fowler: [ParallelChange](https://martinfowler.com/bliki/ParallelChange.html)
- Module 3.3 của [03-database-sql.md](03-database-sql.md)

**3.4 GitOps và supply chain**

- [OpenGitOps principles](https://opengitops.dev/), [Argo CD docs](https://argo-cd.readthedocs.io/en/stable/) (phần *Core Concepts*)
- [Trivy](https://trivy.dev/), [Sigstore cosign](https://docs.sigstore.dev/cosign/signing/overview/)

**3.5 Dịch vụ cloud (AWS làm ví dụ)**

- AWS: [IAM best practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html), [RDS Multi-AZ](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.html), [SQS visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html), [S3 consistency](https://aws.amazon.com/s3/consistency/), [Restricting access to S3 origin](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)
- AWS Well-Architected: trụ cột *Reliability* và *Security*

**3.6 Serverless trade-off**

- AWS Lambda: [Quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html), [Concurrency](https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html)
- AWS: [RDS Proxy](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-proxy.html)

**3.7 Cost awareness**

- AWS: [Cost Explorer](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html), [Gateway endpoints for S3](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-s3.html)
- [FinOps Framework](https://www.finops.org/framework/): lướt phần *Principles*

</details>

<details>
<summary><strong>20. Testing và chất lượng code</strong> (14 module, 72 link)</summary>

Học chi tiết: [20-testing-quality.md](20-testing-quality.md)

**1.1 Các loại test và chiến lược**

- Martin Fowler: [The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html) (đọc hết)
- Kent C. Dodds: [The Testing Trophy and Testing Classifications](https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications)
- *Software Engineering at Google*: [ch.11 Testing Overview](https://abseil.io/resources/swe-book/html/ch11.html) (phần test size và test scope)

**1.2 Viết test tốt**

- Martin Fowler: [Test Double](https://martinfowler.com/bliki/TestDouble.html), [Mocks Aren't Stubs](https://martinfowler.com/articles/mocksArentStubs.html) (classical so với mockist)
- *Software Engineering at Google*: [ch.12 Unit Testing](https://abseil.io/resources/swe-book/html/ch12.html) (test qua public API, test hành vi), [ch.13 Test Doubles](https://abseil.io/resources/swe-book/html/ch13.html) (ưu tiên real > fake > stub/mock)

**1.3 Git cơ bản**

- Pro Git: [Git Branching: Rebasing](https://git-scm.com/book/en/v2/Git-Branching-Rebasing) (đặc biệt mục *The Perils of Rebasing*)
- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)

**1.4 Code review và PR**

- [Google Engineering Practices: Code Review](https://google.github.io/eng-practices/review/) (cả hai phần: người review và người viết)
- *Software Engineering at Google*: [ch.9 Code Review](https://abseil.io/resources/swe-book/html/ch09.html)

**2.1 Test isolation, DB và flaky test**

- Martin Fowler: [Eradicating Non-Determinism in Tests](https://martinfowler.com/articles/nonDeterminism.html)
- Google Testing Blog: [Flaky Tests at Google and How We Mitigate Them](https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html)
- [Testcontainers](https://testcontainers.com/) (khái niệm), [Testcontainers for PHP](https://php.testcontainers.org/)
- Laravel: [Resetting the Database After Each Test](https://laravel.com/docs/database-testing#resetting-the-database-after-each-test), [The .env.testing file](https://laravel.com/docs/testing#the-env-testing-environment-file), [Parallel Testing and Databases](https://laravel.com/docs/testing#parallel-testing-and-databases)

**2.2 Test những thứ khó**

- PHP-FIG: [PSR-20 Clock](https://www.php-fig.org/psr/psr-20/)
- Laravel: [Mocking: Interacting With Time](https://laravel.com/docs/mocking#interacting-with-time), [HTTP Client: Testing](https://laravel.com/docs/http-client#testing) (mục [Preventing Stray Requests](https://laravel.com/docs/http-client#preventing-stray-requests)), [Queues: Testing](https://laravel.com/docs/queues#testing)

**2.3 Testing trong PHP và Laravel**

- PHPUnit: [Manual](https://docs.phpunit.de/) (các chương *Writing Tests*, *Test Doubles*, *Attributes*), [Supported Versions](https://phpunit.de/supported-versions.html)
- Pest: [Installation](https://pestphp.com/docs/installation), [Browser Testing](https://pestphp.com/docs/browser-testing), [Pest v4 announcement](https://pestphp.com/docs/pest-v4-is-here-now-with-browser-testing)
- [Mockery docs](https://docs.mockery.io/en/latest/)
- Laravel: [HTTP Tests](https://laravel.com/docs/http-tests), [Database Testing](https://laravel.com/docs/database-testing), [Mocking](https://laravel.com/docs/mocking) (mục [Mocking Facades](https://laravel.com/docs/mocking#mocking-facades)), [Running Tests in Parallel](https://laravel.com/docs/testing#running-tests-in-parallel), [Events: Testing](https://laravel.com/docs/events#testing), [Dusk](https://laravel.com/docs/dusk)
- Góc runtime PHP/Laravel: [05-php-laravel.md](05-php-laravel.md)

**2.4 Contract testing**

- [Pact docs: How Pact works](https://docs.pact.io/getting_started/how_pact_works), [pact-php](https://github.com/pact-foundation/pact-php) (README, ví dụ consumer/provider)
- Martin Fowler: [Contract Test](https://martinfowler.com/bliki/ContractTest.html); phần *Contract Tests* trong [The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)

**2.5 Static analysis, linter và CI**

- PHPStan: [Rule Levels](https://phpstan.org/user-guide/rule-levels), [Baseline](https://phpstan.org/user-guide/baseline); [Larastan](https://github.com/larastan/larastan)
- [Rector documentation](https://getrector.com/documentation); Laravel: [Pint](https://laravel.com/docs/pint) (mục [Continuous Integration](https://laravel.com/docs/pint#continuous-integration))
- GitHub: [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)

**2.6 Git nâng cao và quy trình nhóm**

- Git: [git-bisect](https://git-scm.com/docs/git-bisect), [git-reflog](https://git-scm.com/docs/git-reflog), [git-rerere](https://git-scm.com/docs/git-rerere)
- [Trunk Based Development](https://trunkbaseddevelopment.com/); [A successful Git branching model](https://nvie.com/posts/a-successful-git-branching-model/) (bài gốc Git flow, đọc cả ghi chú 2020 của tác giả ở đầu bài); Martin Fowler: [Patterns for Managing Source Code Branches](https://martinfowler.com/articles/branching-patterns.html)
- Martin Fowler: [Feature Toggles](https://martinfowler.com/articles/feature-toggles.html); Laravel: [Pennant](https://laravel.com/docs/pennant)
- [The Scrum Guide](https://scrumguides.org/scrum-guide.html)

**3.1 TDD, BDD và chọn phương pháp**

- *Software Engineering at Google*: [ch.14 Larger Testing](https://abseil.io/resources/swe-book/html/ch14.html)
- [Cucumber docs](https://cucumber.io/docs/), [Behat docs](https://docs.behat.org/en/latest/)

**3.2 Đo chất lượng test: coverage, mutation, property-based**

- Martin Fowler: [Test Coverage](https://martinfowler.com/bliki/TestCoverage.html)
- [Infection guide](https://infection.github.io/guide/) (phần *Mutators* và *Metrics*: MSI, covered MSI); [Pest mutation testing](https://pestphp.com/docs/mutation-testing); [PIT](https://pitest.org/)
- [Eris](https://github.com/giorgiosironi/eris), [jqwik](https://jqwik.net/), [Go fuzzing](https://go.dev/doc/security/fuzz/)

**3.3 Test concurrency**

- [Go Data Race Detector](https://go.dev/doc/articles/race_detector)
- Laravel: [Processes: Concurrent Processes](https://laravel.com/docs/processes#concurrent-processes)

**3.4 Legacy code, tech debt và documentation**

- *Working Effectively with Legacy Code*: chương về seam và characterization test; Michael Feathers: [Characterization Testing](https://michaelfeathers.silvrback.com/characterization-testing)
- Martin Fowler: [Technical Debt Quadrant](https://martinfowler.com/bliki/TechnicalDebtQuadrant.html), [Strangler Fig Application](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [ADR GitHub organization](https://adr.github.io/) (mẫu ADR)

</details>

### Làm việc cùng AI

<details>
<summary><strong>26. Dùng AI trong công việc và coding</strong> (14 module, 47 link)</summary>

Học chi tiết: [26-ai-assisted-engineering.md](26-ai-assisted-engineering.md)

**1.1 AI coding tool hoạt động thế nào (ở mức người dùng cần biết)**

- [Stack Overflow Developer Survey 2025: AI](https://survey.stackoverflow.co/2025/ai): phần trust và frustrations
- [Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172) (Liu và cộng sự, 2023): chỉ cần đọc abstract và hình 1
- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents): phần đầu, về việc context là tài nguyên có hạn

**1.2 Các loại công cụ và khi nào dùng loại nào**

- [Claude Code: Overview](https://code.claude.com/docs/en/overview): để hiểu một coding agent làm được những gì
- [GitHub Copilot docs](https://docs.github.com/en/copilot) và [About Copilot coding agent](https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent): ví dụ về agent chạy nền, mở PR
- [Claude Code: Security](https://code.claude.com/docs/en/security): permission và sandbox của một coding agent

**1.3 Giao việc cho AI: prompt và context**

- [Claude Code: Best practices](https://www.anthropic.com/engineering/claude-code-best-practices): các phần về viết chỉ dẫn cụ thể và yêu cầu lập kế hoạch trước
- [Anthropic: Prompt engineering overview](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview): nguyên tắc chung, áp dụng cho mọi model
- [Simon Willison: Here's how I use LLMs to help me write code](https://simonwillison.net/2025/Mar/11/using-llms-for-code/): phần "context is king" và "tell them exactly what to do"

**1.4 Kiểm chứng output: bạn là người chịu trách nhiệm**

- [Socket: The Rise of Slopsquatting](https://socket.dev/blog/slopsquatting-how-ai-hallucinations-are-fueling-a-new-class-of-supply-chain-attacks)
- [Simon Willison: Here's how I use LLMs to help me write code](https://simonwillison.net/2025/Mar/11/using-llms-for-code/): phần "you have to test what it writes"
- Bảo mật dependency nói chung: [10-security.md](10-security.md) (phần supply chain)

**2.1 Quy trình làm việc với coding agent**

- [Claude Code: Best practices](https://www.anthropic.com/engineering/claude-code-best-practices): phần "explore, plan, code, commit" và "write tests, commit; code, iterate, commit"
- [Claude Code: Common workflows](https://code.claude.com/docs/en/common-workflows): hiểu codebase, sửa bug, refactor, làm việc với test
- [Simon Willison: Vibe engineering](https://simonwillison.net/2025/Oct/7/vibe-engineering/): khác biệt giữa "vibe coding" và dùng agent có kỷ luật kỹ thuật

**2.2 Context engineering: file hướng dẫn, MCP, quản lý context**

- [Claude Code: How Claude remembers your project](https://code.claude.com/docs/en/memory): file `CLAUDE.md` và cách tổ chức
- [AGENTS.md](https://agents.md/): định dạng chung cho nhiều công cụ
- [GitHub: Adding repository custom instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions) và [Cursor: Rules](https://cursor.com/docs/context/rules)
- [Model Context Protocol](https://modelcontextprotocol.io/) và [Claude Code: MCP](https://code.claude.com/docs/en/mcp)
- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

**2.3 Dùng AI cho từng loại việc backend**

- [How Anthropic teams use Claude Code](https://www.anthropic.com/news/how-anthropic-teams-use-claude-code): ví dụ thật từ nhiều loại team
- [Addy Osmani: The 70% problem](https://addyo.substack.com/p/the-70-problem-hard-truths-about): vì sao AI làm nhanh 70% đầu nhưng 30% cuối vẫn cần kinh nghiệm
- Bối cảnh cho từng việc: [03-database-sql.md](03-database-sql.md) (EXPLAIN), [20-testing-quality.md](20-testing-quality.md) (test), [13-concurrency.md](13-concurrency.md)

**2.4 Review code do AI viết**

- [Martin Fowler: Exploring Generative AI](https://martinfowler.com/articles/exploring-gen-ai.html): các bài về chất lượng code và rủi ro
- [DORA AI Capabilities Model](https://services.google.com/fh/files/misc/2025_dora_ai_capabilities_model.pdf): phần về version control và small batches
- Quy trình review và static analysis: [20-testing-quality.md](20-testing-quality.md)

**2.5 Bảo mật, dữ liệu và tuân thủ**

- [Simon Willison: The lethal trifecta for AI agents](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/)
- [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/): mục prompt injection và excessive agency
- [Claude Code: Security](https://code.claude.com/docs/en/security) và [Claude Code: Settings](https://code.claude.com/docs/en/settings) (permission, chặn đọc file)
- Prompt injection từ góc nhìn sản phẩm: [23-ai-llm-backend.md](23-ai-llm-backend.md), module 3.1

**2.6 Tầng PHP/Laravel: công cụ riêng và lưới an toàn**

- [Laravel Boost](https://laravel.com/docs/boost) và [repo laravel/boost](https://github.com/laravel/boost)
- [Infection](https://github.com/infection/infection): mutation testing cho PHP
- Công cụ chất lượng: [20-testing-quality.md](20-testing-quality.md) và [05-php-laravel.md](05-php-laravel.md) (module về PHPStan, Rector, Pint)

**3.1 Đo hiệu quả thật**

- [METR: Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/) và [bản cập nhật 02/2026](https://metr.org/blog/2026-02-24-uplift-update/)
- [Google Cloud: Announcing the 2025 DORA report](https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report) và [DORA AI Capabilities Model (PDF)](https://services.google.com/fh/files/misc/2025_dora_ai_capabilities_model.pdf)
- Các chỉ số DORA: [24-senior-leadership.md](24-senior-leadership.md)

**3.2 Đưa AI vào team**

- [DORA AI Capabilities Model (PDF)](https://services.google.com/fh/files/misc/2025_dora_ai_capabilities_model.pdf): phần "clear and communicated AI stance"
- [How Anthropic teams use Claude Code](https://www.anthropic.com/news/how-anthropic-teams-use-claude-code)
- Mentor và dẫn dắt team nói chung: [24-senior-leadership.md](24-senior-leadership.md)

**3.3 Workflow agent nâng cao và guardrail**

- [Claude Code: Hooks reference](https://code.claude.com/docs/en/hooks) và [Create custom subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code: Common workflows](https://code.claude.com/docs/en/common-workflows): phần chạy song song bằng git worktree
- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents): các mẫu workflow và khi nào nên dùng agent
- [Agent Skills](https://agentskills.io/home): định dạng skill dùng chung giữa nhiều công cụ

**3.4 Giữ kỹ năng nền và quan điểm nghề nghiệp**

- [Addy Osmani: The 70% problem](https://addyo.substack.com/p/the-70-problem-hard-truths-about)
- [Simon Willison: Vibe engineering](https://simonwillison.net/2025/Oct/7/vibe-engineering/)
- [Martin Fowler: Exploring Generative AI](https://martinfowler.com/articles/exploring-gen-ai.html)

</details>

<details>
<summary><strong>23. Tích hợp AI/LLM vào backend</strong> (18 module, 81 link)</summary>

Học chi tiết: [23-ai-llm-backend.md](23-ai-llm-backend.md)

**1.1 LLM là một dependency ngoài**

- Anthropic: [Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows), [Extended thinking](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) (phần tính tiền thinking token), [Token counting](https://platform.claude.com/docs/en/build-with-claude/token-counting)
- OpenAI: [Reasoning models](https://developers.openai.com/api/docs/guides/reasoning) (phần reasoning token và quản lý chi phí), [Conversation state](https://developers.openai.com/api/docs/guides/conversation-state)

**1.2 Gọi API: timeout, retry, stop reason**

- Anthropic: [Errors](https://platform.claude.com/docs/en/api/errors), [Rate limits](https://platform.claude.com/docs/en/api/rate-limits), [Stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)
- OpenAI: [Error codes](https://developers.openai.com/api/docs/guides/error-codes), [Rate limits](https://developers.openai.com/api/docs/guides/rate-limits)
- Retry và backoff chung: [Amazon Builders' Library: Timeouts, retries and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)

**1.3 Structured output và tool use**

- Anthropic: [Tool use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview), [Implement tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use), [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- OpenAI: [Function calling](https://developers.openai.com/api/docs/guides/function-calling), [Structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- Anthropic: [Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)

**1.4 Không tin output LLM**

- OWASP: [Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/): đọc LLM05 (Improper Output Handling) và LLM06 (Excessive Agency)

**2.1 Streaming**

- Anthropic: [Streaming Messages](https://platform.claude.com/docs/en/build-with-claude/streaming) (các loại event, lỗi giữa stream)
- OpenAI: [Streaming API responses](https://developers.openai.com/api/docs/guides/streaming-responses)
- MDN: [Using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
- Nginx: [`proxy_buffering`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_buffering), [`proxy_read_timeout`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_read_timeout)

**2.2 Tầng PHP: gọi LLM từ PHP-FPM và Laravel**

- Anthropic: [PHP SDK](https://platform.claude.com/docs/en/api/sdks/php) (phần streaming, retries, error handling), [anthropic-sdk-php](https://github.com/anthropics/anthropic-sdk-php)
- OpenAI: [Libraries](https://developers.openai.com/api/docs/libraries) (danh sách SDK chính thức và thư viện cộng đồng); [openai-php/client](https://github.com/openai-php/client)
- Laravel: [AI SDK](https://laravel.com/docs/ai-sdk), [HTTP Client](https://laravel.com/docs/http-client) (mục [Timeout](https://laravel.com/docs/http-client#timeout), [Retries](https://laravel.com/docs/http-client#retries)), [Event Streams](https://laravel.com/docs/responses#event-streams), [Queues](https://laravel.com/docs/queues) (mục [Worker timeouts](https://laravel.com/docs/queues#worker-timeouts))
- Guzzle: [Request options](https://docs.guzzlephp.org/en/stable/request-options.html) (mục [stream](https://docs.guzzlephp.org/en/stable/request-options.html#stream), [read_timeout](https://docs.guzzlephp.org/en/stable/request-options.html#read-timeout)); Symfony: [HttpClient streaming responses](https://symfony.com/doc/current/http_client.html#streaming-responses)
- Nginx: [`fastcgi_buffering`](https://nginx.org/en/docs/http/ngx_http_fastcgi_module.html#fastcgi_buffering) (có ghi chú về header `X-Accel-Buffering`), [`fastcgi_read_timeout`](https://nginx.org/en/docs/http/ngx_http_fastcgi_module.html#fastcgi_read_timeout)
- PHP: [Connection handling](https://www.php.net/manual/en/features.connection-handling.php), [`connection_aborted`](https://www.php.net/manual/en/function.connection-aborted.php), [`flush`](https://www.php.net/manual/en/function.flush.php)

**2.3 Chi phí và caching**

- Anthropic: [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) (ngưỡng tối thiểu, breakpoint, TTL, cách đọc usage), [Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)
- OpenAI: [Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching), [Batch API](https://developers.openai.com/api/docs/guides/batch)

**2.4 Chọn model, fallback và LLM gateway**

- [LiteLLM docs](https://docs.litellm.ai/): phần proxy (routing, fallback, budget) để thấy một gateway làm những gì
- Anthropic: [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) (pattern *routing*)

**2.5 RAG: luồng, chunking, embedding, vector store**

- Bài gốc: [Lewis et al., Retrieval-Augmented Generation](https://arxiv.org/abs/2005.11401) (đọc abstract và phần 2)
- Anthropic: [Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval): kỹ thuật thêm ngữ cảnh vào chunk, có số đo trước/sau
- [pgvector](https://github.com/pgvector/pgvector): README, phần HNSW, IVFFlat, filtering
- Laravel AI SDK: [AI SDK](https://laravel.com/docs/ai-sdk) (phần embedding)

**2.6 Hybrid search, rerank và cập nhật index**

- [Cormack et al., Reciprocal Rank Fusion](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf) (bài ngắn, 2 trang)
- Elasticsearch: [Reciprocal rank fusion](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion)
- Anthropic: [Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) (phần kết hợp BM25 và rerank)

**2.7 Agent và workflow**

- Anthropic: [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents): **đọc hết**
- OWASP: LLM06 Excessive Agency và LLM10 Unbounded Consumption trong [Top 10](https://genai.owasp.org/llm-top-10/)

**2.8 Model Context Protocol (MCP)**

- [MCP: Introduction](https://modelcontextprotocol.io/docs/getting-started/intro), [Architecture](https://modelcontextprotocol.io/docs/learn/architecture), [Specification](https://modelcontextprotocol.io/specification/latest) (lướt phần *Base Protocol* và *Transports*)
- MCP: [Security Best Practices](https://modelcontextprotocol.io/specification/latest/basic/security_best_practices): **đọc hết**
- PHP: [Announcing the Official PHP SDK for MCP](https://thephp.foundation/blog/2025/09/05/php-mcp-sdk/), [modelcontextprotocol/php-sdk](https://github.com/modelcontextprotocol/php-sdk); Laravel: [MCP](https://laravel.com/docs/mcp)
- Anthropic: [MCP connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector) (gọi MCP server từ xa thẳng qua API)

**2.9 Log, theo dõi production, version prompt**

- OpenTelemetry: [Semantic conventions](https://opentelemetry.io/docs/specs/semconv/) (lướt nhóm *Generative AI* để biết tên attribute chuẩn)
- Eugene Yan: [Patterns for Building LLM-based Systems & Products](https://eugeneyan.com/writing/llm-patterns/) (phần evals, guardrails, collect feedback)

**3.1 Prompt injection**

- Simon Willison: [The lethal trifecta for AI agents](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/), và lướt [chuỗi bài prompt injection](https://simonwillison.net/series/prompt-injection/)
- OWASP: LLM01 Prompt Injection và LLM07 System Prompt Leakage trong [Top 10](https://genai.owasp.org/llm-top-10/)
- Anthropic: [Mitigate jailbreaks and prompt injections](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks)

**3.2 Rò rỉ dữ liệu, PII và phân quyền trong RAG**

- OWASP: LLM02 Sensitive Information Disclosure và LLM08 Vector and Embedding Weaknesses trong [Top 10](https://genai.owasp.org/llm-top-10/)
- Bảo mật chung và dữ liệu cá nhân: [10-security.md](10-security.md)

**3.3 Guardrail và moderation**

- OpenAI: [Moderation](https://developers.openai.com/api/docs/guides/moderation)
- Anthropic: [Mitigate jailbreaks and prompt injections](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks) và các trang cùng mục *Strengthen guardrails*
- Eugene Yan: [Patterns for Building LLM-based Systems](https://eugeneyan.com/writing/llm-patterns/) (phần guardrails)

**3.4 Eval**

- Anthropic: [Define success criteria and build evaluations](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests)
- OpenAI: [Evals](https://developers.openai.com/api/docs/guides/evals)
- Hamel Husain: [Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/)
- *AI Engineering* (Chip Huyen): các chương về evaluation

**3.5 Bên trong vector search**

- Bài gốc: [Malkov, Yashunin: HNSW](https://arxiv.org/abs/1603.09320) (đọc phần 1, 3 và hình minh hoạ)
- [pgvector](https://github.com/pgvector/pgvector): mục HNSW, IVFFlat, *Iterative Index Scans*

</details>

### Ngoài kỹ thuật

<details>
<summary><strong>24. Kỹ năng senior: ra quyết định, giao hàng, dẫn dắt</strong> (14 module, 38 link)</summary>

Học chi tiết: [24-senior-leadership.md](24-senior-leadership.md)

**1.1 Senior là gì, ownership**

- Staff Engineer: [Staff archetypes](https://staffeng.com/guides/staff-archetypes/), [Work on what matters](https://staffeng.com/guides/work-on-what-matters/)
- The Staff Engineer's Path: Part I (*The Big Picture*), ch.1 về vai trò

**1.2 Khung trade-off và loại quyết định**

- Jeff Bezos: [2016 Letter to Shareholders](https://www.aboutamazon.com/news/company-news/2016-letter-to-shareholders) (mục high-velocity decision making, disagree and commit)
- Staff Engineer: [Learn to never be wrong](https://staffeng.com/guides/learn-to-never-be-wrong/)

**1.3 Build vs buy, chọn công nghệ mới**

- Dan McKinley: [Choose Boring Technology](https://mcfunley.com/choose-boring-technology) (bài gốc, có bản slide ở [boringtechnology.club](https://boringtechnology.club/))
- The Staff Engineer's Path: ch.2–3 (hiểu bối cảnh và chiến lược kỹ thuật)

**1.4 Design doc/RFC và ADR**

- Malte Ubl: [Design Docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/)
- Pragmatic Engineer: [Companies Using RFCs or Design Docs and Examples of These](https://blog.pragmaticengineer.com/rfcs-and-design-docs/)
- Michael Nygard: [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) (bài gốc của ADR); [adr.github.io](https://adr.github.io/) và [template của Joel Parker Henderson](https://github.com/joelparkerhenderson/architecture-decision-record)

**1.5 Chất lượng dài hạn: tech debt, code review, chuẩn hoá, chi phí**

- Martin Fowler: [Technical Debt Quadrant](https://martinfowler.com/bliki/TechnicalDebtQuadrant.html), [Is High Quality Software Worth the Cost?](https://martinfowler.com/articles/is-quality-worth-cost.html)
- Staff Engineer: [Manage technical quality](https://staffeng.com/guides/manage-technical-quality/)
- Will Larson: [Migrations: the sole scalable fix to tech debt](https://lethain.com/migrations/)
- Google eng-practices: [The Standard of Code Review](https://google.github.io/eng-practices/review/reviewer/standard.html), [How to write code review comments](https://google.github.io/eng-practices/review/reviewer/comments.html), [Small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html)
- Chất lượng code và test: [20-testing-quality.md](20-testing-quality.md)

**2.1 Chia việc và ước lượng**

- Martin Fowler / Pete Hodgson: [Feature Toggles](https://martinfowler.com/articles/feature-toggles.html)
- The Staff Engineer's Path: Part II (*Execution*), ch.5 (*Leading Big Projects*)
- *Software Estimation: Demystifying the Black Art* (Steve McConnell): phần về cone of uncertainty, nếu muốn đọc sâu

**2.2 Rủi ro, dependency, cắt phạm vi, cập nhật tiến độ**

- Staff Engineer: [Staying aligned with authority](https://staffeng.com/guides/staying-aligned-with-authority/), [Present to executives](https://staffeng.com/guides/present-to-executives/)
- The Staff Engineer's Path: ch.6 (*Why Have We Stopped?*): các lý do dự án bị kẹt và cách gỡ

**2.3 Làm việc với product và business**

- Staff Engineer: [Getting in the room](https://staffeng.com/guides/getting-in-the-room/)
- *An Elegant Puzzle*: chương *Tools* (phần planning và metrics)

**2.4 Legacy và migration lớn**

- Martin Fowler: [Strangler Fig Application](https://martinfowler.com/bliki/StranglerFigApplication.html), [Patterns of Legacy Displacement](https://martinfowler.com/articles/patterns-legacy-displacement/)
- Stripe: [Online migrations at scale](https://stripe.com/blog/online-migrations) (4 bước dual write → đổi đọc → đổi ghi → dọn)
- Joel Spolsky: [Things You Should Never Do, Part I](https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/) (viết lại từ đầu)
- *Working Effectively with Legacy Code* (Michael Feathers): phần characterization test và seam

**2.5 Vận hành, sự cố, đo năng lực giao hàng**

- Google SRE Book: [Managing Incidents](https://sre.google/sre-book/managing-incidents/), [Postmortem Culture](https://sre.google/sre-book/postmortem-culture/); SRE Workbook: [Incident Response](https://sre.google/workbook/incident-response/)
- DORA: [DORA's software delivery metrics](https://dora.dev/guides/dora-metrics/), [Capabilities](https://dora.dev/capabilities/)
- *Accelerate*: Part I (các capability ảnh hưởng tới năng lực giao hàng)

**3.1 Mentor, onboarding, giao việc**

- Staff Engineer: [Create space for others](https://staffeng.com/guides/create-space-for-others/)
- The Staff Engineer's Path: Part III (*Leveling Up*), ch.7 (*You're a Role Model Now*) và ch.8 (*Good Influence at Scale*)

**3.2 Góp ý và nhận góp ý**

- Google eng-practices: [Handling pushback in code reviews](https://google.github.io/eng-practices/review/reviewer/pushback.html), [How to write code review comments](https://google.github.io/eng-practices/review/reviewer/comments.html)

**3.3 Đưa quyết định qua nhiều bên, ảnh hưởng khi không có quyền**

- Staff Engineer: [Staying aligned with authority](https://staffeng.com/guides/staying-aligned-with-authority/), [Getting in the room](https://staffeng.com/guides/getting-in-the-room/)
- Bezos: [2016 Letter to Shareholders](https://www.aboutamazon.com/news/company-news/2016-letter-to-shareholders) (disagree and commit)
- The Staff Engineer's Path: ch.3 (*Creating the Big Picture*): viết strategy và đưa nó qua tổ chức

**3.4 Tuyển người**

- Tech Interview Handbook: [Coding interview rubrics](https://www.techinterviewhandbook.org/coding-interview-rubrics/) (góc nhìn người chấm)
- *An Elegant Puzzle*: chương *Careers* (phần hiring funnel và thiết kế vòng phỏng vấn)

</details>

<details>
<summary><strong>25. Kỹ năng phỏng vấn</strong> (13 module, 23 link)</summary>

Học chi tiết: [25-interview-skills.md](25-interview-skills.md)

**1.1 Đọc JD và hiểu quy trình**

- Tech Interview Handbook: [Coding interview prep](https://www.techinterviewhandbook.org/coding-interview-prep/) (phần đầu về quy trình)
- Đối chiếu JD với [bản đồ tổng](README.md)

**1.2 CV, LinkedIn, GitHub**

- Tech Interview Handbook: [Resume](https://www.techinterviewhandbook.org/resume/)

**1.3 Giới thiệu bản thân**

- Tech Interview Handbook: [Self introduction](https://www.techinterviewhandbook.org/self-introduction/)

**1.4 Kho câu chuyện STAR**

- Tech Interview Handbook: [Behavioral interview](https://www.techinterviewhandbook.org/behavioral-interview/), [Behavioral interview questions](https://www.techinterviewhandbook.org/behavioral-interview-questions/)
- [Amazon Leadership Principles](https://www.amazon.jobs/content/en/our-workplace/leadership-principles)

**2.1 Screening HR, coding test online**

- Tech Interview Handbook: [Coding interview rubrics](https://www.techinterviewhandbook.org/coding-interview-rubrics/) (người chấm cho điểm theo những gì)

**2.2 Live coding**

- Tech Interview Handbook: [Coding interview techniques](https://www.techinterviewhandbook.org/coding-interview-techniques/), [Mock interviews](https://www.techinterviewhandbook.org/mock-interviews/)
- Chi tiết pattern và quy trình làm bài: [21-dsa.md](21-dsa.md) module 1.5

**2.3 Take-home và vòng code review/debug**

- Google eng-practices: [How to do a code review](https://google.github.io/eng-practices/review/reviewer/), [How to write code review comments](https://google.github.io/eng-practices/review/reviewer/comments.html)
- Bảo mật và testing: [10-security.md](10-security.md), [20-testing-quality.md](20-testing-quality.md)

**2.4 Hỏi đáp kỹ thuật, system design, behavioral: khung trả lời**

- Tech Interview Handbook: [System design](https://www.techinterviewhandbook.org/system-design/)

**2.5 Dùng AI trong phỏng vấn (2026)**

- Anthropic: [Guidance on Candidates' AI Usage](https://www.anthropic.com/candidate-ai-guidance)
- Canva: [Yes, You Can Use AI in Our Interviews](https://www.canva.dev/blog/engineering/yes-you-can-use-ai-in-our-interviews/) (đọc phần họ chấm gì)
- Hello Interview: [Meta's AI-Enabled Coding Interview](https://www.hellointerview.com/blog/meta-ai-enabled-coding) (nguồn thứ cấp, mô tả format vòng của Meta)
- Cách dùng AI khi làm việc và cách kể về nó: [26-ai-assisted-engineering.md](26-ai-assisted-engineering.md)

**3.1 Giao tiếp và tình huống khó**

- Tech Interview Handbook: [Behavioral interview](https://www.techinterviewhandbook.org/behavioral-interview/) (phần tips khi trả lời)

**3.2 Câu hỏi ngược cho người phỏng vấn**

- Tech Interview Handbook: [Final questions](https://www.techinterviewhandbook.org/final-questions/)

**3.3 Lương và offer (thị trường Việt Nam)**

- Tech Interview Handbook: [Understanding compensation](https://www.techinterviewhandbook.org/understanding-compensation/), [Negotiation](https://www.techinterviewhandbook.org/negotiation/), [Ten rules of negotiation](https://www.techinterviewhandbook.org/negotiation-rules/)
- [ITviec: Báo cáo Lương IT & Thị trường tuyển dụng IT Việt Nam](https://itviec.com/bao-cao/luong-it-va-thi-truong-tuyen-dung-it-vietnam)
- [levels.fyi: Software Engineer, Vietnam](https://www.levels.fyi/t/software-engineer/locations/vietnam)

**3.4 Tâm lý, mock, sau phỏng vấn**

- Tech Interview Handbook: [Mock interviews](https://www.techinterviewhandbook.org/mock-interviews/)

</details>
