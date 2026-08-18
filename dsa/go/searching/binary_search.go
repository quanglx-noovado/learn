// Package searching: các thuật toán tìm kiếm.
package searching

// BinarySearch tìm target trong slice ĐÃ SẮP XẾP tăng dần.
// Trả về chỉ số của target, hoặc -1 nếu không có.
//
// Ý tưởng: mỗi bước loại bỏ một nửa vùng tìm kiếm.
// Độ phức tạp: thời gian O(log n), bộ nhớ O(1).
func BinarySearch(nums []int, target int) int {
	lo, hi := 0, len(nums)-1 // vùng tìm kiếm [lo, hi] — hai đầu đều đóng

	for lo <= hi { // còn ít nhất 1 phần tử thì còn tìm
		// Vì sao không viết (lo+hi)/2? Với n rất lớn, lo+hi có thể tràn số.
		// Cách viết dưới đây luôn an toàn.
		mid := lo + (hi-lo)/2

		switch {
		case nums[mid] == target:
			return mid
		case nums[mid] < target:
			lo = mid + 1 // target nằm ở nửa phải
		default:
			hi = mid - 1 // target nằm ở nửa trái
		}
	}
	return -1
}

// LowerBound trả về chỉ số ĐẦU TIÊN có nums[i] >= target.
// Nếu mọi phần tử đều nhỏ hơn target, trả về len(nums).
//
// Biến thể này quan trọng hơn BinarySearch trong thực tế: nó trả lời
// "chèn vào đâu" và xử lý được mảng có phần tử trùng nhau.
// Ở đây vùng tìm kiếm là [lo, hi) — đầu phải MỞ.
func LowerBound(nums []int, target int) int {
	lo, hi := 0, len(nums)

	for lo < hi {
		mid := lo + (hi-lo)/2
		if nums[mid] < target {
			lo = mid + 1 // mid chắc chắn không phải đáp án
		} else {
			hi = mid // mid CÓ THỂ là đáp án -> giữ lại
		}
	}
	return lo
}
