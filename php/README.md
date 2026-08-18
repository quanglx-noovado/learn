# PHP

Chạy một bài: `php php/01-basics/basics.php`

Kiểm tra đã cài chưa: `php -v`. Nếu chưa: `brew install php`.

## Lộ trình

- [x] **01-basics** — `strict_types`, biến & kiểu, `==` vs `===`, mảng, hàm, class PHP 8
- [ ] 02-oop — interface, trait, abstract, namespace, autoload PSR-4
- [ ] 03-composer — `composer init`, quản lý package, autoload, PHPUnit
- [ ] 04-http — request/response thuần, superglobal, route đơn giản
- [ ] 05-database — PDO, prepared statement (chống SQL injection)
- [ ] 06-framework — Laravel: route → controller → model → view
- [ ] 07-security — validate input, escape output (XSS), hash password

## Ba thứ nên bật/nhớ từ đầu

- `declare(strict_types=1);` ở đầu **mọi** file — tắt chuyển kiểu ngầm.
- Luôn dùng `===`, không dùng `==` (vì `0 == '0'` là `true`).
- Luôn khai báo kiểu tham số và kiểu trả về cho hàm/method.

## Bài tập cho 01-basics

1. Viết `function locTheoNam(array $ngonNgu, int $tu, int $den): array` dùng `array_filter`.
2. Tạo interface `CoTen` với method `ten(): string`, cho `NgonNgu` implement nó.
3. Thử truyền `'10'` (chuỗi) vào `chia()` — đọc lỗi, rồi xóa `strict_types` và chạy lại để thấy khác biệt.
