# CLAUDE.md

Repo học tập cá nhân. Bốn nhánh: `java/`, `go/`, `dsa/`, `php/`.

## Cách làm việc trong repo này

- **Dạy, không chỉ đưa code.** Giải thích *vì sao* chọn cách đó, và cạm bẫy thường gặp.
- Trả lời và viết chú thích code bằng **tiếng Việt**. Giữ nguyên thuật ngữ tiếng Anh
  (slice, interface, exception, big-O...) — người học cần quen mặt từ gốc.
- Mỗi bài học phải **chạy được** bằng một lệnh duy nhất, không cần cài thêm gì
  ngoài compiler/interpreter của ngôn ngữ đó.
- Ưu tiên ví dụ nhỏ, tự chứa. Không thêm framework/abstraction khi chưa cần —
  hỏi trước nếu định thêm dependency.
- Mỗi bài kết thúc bằng **bài tập** cho người học tự làm. Không tự động giải bài tập
  trừ khi được yêu cầu; nếu người học nộp bài, hãy review chứ đừng viết lại hộ.
- Khi cùng một khái niệm tồn tại ở nhiều ngôn ngữ, hãy **đối chiếu**
  (ví dụ: error của Go so với exception của Java/PHP).

## Quy ước code

- Go: `gofmt` trước khi xong; test theo kiểu table-driven; module gốc là `learn`.
- Java: một file một class public, tên file trùng tên class, chạy `java File.java` (JDK 11+).
- PHP: luôn `declare(strict_types=1);`, luôn `===`, luôn khai báo kiểu.

## Trạng thái công cụ (cập nhật 2026-08-18)

- Go 1.26.1 đã cài.
- **Chưa có JDK và PHP** → code Java/PHP trong repo chưa từng được chạy thử.
  Cài bằng `brew install openjdk` và `brew install php`.
