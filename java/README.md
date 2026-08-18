# Java

Chạy một bài (JDK 11+, không cần `javac`): `java java/01-basics/Basics.java`

Kiểm tra đã cài chưa: `java -version`. Nếu chưa: `brew install openjdk`.

## Lộ trình

- [x] **01-basics** — primitive vs reference, `==` vs `.equals()`, class/object, collection, exception
- [ ] 02-oop — kế thừa, `abstract`, `interface`, đa hình, `record`
- [ ] 03-collections — `List`/`Set`/`Map`, khi nào dùng cái nào, `equals`/`hashCode`
- [ ] 04-generics — type parameter, wildcard `? extends` / `? super`
- [ ] 05-streams — `map`/`filter`/`collect`, `Optional`
- [ ] 06-concurrency — `Thread`, `ExecutorService`, `synchronized`, virtual thread
- [ ] 07-build — chuyển sang Maven, thêm JUnit 5, viết test thật
- [ ] 08-spring — Spring Boot REST API cơ bản

## Quy tắc dễ vướng

- Tên file phải trùng tên class `public` bên trong.
- `==` trên object là so sánh **địa chỉ**; so sánh nội dung luôn dùng `.equals()`.
- Primitive (`int`) không thể `null`; wrapper (`Integer`) thì có thể → dễ `NullPointerException`.

## Bài tập cho 01-basics

1. Thêm class `KhoNgonNgu` với method `timTheoTen(String)` trả về `Optional<NgonNgu>`.
2. Cho `NgonNgu` implement `Comparable<NgonNgu>` (sắp theo năm) rồi `Collections.sort`.
3. Ghi đè `equals` và `hashCode` cho `NgonNgu`, kiểm tra bằng `HashSet` xem có chặn trùng.
