# Xử lý value của Map bằng lambda expression

> Dịch từ [Handling Map Values with Lambda Expressions](https://dev.java/learn/api/collections-framework/maps-and-lambdas/) — dev.java.

## Tiêu thụ nội dung của một Map

Interface [`Map`][Map] có method [`forEach()`][mapForEach] hoạt động giống method [`forEach()`][iterForEach] của interface [`Iterable`][Iterable]. Khác biệt là [`forEach()`][mapForEach] của Map nhận một [`BiConsumer`][BiConsumer] làm tham số thay vì một [`Consumer`][Consumer] đơn giản.

Nếu bạn nóng lòng muốn thực hành, hãy nhảy xuống cuối trang: [Thực hành các phép toán trên Map](#thực-hành-các-phép-toán-trên-map).

Tạo một map đơn giản và in nội dung của nó:

```java
Map<Integer, String> map = new HashMap<>();
map.put(1, "one");
map.put(2, "two");
map.put(3, "three");

map.forEach((key, value) -> IO.println(key + " :: " + value));
```

Kết quả:

```text
1 :: one
2 :: two
3 :: three
```

## Thay thế value

Interface [`Map`][Map] cho bạn ba method để thay value gắn với một key bằng value khác.

Cái đầu tiên là [`replace(key, value)`][replace], thay value hiện có bằng value mới, một cách "mù quáng". Đây tương đương với thao tác **put-if-present**. Method này trả về value đã bị lấy khỏi map.

Nếu bạn cần kiểm soát tinh hơn, hãy dùng overload nhận value cũ làm tham số: [`replace(key, oldValue, newValue)`][replace3]. Trong trường hợp này, value đang được map chỉ bị thay bằng `newValue` nếu nó **khớp** `oldValue`. Method này trả về `true` nếu việc thay thế đã diễn ra.

Interface [`Map`][Map] cũng có method để thay **tất cả** value của map bằng một [`BiFunction`][BiFunction]. [`BiFunction`][BiFunction] này là một *remapping function*, nhận key và value làm tham số, và trả về value mới sẽ thay thế value hiện có. Lời gọi method này iterate nội bộ qua tất cả cặp key/value của map.

Ví dụ dùng [`replaceAll()`][replaceAll]:

```java
Map<Integer, String> map = new HashMap<>();

map.put(1, "one");
map.put(2, "two");
map.put(3, "three");

map.replaceAll((key, value) -> value.toUpperCase());
map.forEach((key, value) -> IO.println(key + " :: " + value));
```

Kết quả:

```text
1 :: ONE
2 :: TWO
3 :: THREE
```

## Tính toán value (compute)

Interface [`Map`][Map] cho bạn pattern thứ ba để thêm cặp key-value hoặc sửa value hiện có, dưới dạng ba method: [`compute()`][compute], [`computeIfPresent()`][computeIfPresent] và [`computeIfAbsent()`][computeIfAbsent].

Ba method này nhận các tham số sau:

- key mà việc tính toán được thực hiện trên đó,
- một [`BiFunction`][BiFunction] đóng vai trò remapping function — hoặc một mapping function trong trường hợp [`computeIfAbsent()`][computeIfAbsent].

Với [`compute()`][compute] và [`computeIfPresent()`][computeIfPresent], bifunction này nhận key và value đang gắn với key đó.

Với [`compute()`][compute], remapping bifunction được gọi với hai tham số. Cái đầu là key, cái thứ hai là value hiện có nếu có, hoặc `null` nếu không có. Remapping bifunction của bạn **có thể** được gọi với value null.

Với [`computeIfPresent()`][computeIfPresent], remapping function cũng là một [`BiFunction`][BiFunction] nhận key và value gắn với nó. Nó được gọi **nếu** có value non-null gắn với key đó. Nếu key gắn với value null thì remapping function **không** được gọi. Remapping function của bạn không thể bị gọi với value null.

Với [`computeIfAbsent()`][computeIfAbsent], vì không có value nào gắn với key đó, remapping function thực chất là một [`Function`][Function] đơn giản nhận key làm tham số. Function này được gọi nếu key không có trong map hoặc nếu nó gắn với value null.

Trong mọi trường hợp, nếu bifunction (hoặc function) của bạn trả về null thì **key bị xóa** khỏi map: không mapping nào được tạo cho key đó. Không cặp key/value nào với value null có thể được đưa vào map bằng ba method này.

Trong mọi trường hợp, giá trị trả về là **value mới** gắn với key đó trong map, hoặc null nếu remapping function trả về null. Đáng chỉ ra rằng ngữ nghĩa này **khác** với các method [`put()`][put]. Các method [`put()`][put] trả về value **trước đó**, còn các method [`compute()`][compute] trả về value **mới**.

Một use case rất hay của [`computeIfAbsent()`][computeIfAbsent] là tạo map mà value là các list. Giả sử bạn có list string sau: `[one two three four five six seven]`. Bạn cần tạo một map mà key là độ dài của các từ trong list, còn value là list các từ đó. Bạn cần tạo map như sau:

```text
3 :: [one, two, six]
4 :: [four, five]
5 :: [three, seven]
```

Không có các method [`compute()`][compute], bạn có lẽ sẽ viết:

```java
List<String> strings = List.of("one", "two", "three", "four", "five", "six", "seven");
Map<Integer, List<String>> map = new HashMap<>();
for (String word: strings) {
    int length = word.length();
    if (!map.containsKey(length)) {
        map.put(length, new ArrayList<>());
    }
    map.get(length).add(word);
}

map.forEach((key, value) -> IO.println(key + " :: " + value));
```

Kết quả đúng như mong đợi:

```text
3 :: [one, two, six]
4 :: [four, five]
5 :: [three, seven]
```

Nhân đây, bạn có thể dùng [`putIfAbsent()`][putIfAbsent] để đơn giản hóa vòng for này:

```java
List<String> strings = List.of("one", "two", "three", "four", "five", "six", "seven");
Map<Integer, List<String>> map = new HashMap<>();
for (String word: strings) {
    int length = word.length();
    map.putIfAbsent(length, new ArrayList<>());
    map.get(length).add(word);
}

map.forEach((key, value) -> IO.println(key + " :: " + value));
```

Cho ra:

```text
3 :: [one, two, six]
4 :: [four, five]
5 :: [three, seven]
```

Nhưng dùng [`computeIfAbsent()`][computeIfAbsent] khiến code còn tốt hơn nữa:

```java
List<String> strings = List.of("one", "two", "three", "four", "five", "six", "seven");
Map<Integer, List<String>> map = new HashMap<>();
for (String word: strings) {
    int length = word.length();
    map.computeIfAbsent(length, key -> new ArrayList<>())
       .add(word);
}

map.forEach((key, value) -> IO.println(key + " :: " + value));
```

Cho ra:

```text
3 :: [one, two, six]
4 :: [four, five]
5 :: [three, seven]
```

Đoạn code này hoạt động thế nào?

- Nếu key không có trong map, mapping function được gọi và tạo một list rỗng. List này được [`computeIfAbsent()`][computeIfAbsent] trả về. Đây chính là list rỗng mà code thêm `word` vào.
- Nếu key có trong map, mapping function **không** được gọi, và value hiện tại gắn với key đó được trả về. Đây là list đã điền một phần mà bạn cần thêm `word` vào.

Code này **hiệu quả hơn nhiều** so với bản dùng [`putIfAbsent()`][putIfAbsent], chủ yếu vì list rỗng chỉ được tạo **khi cần**. Lời gọi [`putIfAbsent()`][putIfAbsent] đòi hỏi phải có sẵn một list rỗng, mà list đó chỉ được dùng nếu key chưa có trong map. Trong trường hợp object bạn thêm vào map phải được tạo theo yêu cầu (on demand), nên **ưu tiên** [`computeIfAbsent()`][computeIfAbsent] hơn [`putIfAbsent()`][putIfAbsent].

## Gộp value (merge)

Pattern [`computeIfAbsent()`][computeIfAbsent] hoạt động tốt nếu map của bạn có value là kết quả tổng hợp (aggregation) của các value khác. Nhưng có một hạn chế về cấu trúc hỗ trợ việc tổng hợp đó: nó phải **mutable**. [`ArrayList`][ArrayList] thì mutable, và đó là điều code bạn vừa viết làm: nó thêm value vào một [`ArrayList`][ArrayList].

Thay vì tạo list các từ, giả sử bạn cần tạo một **chuỗi nối** các từ. Class [`String`][String] ở đây được xem như phép tổng hợp các string khác, nhưng nó **không** phải container mutable: bạn không dùng được pattern [`computeIfAbsent()`][computeIfAbsent] cho việc đó.

Đây là lúc pattern [`merge()`][merge] tới giải cứu. Method [`merge()`][merge] nhận ba tham số:

- một key,
- một value mà bạn cần gắn với key đó,
- một remapping [`BiFunction`][BiFunction].

Nếu key không có trong map hoặc gắn với value null thì value được gắn với key đó. Remapping function **không** được gọi trong trường hợp này.

Ngược lại, nếu key đã gắn với một value non-null, remapping function được gọi với value hiện có và value mới truyền vào làm tham số. Nếu remapping function này trả về null thì key **bị xóa** khỏi map. Nếu không, value nó tạo ra được gắn với key đó.

Xem pattern [`merge()`][merge] hoạt động:

```java
List<String> strings = List.of("one", "two", "three", "four", "five", "six", "seven");
Map<Integer, String> map = new HashMap<>();
for (String word: strings) {
    int length = word.length();
    map.merge(length, word,
              (existingValue, newWord) -> existingValue + ", " + newWord);
}

map.forEach((key, value) -> IO.println(key + " :: " + value));
```

Ở đây, nếu key `length` không có trong map thì lời gọi [`merge()`][merge] chỉ thêm nó và gắn với `word`. Ngược lại, nếu key `length` đã có, bifunction được gọi với value hiện có và `word`. Kết quả của bifunction sau đó thay thế value hiện tại.

Kết quả:

```text
3 :: one, two, six
4 :: four, five
5 :: three, seven
```

Ở cả hai pattern [`computeIfAbsent()`][computeIfAbsent] và [`merge()`][merge], có thể bạn thắc mắc vì sao lambda được tạo lại nhận một tham số vốn đã luôn có sẵn trong ngữ cảnh của lambda đó, và có thể được capture từ ngữ cảnh. Câu trả lời: bạn nên **ưu tiên lambda không capture** hơn lambda có capture, vì lý do hiệu năng.

## Thực hành các phép toán trên Map

### In nội dung Map bằng BiConsumer

Bạn dùng method [`map.forEach()`][mapForEach] nhận một [`BiConsumer`][BiConsumer] để in nội dung một [`Map`][Map].

```java
Map<String, Integer> scores = Map.of(
   "Alice", 95,
   "Bob", 87,
   "Carol", 92,
   "David", 78
);

IO.println("Original Scores:");
scores.forEach((name, score) -> IO.println(name + ": " + score));
```

Kết quả:

```text
Original Scores:
Carol: 92
Alice: 95
Bob: 87
David: 78
```

### Thay thế value

Có nhiều method để thay value trong một [`Map`][Map].

```java
Map<String, Integer> scores = Map.of(
   "Alice", 95,
   "Bob", 87,
   "Carol", 92,
   "David", 78
);
// make scores modifiable
scores = new HashMap<>(scores);

// Replace operations
scores.replace("Alice", 97); // Replace existing value
scores.replace("Eve", 85);   // Won't replace (key doesn't exist)
scores.replace("Bob", 87, 90); // Replace only if current value matches

IO.println("");
IO.println("After specific replacements:");
scores.forEach((name, score) -> IO.println("   " + name + ": " + score));

// ReplaceAll with BiFunction - give everyone bonus points!
scores.replaceAll((name, score) -> score + 5);

IO.println("");
IO.println("After adding 5 bonus points to everyone:");
scores.forEach((name, score) -> IO.println("   " + name + ": " + score));
```

Kết quả:

```text
After specific replacements:
   David: 78
   Carol: 92
   Bob: 90
   Alice: 97
After adding 5 bonus points to everyone:
   David: 83
   Carol: 97
   Bob: 95
   Alice: 102
```

### Thực hành các phép compute

```java
Map<String, Integer> inventory = Map.of(
   "apples", 50,
   "bananas", 30,
   "oranges", 25);
// make inventory modifiable
inventory = new HashMap<>(inventory);

IO.println("Initial inventory:");
inventory.forEach((item, count) -> IO.println("   " + item + ": " + count));

// compute - always executes, can handle null values
inventory.compute("apples", (item, count) -> count != null ? count + 20 : 20);

// computeIfPresent - only if key exists and value is not null
inventory.computeIfPresent("bananas", (item, count) -> count - 5);

// computeIfAbsent - only if key doesn't exist or value is null
inventory.computeIfAbsent("grapes", item -> 15);

IO.println("");
IO.println("After compute operations:");
inventory.forEach((item, count) -> IO.println("   " + item + ": " + count));

// Try more examples
inventory.computeIfPresent("nonexistent", (item, count) -> 999); // Won't execute
inventory.computeIfAbsent("pears", item -> 12); // Will execute

IO.println("");
IO.println("Final inventory:");
inventory.forEach((item, count) -> IO.println("   " + item + ": " + count));
```

Kết quả:

```text
Initial inventory:
   apples: 50
   bananas: 30
   oranges: 25
After compute operations:
   apples: 70
   bananas: 25
   grapes: 15
   oranges: 25
Final inventory:
   bananas: 25
   oranges: 25
   pears: 12
   apples: 70
   grapes: 15
```

### Gom nhóm list bằng computeIfAbsent

Bạn dùng [`map.computeIfAbsent()`][computeIfAbsent] để gom nhóm phần tử của list.

```java
// Group words by their length
List<String> words = List.of(
   "java", "python", "go", "rust",
   "c++", "swift", "kotlin", "html",
   "css");
Map<Integer, List<String>> wordsByLength = new HashMap<>();

for (String word : words) {
   wordsByLength
      .computeIfAbsent(word.length(), _ -> new ArrayList<>()).add(word);
}

IO.println("Words grouped by length:");
wordsByLength.forEach((length, wordList) ->
IO.println("   " + length + " letters: " + wordList));
```

Kết quả:

```text
Words grouped by length:
2 letters: [go]
3 letters: [c++, css]
4 letters: [java, rust, html]
5 letters: [swift]
6 letters: [python, kotlin]
```

Ở ví dụ khác, bạn gom nhóm học sinh theo điểm xếp loại.

```java
// Group students by grade
String[] students =
   {"Alice-A", "Bob-B", "Carol-A", "David-C", "Eve-B", "Frank-A"};
Map<String, List<String>> studentsByGrade = new HashMap<>();

for (String student : students) {
   String[] parts = student.split("-");
   String name = parts[0];
   String grade = parts[1];

   studentsByGrade
      .computeIfAbsent(grade, _ -> new ArrayList<>()).add(name);
}

IO.println("");
IO.println("Students grouped by grade:");
studentsByGrade.forEach(
   (grade, studentList) ->
      IO.println("Grade " + grade + ": " + studentList));
```

Kết quả:

```text
Students grouped by grade:
Grade A: [Alice, Carol, Frank]
Grade B: [Bob, Eve]
Grade C: [David]
```

### Dùng merge

Method [`Map.merge()`][merge] gộp một cặp key/value cho trước vào một binding key đã có.

```java
// Character counting with merge
String text = "Duke loves Java!";
Map<Character, Integer> charCount = new HashMap<>();

for (char c : text.toCharArray()) {
   if (Character.isLetter(c)) { // only keep letters
      c = Character.toLowerCase(c);
      charCount.merge(c, 1, (oldCount, newCount) -> oldCount + newCount);
   }
}

IO.println("Character frequencies:");
charCount.forEach((character, count) ->
IO.println("'" + character + "': " + count));
```

Kết quả:

```text
Character frequencies:
'a': 2
's': 1
'd': 1
'e': 2
'u': 1
'v': 2
'j': 1
'k': 1
'l': 1
'o': 1
```

Bạn cũng có thể đếm tần suất từ trong một đoạn text.

```java
String[] sentence = {
   "the", "quick", "brown", "fox",
   "jumps", "over", "the", "lazy", "dog"};
Map<String, Integer> wordCount = new HashMap<>();

for (String word : sentence) {
   wordCount.merge(word, 1, Integer::sum);
}

IO.println("Word frequencies:");
wordCount.forEach(
   (word, count) ->
      IO.println("'" + word + "': " + count));
```

Kết quả:

```text
Word frequencies:
'over': 1
'the': 2
'quick': 1
'lazy': 1
'jumps': 1
'brown': 1
'dog': 1
'fox': 1
```

Bạn cũng dùng [`Map.merge()`][merge] để gộp cả hai map với nhau.

```java
Map<String, Integer> sales1 =
   Map.of("Product A", 100, "Product B", 150);
Map<String, Integer> sales2 =
   Map.of("Product B", 75, "Product C", 200);
Map<String, Integer> totalSales = new HashMap<>(sales1);

sales2.forEach(
   (product, amount) ->
      totalSales.merge(product, amount, Integer::sum));

IO.println("Combined sales:");
totalSales.forEach(
   (product, total) ->
      IO.println(product + ": " + total));
```

Kết quả:

```text
Combined sales:
Product A: 100
Product B: 225
Product C: 200
```

---

**Bài tập**

1. Viết bộ đếm từ bằng ba cách: `containsKey` + `put`, `getOrDefault` + `put`, và `merge(word, 1, Integer::sum)`. So sánh số dòng và mức dễ đọc.
2. `compute()` trả về value **mới**, `put()` trả về value **cũ**. Viết một ví nhỏ chứng minh, rồi tự nhắc mình vì sao lẫn hai cái này dễ sinh bug.
3. Dùng `merge()` với remapping function trả về `null` để hiện thực "giảm số lượng, hết thì xóa khỏi kho".
4. Đối chiếu: Go làm `m[k]++` được ngay vì zero value của `int` là 0. Java cần `merge` hoặc `getOrDefault`. Cách nào bạn thấy an toàn hơn khi value là type phức tạp?

[Iterable]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Iterable.html
[Map]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html
[ArrayList]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html
[String]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/String.html
[BiConsumer]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/function/BiConsumer.html
[Consumer]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/function/Consumer.html
[BiFunction]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/function/BiFunction.html
[Function]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/function/Function.html
[mapForEach]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#forEach(java.util.function.BiConsumer)
[iterForEach]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Iterable.html#forEach(java.util.function.Consumer)
[replace]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#replace(K,V)
[replace3]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#replace(K,V,V)
[replaceAll]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#replaceAll(java.util.function.BiFunction)
[compute]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#compute(K,java.util.function.BiFunction)
[computeIfPresent]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#computeIfPresent(K,java.util.function.BiFunction)
[computeIfAbsent]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#computeIfAbsent(K,java.util.function.Function)
[merge]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#merge(K,V,java.util.function.BiFunction)
[put]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#put(K,V)
[putIfAbsent]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#putIfAbsent(K,V)
