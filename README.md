# learn — repo học tập

Bốn nhánh học song song: **Java**, **Go**, **DSA**, **PHP**.

## Chạy thử

| Nhánh | Lệnh | Trạng thái công cụ |
|---|---|---|
| Go | `go run ./go/01-basics` | Go 1.26.1 — chạy được |
| DSA (Go) | `go test ./dsa/go/... -v` | chạy được |
| Java | `java java/01-basics/Basics.java` | **chưa cài JDK** |
| DSA (Java) | `java dsa/java/BinarySearch.java` | **chưa cài JDK** |
| PHP | `php php/01-basics/basics.php` | **chưa cài PHP** |

Cài phần còn thiếu (macOS + Homebrew):

```bash
brew install openjdk    # rồi làm theo hướng dẫn symlink mà brew in ra
brew install php
```

## Cấu trúc

```
go/        bài học Go, mỗi bài một thư mục package main
java/      bài học Java, một file .java chạy trực tiếp (JDK 11+)
php/       bài học PHP, một file .php chạy trực tiếp
dsa/       thuật toán & cấu trúc dữ liệu, cài lại bằng nhiều ngôn ngữ
  go/      có test bằng `go test`
  java/    test thủ công trong hàm main
```

Toàn repo là **một Go module** (`go.mod` ở gốc, module `learn`), nên `go test ./...`
chạy được mọi test Go ở bất kỳ thư mục nào.

## Lộ trình

Xem `README.md` trong từng thư mục nhánh. Nguyên tắc chung: mỗi bài là code
**chạy được**, có chú thích giải thích *vì sao*, và kết thúc bằng bài tập tự làm.
