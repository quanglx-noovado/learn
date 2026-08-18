// Bài 1: Nền tảng Go — biến, hàm, slice, map, struct, error.
// Chạy: go run ./go/01-basics
package main

import (
	"errors"
	"fmt"
	"strings"
)

func main() {
	bienVaKieu()
	hamVaNhieuGiaTriTraVe()
	sliceVaMap()
	structVaMethod()
	xuLyLoi()
}

// --- 1. Biến và kiểu -------------------------------------------------------
// Go là ngôn ngữ static type: kiểu được xác định lúc biên dịch.
func bienVaKieu() {
	var ten string = "Go"   // khai báo đầy đủ
	var namRaDoi = 2009     // kiểu được suy ra -> int
	phienBan := 1.26        // ':=' chỉ dùng được trong hàm
	const laCompiled = true // hằng số

	// Zero value: biến chưa gán vẫn có giá trị mặc định, KHÔNG phải null.
	var chuaGan int      // 0
	var chuoiRong string // ""
	var conTro *int      // nil

	fmt.Printf("[1] %s ra đời %d, bản %.2f, compiled=%t\n", ten, namRaDoi, phienBan, laCompiled)
	fmt.Printf("[1] zero values: int=%d, string=%q, pointer=%v\n\n", chuaGan, chuoiRong, conTro)
}

// --- 2. Hàm ----------------------------------------------------------------
// Điểm đặc trưng: Go trả về nhiều giá trị cùng lúc.
func chia(a, b float64) (float64, error) {
	if b == 0 {
		return 0, errors.New("không thể chia cho 0")
	}
	return a / b, nil
}

func hamVaNhieuGiaTriTraVe() {
	ketQua, err := chia(10, 4)
	fmt.Printf("[2] 10/4 = %.2f, err = %v\n", ketQua, err)

	// '_' để bỏ giá trị không dùng. Go báo lỗi nếu biến khai báo mà không dùng.
	_, err = chia(1, 0)
	fmt.Printf("[2] 1/0 -> err = %v\n\n", err)
}

// --- 3. Slice và map -------------------------------------------------------
func sliceVaMap() {
	// Slice: mảng động. len = số phần tử, cap = dung lượng đã cấp.
	ngonNgu := []string{"Java", "Go"}
	ngonNgu = append(ngonNgu, "PHP") // append CÓ THỂ cấp lại bộ nhớ -> phải gán lại
	fmt.Printf("[3] slice=%v len=%d cap=%d\n", ngonNgu, len(ngonNgu), cap(ngonNgu))

	// Map: bảng băm. Thứ tự lặp KHÔNG xác định — đừng phụ thuộc vào nó.
	namRaDoi := map[string]int{"Java": 1995, "Go": 2009, "PHP": 1995}

	// Cú pháp "comma ok" để phân biệt "không có key" với "giá trị bằng 0".
	if nam, ok := namRaDoi["Go"]; ok {
		fmt.Printf("[3] Go ra đời năm %d\n", nam)
	}
	if _, ok := namRaDoi["Rust"]; !ok {
		fmt.Println("[3] không có key \"Rust\" trong map")
	}

	// for ... range đi qua từng phần tử.
	var in []string
	for i, l := range ngonNgu {
		in = append(in, fmt.Sprintf("%d:%s(%d)", i, l, namRaDoi[l]))
	}
	fmt.Printf("[3] %s\n\n", strings.Join(in, " "))
}

// --- 4. Struct và method ---------------------------------------------------
// Go không có class/kế thừa. Thay vào đó: struct + method + interface.
type NgonNgu struct {
	Ten      string
	NamRaDoi int
}

// Receiver value: nhận bản copy, không sửa được bản gốc.
func (n NgonNgu) MoTa() string {
	return fmt.Sprintf("%s (%d)", n.Ten, n.NamRaDoi)
}

// Receiver pointer: sửa được bản gốc.
func (n *NgonNgu) DoiTen(ten string) {
	n.Ten = ten
}

func structVaMethod() {
	n := NgonNgu{Ten: "Golang", NamRaDoi: 2009}
	fmt.Printf("[4] trước: %s\n", n.MoTa())
	n.DoiTen("Go") // Go tự lấy địa chỉ: (&n).DoiTen("Go")
	fmt.Printf("[4] sau:   %s\n\n", n.MoTa())
}

// --- 5. Xử lý lỗi ----------------------------------------------------------
// Go KHÔNG dùng exception cho lỗi thường. Lỗi là một giá trị được trả về.
var ErrKhongTimThay = errors.New("không tìm thấy")

func timNgonNgu(ten string) (NgonNgu, error) {
	kho := []NgonNgu{{"Java", 1995}, {"Go", 2009}, {"PHP", 1995}}
	for _, n := range kho {
		if n.Ten == ten {
			return n, nil
		}
	}
	// %w "bọc" lỗi gốc lại để tầng trên vẫn kiểm tra được bằng errors.Is.
	return NgonNgu{}, fmt.Errorf("tra cứu %q: %w", ten, ErrKhongTimThay)
}

func xuLyLoi() {
	if n, err := timNgonNgu("Go"); err == nil {
		fmt.Printf("[5] tìm thấy %s\n", n.MoTa())
	}

	_, err := timNgonNgu("Rust")
	fmt.Printf("[5] err = %v\n", err)
	fmt.Printf("[5] errors.Is(err, ErrKhongTimThay) = %t\n", errors.Is(err, ErrKhongTimThay))
}
