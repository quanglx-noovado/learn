<?php
// Bài 1: Nền tảng PHP — biến, mảng, hàm, class, exception.
// Chạy: php php/01-basics/basics.php
//
// declare(strict_types=1) BẮT BUỘC nên có ở mọi file: nó tắt việc PHP tự
// chuyển kiểu ngầm ("5" -> 5), giúp lỗi lộ ra sớm thay vì âm thầm sai.
declare(strict_types=1);

// --- 1. Biến và kiểu -------------------------------------------------------
function bienVaKieu(): void
{
    // PHP là dynamic type: biến không cần khai báo kiểu, bắt đầu bằng '$'.
    $ten = 'PHP';
    $namRaDoi = 1995;
    $phienBan = 8.3;
    $laWeb = true;
    $khong = null;

    // Chuỗi nháy đôi nội suy biến; nháy đơn thì KHÔNG.
    echo "[1] \"$ten ra đời $namRaDoi\" vs '\$ten ra đời \$namRaDoi'\n";
    echo sprintf("[1] bản %.1f, web=%s, null=%s\n", $phienBan, var_export($laWeb, true), var_export($khong, true));

    // '==' so sánh lỏng (có chuyển kiểu), '===' so sánh chặt (cả kiểu).
    var_dump(0 == '0');    // true  — dễ gây bug
    var_dump(0 === '0');   // false — luôn ưu tiên dùng ===
    echo "\n";
}

// --- 2. Mảng ---------------------------------------------------------------
// Mảng PHP là kiểu lai: vừa là list (chỉ số 0,1,2...) vừa là map (key => value).
function mangPHP(): void
{
    $ngonNgu = ['Java', 'Go', 'PHP'];              // list
    $ngonNgu[] = 'JavaScript';                      // thêm vào cuối

    $namRaDoi = ['Java' => 1995, 'Go' => 2009, 'PHP' => 1995];  // associative array

    echo '[2] list: ' . implode(', ', $ngonNgu) . "\n";

    foreach ($namRaDoi as $ten => $nam) {
        echo sprintf("[2] %-5s -> %d\n", $ten, $nam);
    }

    // Kiểm tra key tồn tại. isset() trả false nếu giá trị là null,
    // array_key_exists() thì vẫn true — khác biệt quan trọng.
    echo '[2] có key Go? ' . (array_key_exists('Go', $namRaDoi) ? 'có' : 'không') . "\n";

    // Hàm mảng hay dùng: filter (lọc) + array_keys (lấy key).
    $cu = array_keys(array_filter($namRaDoi, fn(int $nam): bool => $nam < 2000));
    echo '[2] ra đời trước 2000: ' . implode(', ', $cu) . "\n\n";
}

// --- 3. Hàm ----------------------------------------------------------------
// Luôn khai báo kiểu tham số và kiểu trả về — kết hợp với strict_types
// sẽ chặn được phần lớn lỗi truyền sai dữ liệu.
function chia(float $a, float $b): float
{
    if ($b === 0.0) {
        throw new InvalidArgumentException('không thể chia cho 0');
    }
    return $a / $b;
}

function ham(): void
{
    echo sprintf("[3] 10/4 = %.2f\n", chia(10, 4));

    try {
        chia(1, 0);
    } catch (InvalidArgumentException $e) {
        echo '[3] bắt được: ' . $e->getMessage() . "\n\n";
    }
}

// --- 4. Class và object ----------------------------------------------------
final class NgonNgu
{
    // Constructor property promotion (PHP 8+): khai báo và gán field ngay
    // trên tham số constructor — thay cho 4 dòng boilerplate của PHP cũ.
    public function __construct(
        public readonly string $ten,   // readonly = gán một lần trong constructor
        private int $namRaDoi,
    ) {
    }

    public function namRaDoi(): int
    {
        return $this->namRaDoi;
    }

    public function doiNam(int $nam): void
    {
        if ($nam < 1950) {
            throw new InvalidArgumentException("năm không hợp lệ: $nam");
        }
        $this->namRaDoi = $nam;
    }

    public function __toString(): string
    {
        return "{$this->ten} ({$this->namRaDoi})";
    }
}

function classVaObject(): void
{
    $php = new NgonNgu('PHP', 1994);
    $php->doiNam(1995);
    echo "[4] $php\n";   // __toString() được gọi tự động

    try {
        $php->ten = 'Hack';   // readonly -> ném Error
    } catch (Error $e) {
        echo '[4] readonly chặn ghi: ' . $e->getMessage() . "\n";
    }
}

bienVaKieu();
mangPHP();
ham();
classVaObject();
