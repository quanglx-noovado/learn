# Kiến thức tổng hợp

> [← Mục lục ôn phỏng vấn](../README.md)

Mỗi file ở đây là **bài đọc tổng hợp** cho một chủ đề: nội dung của các tài liệu gốc (official
docs, RFC, blog kỹ thuật, sách) được viết lại thành một bài liền mạch theo đúng thứ tự module của
file plan. Mục đích là để bạn không phải mở hàng chục link khi học.

## Cách học một chủ đề

1. **Đọc file plan** (ví dụ [../03-database-sql.md](../03-database-sql.md)): xem "Vì sao cần học"
   và "Học gì" của từng module để biết mình sắp học gì.
2. **Đọc file kiến thức** cùng số ở đây. Mỗi module có phần giải thích, ví dụ, cạm bẫy, và một
   đoạn "Tóm tắt nhanh" để ôn lại trước khi phỏng vấn.
3. **Quay lại file plan**, tick các tiêu chí "Nắm chắc khi", rồi tự trả lời Phần 2 (câu hỏi).
4. Chỗ nào muốn hiểu sâu hơn thì mở link ở mục "Nguồn" cuối mỗi module.

## Giáo trình (từ cơ bản tới nâng cao)

Viết như sách cho người chưa biết gì về chủ đề: mỗi chương đi từ "là gì, để làm gì" tới cơ chế bên
trong, có ví dụ chạy được, lỗi thường gặp, câu hỏi tự kiểm tra và bài tập. Mỗi chương đã qua một
lượt review độc lập đối chiếu tài liệu gốc.

| Giáo trình | File plan |
|---|---|
| [PHP và Laravel](php/README.md) (30 chương) | [05-php-laravel.md](../05-php-laravel.md) |
| [Database quan hệ](database/README.md) (đang viết) | [03-database-sql.md](../03-database-sql.md) |

## Bài đọc tổng hợp theo module

Bản ngắn hơn, bám theo thứ tự module của plan, hợp để ôn lại.

| File kiến thức | File plan |
|---|---|
| [03. Database quan hệ và SQL](03-database-sql.md) | [03-database-sql.md](../03-database-sql.md) |
| [05. PHP và Laravel](05-php-laravel.md) (đã có giáo trình đầy đủ ở trên) | [05-php-laravel.md](../05-php-laravel.md) |
| [09. Thiết kế API](09-api-design.md) | [09-api-design.md](../09-api-design.md) |
| [10. Bảo mật](10-security.md) | [10-security.md](../10-security.md) |
| [11. Cache](11-cache.md) | [11-cache.md](../11-cache.md) |
| [13. Concurrency](13-concurrency.md) | [13-concurrency.md](../13-concurrency.md) |

Các chủ đề khác sẽ được bổ sung dần.

## Lưu ý

- Kiến thức được viết lại bằng lời của mình từ nguồn gốc, không phải bản dịch. Khi cần con số
  chính xác tuyệt đối (giá trị mặc định, giới hạn), đối chiếu lại docs của phiên bản bạn đang dùng.
- Mốc phiên bản tại thời điểm viết: 09/2026 (MySQL 8.4 LTS, PostgreSQL 18, PHP 8.5, Laravel 13).
