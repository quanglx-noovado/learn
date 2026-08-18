// Bài 1: Nền tảng Java — kiểu dữ liệu, class, object, collection, exception.
// Chạy (JDK 11+, không cần biên dịch riêng): java java/01-basics/Basics.java
//
// Quy tắc Java: tên file PHẢI trùng tên class public bên trong (Basics.java -> class Basics).

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class Basics {

    // main là điểm khởi đầu của mọi chương trình Java.
    public static void main(String[] args) {
        kieuDuLieu();
        classVaObject();
        collections();
        xuLyException();
    }

    // --- 1. Kiểu dữ liệu ---------------------------------------------------
    static void kieuDuLieu() {
        // Primitive: lưu trực tiếp giá trị, KHÔNG thể null.
        int soNguyen = 42;
        double soThuc = 3.14;
        boolean dung = true;
        char kyTu = 'J';

        // Reference: lưu địa chỉ tới object trên heap, CÓ THỂ null.
        String chuoi = "Java";
        Integer boxed = 42;   // bản "đóng hộp" của int
        String rong = null;

        // Bẫy kinh điển: '==' so sánh địa chỉ, '.equals()' so sánh nội dung.
        String a = new String("Java");
        String b = new String("Java");
        System.out.printf("[1] a == b      -> %b  (so sánh địa chỉ)%n", a == b);
        System.out.printf("[1] a.equals(b) -> %b  (so sánh nội dung)%n", a.equals(b));
        System.out.printf("[1] %d %.2f %b %c %s boxed=%d null=%s%n%n",
                soNguyen, soThuc, dung, kyTu, chuoi, boxed, rong);
    }

    // --- 2. Class và object ------------------------------------------------
    // Java là OOP: dữ liệu và hành vi được gói trong class.
    static class NgonNgu {
        // private: chỉ truy cập được trong class này (encapsulation).
        private final String ten;   // final = gán một lần, không đổi được nữa
        private int namRaDoi;

        NgonNgu(String ten, int namRaDoi) {   // constructor
            this.ten = ten;
            this.namRaDoi = namRaDoi;
        }

        String getTen() { return ten; }

        void setNamRaDoi(int nam) {
            if (nam < 1950) throw new IllegalArgumentException("năm không hợp lệ: " + nam);
            this.namRaDoi = nam;
        }

        // @Override: ghi đè method của lớp cha (Object.toString).
        // Annotation này giúp compiler báo lỗi nếu bạn viết sai tên method.
        @Override
        public String toString() {
            return ten + " (" + namRaDoi + ")";
        }
    }

    static void classVaObject() {
        NgonNgu java = new NgonNgu("Java", 1990); // 'new' cấp object trên heap
        java.setNamRaDoi(1995);                   // sửa qua setter, không truy cập field trực tiếp
        System.out.println("[2] " + java);         // tự gọi toString()

        try {
            java.setNamRaDoi(1900);
        } catch (IllegalArgumentException e) {
            System.out.println("[2] bị chặn: " + e.getMessage() + "\n");
        }
    }

    // --- 3. Collections ----------------------------------------------------
    static void collections() {
        // Khai báo theo interface (List), khởi tạo bằng implementation (ArrayList).
        // Nhờ vậy sau này đổi sang LinkedList không phải sửa code xung quanh.
        List<String> ngonNgu = new ArrayList<>();   // <> = generics: chỉ chứa String
        ngonNgu.add("Java");
        ngonNgu.add("Go");
        ngonNgu.add("PHP");

        Map<String, Integer> namRaDoi = new HashMap<>();
        namRaDoi.put("Java", 1995);
        namRaDoi.put("Go", 2009);
        namRaDoi.put("PHP", 1995);

        for (String l : ngonNgu) {   // for-each
            System.out.printf("[3] %-5s -> %d%n", l, namRaDoi.get(l));
        }

        // Stream API (Java 8+): xử lý dữ liệu theo kiểu khai báo.
        String cu = ngonNgu.stream()
                .filter(l -> namRaDoi.get(l) < 2000)   // lambda
                .sorted()
                .reduce((x, y) -> x + ", " + y)
                .orElse("(không có)");
        System.out.println("[3] ra đời trước 2000: " + cu + "\n");
    }

    // --- 4. Exception ------------------------------------------------------
    // Khác Go (trả lỗi về như giá trị), Java "ném" exception và bắt bằng try/catch.
    static int docSoNguyen(String s) {
        return Integer.parseInt(s);   // ném NumberFormatException nếu s không phải số
    }

    static void xuLyException() {
        System.out.println("[4] parse \"123\" -> " + docSoNguyen("123"));

        try {
            docSoNguyen("abc");
        } catch (NumberFormatException e) {
            System.out.println("[4] bắt được: " + e.getClass().getSimpleName());
        } finally {
            // finally luôn chạy, dù có exception hay không -> nơi dọn tài nguyên.
            System.out.println("[4] finally luôn chạy");
        }
    }
}
