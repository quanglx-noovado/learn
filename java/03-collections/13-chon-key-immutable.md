# Chọn type immutable cho key của bạn

> Dịch từ [Choosing Immutable Types for Your Key](https://dev.java/learn/api/collections-framework/choosing-keys/) — dev.java.
> Trang gốc lặp lại class `Key` trong từng ví dụ (do dùng playground tự chứa). Ở đây class `Key` được viết **một lần**, các ví dụ sau dùng lại nó.

## Tránh dùng key mutable

Dùng key mutable là một **antipattern**, và bạn nên tuyệt đối tránh. Tác dụng phụ nếu bạn làm vậy rất tệ: bạn có thể khiến nội dung của map trở nên **không thể truy cập được**.

Rất dễ dựng một ví dụ để chứng minh. Đây là class `Key`, chỉ là một wrapper mutable quanh một [`String`][String]. Lưu ý là method [`equals()`][equals] và [`hashCode()`][hashCode] đã được override bằng đoạn code mà IDE của bạn có thể tự sinh ra.

```java
//
// !!!!! Đây là ví dụ về ANTIPATTERN !!!!!!
// !!! đừng làm thế này trong code production !!!
//
class Key {
    private String key;

    public Key(String key) {
        this.key = Objects.requireNonNull(key);
    }

    public String getKey() {
        return key;
    }

    public void setKey(String key) {
        this.key = Objects.requireNonNull(key);
    }

    @Override
    public String toString() {
        return key;
    }

    @Override
    public boolean equals(Object o) {
        return o instanceof Key otherKey && otherKey.key.equals(this.key);
    }

    @Override
    public int hashCode() {
        return key.hashCode();
    }
}
```

Bạn dùng wrapper này để tạo một map và đặt các cặp key-value vào:

```java
Key one = new Key("1");
Key two = new Key("2");

Map<Key, String> map = new HashMap<>();
map.put(one, "one");
map.put(two, "two");

IO.println("map.get(one) = " + map.get(one));
IO.println("map.get(two) = " + map.get(two));
```

Tới đây code vẫn OK và in ra:

```text
map.get(one) = one
map.get(two) = two
```

Điều gì xảy ra nếu ai đó **mutate** key của bạn? Câu trả lời phụ thuộc vào cách mutate. Bạn có thể thử các trường hợp trong ví dụ sau và xem gì xảy ra khi bạn lấy value về.

Trường hợp sau: bạn mutate một key đã có bằng một giá trị mới **không** tương ứng với key nào đang tồn tại.

```java
Key one = new Key("1");
Key two = new Key("2");

Map<Key, String> map = new HashMap<>();
map.put(one, "one");
map.put(two, "two");
IO.println("Map: " + map);

one.setKey("5");

IO.println("map.get(one) = " + map.get(one));
IO.println("map.get(two) = " + map.get(two));
IO.println("map.get(new Key(1)) = " + map.get(new Key("1")));
IO.println("map.get(new Key(2)) = " + map.get(new Key("2")));
IO.println("map.get(new Key(5)) = " + map.get(new Key("5")));
```

Kết quả như sau. Bạn **không còn lấy được** value từ key nữa, kể cả khi dùng chính object đó. Và lấy value từ một key mang giá trị gốc cũng thất bại. **Cặp key-value này đã mất.**

```text
map.get(one) = null
map.get(two) = two
map.get(new Key(1)) = null
map.get(new Key(2)) = two
map.get(new Key(5)) = null
```

Nếu bạn mutate key của mình bằng một giá trị đang được dùng cho một key khác đã tồn tại, kết quả lại khác.

```java
Key one = new Key("1");
Key two = new Key("2");

Map<Key, String> map = new HashMap<>();
map.put(one, "one");
map.put(two, "two");
IO.println("Map: " + map);

one.setKey("2");

IO.println("map.get(one) = " + map.get(one));
IO.println("map.get(two) = " + map.get(two));
IO.println("map.get(new Key(1)) = " + map.get(new Key("1")));
IO.println("map.get(new Key(2)) = " + map.get(new Key("2")));
```

Kết quả bây giờ như sau. Lấy value gắn với key đã bị mutate trả về value gắn với **key kia**. Và, như ví dụ trước, bạn không còn lấy được value gắn với key đã mutate nữa.

```text
Map: {1=one, 2=two}
map.get(one) = two
map.get(two) = two
map.get(new Key(1)) = null
map.get(new Key(2)) = two
```

Như bạn thấy, ngay cả trên một ví dụ rất đơn giản, mọi thứ có thể sai một cách kinh khủng: key đầu tiên không còn dùng được để truy cập đúng value, và bạn có thể **mất value** trong quá trình đó.

Nói ngắn gọn: nếu bạn thật sự không thể tránh dùng key mutable thì **đừng mutate chúng**. Nhưng lựa chọn tốt nhất là dùng key **unmodifiable**.

## Đào vào cấu trúc của HashSet

Có thể bạn thắc mắc vì sao lại nói về class [`HashSet`][HashSet] trong phần này? Hóa ra class [`HashSet`][HashSet] thực chất được xây trên một [`HashMap`][HashMap] nội bộ. Nên hai class chia sẻ vài đặc điểm chung.

Đây là code của method [`add(element)`][hsAdd] trong class [`HashSet`][HashSet]:

```java
private transient HashMap<E,Object> map;
private static final Object PRESENT = new Object();

public boolean add(E e) {
    return map.put(e, PRESENT)==null;
}
```

Bạn thấy rằng thực tế một hashset lưu object của bạn trong một hashmap (keyword `transient` không quan trọng ở đây). Object của bạn chính là **key** của hashmap này, còn value chỉ là một placeholder — một object không mang ý nghĩa gì.

Điểm quan trọng cần nhớ: nếu bạn **mutate** object sau khi đã thêm nó vào một set, bạn có thể gặp những bug rất lạ trong ứng dụng, và sẽ **rất khó sửa**.

Lấy lại ví dụ trước với class `Key` mutable. Lần này bạn thêm các instance của class này vào một set.

```java
Key one = new Key("1");
Key two = new Key("2");

Set<Key> set = new HashSet<>();
set.add(one);
set.add(two);

IO.println("set = " + set);

// Đừng bao giờ mutate một object sau khi đã thêm nó vào Set!
one.setKey("3");
IO.println("set.contains(one) = " + set.contains(one));
boolean addedOne = set.add(one);
IO.println("addedOne = " + addedOne);
IO.println("set = " + set);

List<Key> list = new ArrayList<>(set);
Key key0 = list.get(0);
Key key2 = list.get(2);

IO.println("key0 = " + key0);
IO.println("key2 = " + key2);
IO.println("key0 == key2 ? " + (key0 == key2));
```

Kết quả:

```text
set = [1, 2]
set.contains(one) = false
addedOne = true
set = [3, 2, 3]
key0 = 3
key2 = 3
key0 == key2 ? true
```

Bạn thấy phần tử đầu và phần tử cuối của set là **cùng một object**. Mutate một object sau khi đã thêm nó vào set có thể dẫn tới việc **cùng một object xuất hiện nhiều lần** trong một set. Nói đơn giản: đừng làm thế!

---

**Bài tập**

1. Viết lại class `Key` thành `record Key(String key)` — vì sao bug ở trên không còn khả năng xảy ra? (Gợi ý: field của record là `final`.)
2. Chạy ví dụ cuối và tự trả lời: vì sao `set.contains(one)` trả về `false` dù `one` **đang ở trong** set? (Gợi ý: bucket nào được tính từ `hashCode()`?)
3. Nếu bạn buộc phải dùng một class mutable làm key, hãy thử: `map.remove(key)` **trước khi** mutate, mutate, rồi `map.put(key, value)` lại. Viết một method helper làm đúng ba bước đó.
4. Đối chiếu với `01-basics`: đây chính là lý do bài tập "override `equals`/`hashCode` cho `NgonNgu`" quan trọng. Nếu `NgonNgu` có setter, `HashSet<NgonNgu>` của bạn có an toàn không?

[String]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/String.html
[HashSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/HashSet.html
[HashMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/HashMap.html
[equals]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Object.html#equals(java.lang.Object)
[hashCode]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Object.html#hashCode()
[hsAdd]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/HashSet.html#add(E)
