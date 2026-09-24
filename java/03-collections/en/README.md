# Raw English source

Bản gốc tiếng Anh của các bài trong `java/03-collections/`, tải từ
[dev.java](https://dev.java/learn/api/collections-framework/) và chuyển sang markdown thô.

Mỗi file EN khớp 1:1 với bản dịch tiếng Việt cùng số thứ tự:

| # | Tiếng Việt | Tiếng Anh (gốc) |
|---|---|---|
| 01 | `../01-gioi-thieu.md` | `01-intro.md` |
| 02 | `../02-cay-phan-cap-collection.md` | `02-organization.md` |
| 03 | `../03-luu-phan-tu-trong-collection.md` | `03-collection-interface.md` |
| 04 | `../04-iterate-phan-tu.md` | `04-iterating.md` |
| 05 | `../05-list.md` | `05-lists.md` |
| 06 | `../06-set-sortedset-navigableset.md` | `06-sets.md` |
| 07 | `../07-factory-methods.md` | `07-factory-methods.md` |
| 08 | `../08-stack-va-queue.md` | `08-stacks-queues.md` |

## Tải lại / tải thêm bài

```bash
# tải lại cả series collections (ghi đè)
python3 tools/fetch_devjava.py --all java/03-collections/en

# tải một trang bất kỳ của dev.java
python3 tools/fetch_devjava.py https://dev.java/learn/api/collections-framework/maps/ java/03-collections/en/09-maps.md
```

Script `tools/fetch_devjava.py` chỉ dùng standard library của Python. Nội dung file
là **markdown thô**: giữ nguyên câu chữ của dev.java, chỉ có 2 dòng `> Source: ...`
ở đầu để ghi nguồn — xóa được nếu bạn không cần.

Đây là bản lưu để học cá nhân. Bản quyền nội dung thuộc dev.java / Oracle.
