package searching

import "testing"

// Table-driven test: cách viết test tiêu chuẩn trong Go.
// Chạy: go test ./dsa/go/...      (thêm -v để xem từng case)
func TestBinarySearch(t *testing.T) {
	nums := []int{1, 3, 5, 7, 9, 11}

	cases := []struct {
		ten    string
		target int
		muon   int
	}{
		{"phần tử đầu", 1, 0},
		{"phần tử giữa", 7, 3},
		{"phần tử cuối", 11, 5},
		{"không tồn tại", 4, -1},
		{"nhỏ hơn tất cả", 0, -1},
		{"lớn hơn tất cả", 99, -1},
	}

	for _, c := range cases {
		t.Run(c.ten, func(t *testing.T) {
			if duoc := BinarySearch(nums, c.target); duoc != c.muon {
				t.Errorf("BinarySearch(%v, %d) = %d; muốn %d", nums, c.target, duoc, c.muon)
			}
		})
	}
}

func TestBinarySearchSliceRong(t *testing.T) {
	if duoc := BinarySearch(nil, 1); duoc != -1 {
		t.Errorf("slice rỗng: được %d; muốn -1", duoc)
	}
}

func TestLowerBound(t *testing.T) {
	// Có phần tử trùng: LowerBound phải trả về vị trí trùng ĐẦU TIÊN.
	nums := []int{1, 2, 2, 2, 5}

	cases := []struct{ target, muon int }{
		{0, 0}, // chèn trước tất cả
		{2, 1}, // số 2 đầu tiên ở chỉ số 1
		{3, 4}, // không có 3 -> vị trí chèn là 4
		{5, 4},
		{6, 5}, // lớn hơn tất cả -> len(nums)
	}

	for _, c := range cases {
		if duoc := LowerBound(nums, c.target); duoc != c.muon {
			t.Errorf("LowerBound(%v, %d) = %d; muốn %d", nums, c.target, duoc, c.muon)
		}
	}
}
