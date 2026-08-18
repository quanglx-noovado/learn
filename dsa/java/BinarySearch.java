// DSA — Tìm kiếm nhị phân (bản Java, đối chiếu với dsa/go/searching).
// Chạy: java dsa/java/BinarySearch.java
public class BinarySearch {

    /**
     * Tìm target trong mảng ĐÃ SẮP XẾP tăng dần.
     * @return chỉ số của target, hoặc -1 nếu không có.
     * Thời gian O(log n), bộ nhớ O(1).
     */
    static int search(int[] nums, int target) {
        int lo = 0, hi = nums.length - 1;   // vùng tìm kiếm [lo, hi]

        while (lo <= hi) {
            // >>> 1 là chia 2 (dịch bit) và không bị tràn số như (lo + hi) / 2.
            int mid = lo + ((hi - lo) >>> 1);

            if (nums[mid] == target) return mid;
            if (nums[mid] < target) lo = mid + 1;   // đáp án ở nửa phải
            else hi = mid - 1;                      // đáp án ở nửa trái
        }
        return -1;
    }

    /** Chỉ số đầu tiên có nums[i] >= target; bằng nums.length nếu không có. */
    static int lowerBound(int[] nums, int target) {
        int lo = 0, hi = nums.length;   // vùng [lo, hi) — đầu phải mở

        while (lo < hi) {
            int mid = lo + ((hi - lo) >>> 1);
            if (nums[mid] < target) lo = mid + 1;   // mid không thể là đáp án
            else hi = mid;                          // mid có thể là đáp án
        }
        return lo;
    }

    // Test thủ công (chưa dùng JUnit để khỏi phải cài thêm gì).
    public static void main(String[] args) {
        int[] nums = {1, 3, 5, 7, 9, 11};
        kiemTra("đầu",           search(nums, 1),   0);
        kiemTra("giữa",          search(nums, 7),   3);
        kiemTra("cuối",          search(nums, 11),  5);
        kiemTra("không có",      search(nums, 4),  -1);
        kiemTra("mảng rỗng",     search(new int[0], 1), -1);

        int[] trung = {1, 2, 2, 2, 5};
        kiemTra("lowerBound 2",  lowerBound(trung, 2), 1);
        kiemTra("lowerBound 3",  lowerBound(trung, 3), 4);
        kiemTra("lowerBound 6",  lowerBound(trung, 6), 5);
    }

    static void kiemTra(String ten, int duoc, int muon) {
        System.out.printf("%s %-14s được=%d muốn=%d%n", duoc == muon ? "PASS" : "FAIL", ten, duoc, muon);
    }
}
