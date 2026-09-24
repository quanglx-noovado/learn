# Storing Elements in a Collection

> Source: <https://dev.java/learn/api/collections-framework/collection-interface/> — dev.java (last update: September 14, 2021)
> Raw English content, kept for reference alongside the Vietnamese translation.

## Exploring the Collection Interface

The first interface you need to know is the [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) interface. It models a plain collection, which can store elements and gives you different ways to retrieve them.

If you want to run the examples in this part, you need to know how to create a collection. We have not covered the [`ArrayList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html) class yet, we will do that later.

## Methods That Handle Individual Elements

Let us begin by storing and removing an element from a collection. The two methods involved are [`add()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#add(E)) and [`remove()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#remove(java.lang.Object)).

- [`add(element)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#add(E)): adds an element to the collection. This method returns a `boolean` that is `false` if the operation failed. Failing is a little subtle, as when this method returns, whether with `true` or `false`, then the element must be in the collection. So a further call to [`contains()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#contains(java.lang.Object)) with this element as an argument must return `true`. So if your implementation of [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) decides not to add the element that is not already in this [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html), then you should throw an exception. The [`add(element)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#add(E)) method gives the exceptions you should throw.
  - If your implementation is non-modifiable, then this exception must be an [`UnsupportedOperationException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/UnsupportedOperationException.html).
  - If it does not allow null values, then it must be a [`NullPointerException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/NullPointerException.html).
  - If the element cannot be added because it is of a wrong type, then it must throw a [`ClassCastException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/ClassCastException.html).
  - If your implementation refuses this element based on its properties, then you should throw an [`IllegalArgumentException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/IllegalArgumentException.html).
- [`remove(element)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#remove(java.lang.Object)): removes the given element from the collection. This method also returns a `boolean`, because the operation may fail. A remove may fail, for instance, when the item requested for removal is not present in the collection.

You can run the following example. Here, you create an instance of the [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) interface using the [`ArrayList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html) implementation. The generics used tells the Java compiler that you want to store [`String`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/String.html) objects in this collection. [`ArrayList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html) is not the only implementation of [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) you may use. More on that later.

```java
Collection<String> strings = new ArrayList<>();
strings.add("one");
strings.add("two");
IO.println("strings = " + strings);
strings.remove("one");
IO.println("strings = " + strings);
```

Running the previous code should print the following:

```
strings = [one, two]
strings = [two]
```

You can check for the presence of an element in a collection with the [`contains()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#contains(java.lang.Object)) method. Note that you can check the presence of any type of element. For instance, it is valid to check for the presence of a `User` object in a collection of [`String`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/String.html). This may seem odd, since there is no chance that this check returns `true`, but it is allowed by the compiler. If you are using an IDE to test this code, your IDE may warn about testing for the presence of a `User` object in a collection of [`String`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/String.html) objects. Note that the implementation may choose to throw a [`ClassCastException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/ClassCastException.html).

```java
Collection<String> strings = new ArrayList<>();
strings.add("one");
strings.add("two");
if (strings.contains("one")) {
    IO.println("one is here");
}
if (!strings.contains("three")) {
    IO.println("three is not here");
}

record User(String name) {}

User rebecca = new User("Rebecca");
if (!strings.contains(rebecca)) {
    IO.println("Rebecca is not here");
}
```

Running this code produces the following:

```
one is here
three is not here
Rebecca is not here
```

## Methods That Handle Other Collections

This first set of methods you saw allows you to handle individual elements. There are also methods that take another [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) as a parameter.

There are four such methods: [`containsAll()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#containsAll(java.util.Collection)), [`addAll()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#addAll(java.util.Collection)), [`removeAll()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#removeAll(java.util.Collection)) and [`retainAll()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#retainAll(java.util.Collection)). They define the four fundamental operations on a set of objects.

- [`containsAll()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#containsAll(java.util.Collection)): defines the inclusion.
- [`addAll()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#addAll(java.util.Collection)): defines the union.
- [`removeAll()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#removeAll(java.util.Collection)): defines the complement.
- [`retainAll()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#retainAll(java.util.Collection)): defines the intersection.

The first one is really simple: [`containsAll()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#containsAll(java.util.Collection)) takes another collection as an argument and returns `true` if all the elements of the other collections are contained in this collection. The collection passed as an argument does not have to be the same type as this collection: it is legal to ask if a collection of [`String`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/String.html), of type [`Collection<String>`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) is contained in a collection of `User`, of type [`Collection<User>`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html). The result can even be `true` if the collection of [`String`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/String.html) is empty.

Note that an implementation of [`containsAll()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#containsAll(java.util.Collection)) may throw an exception in two cases.

1. It may throw a [`ClassCastException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/ClassCastException.html) if an element of the other collection is not compatible with this collection.
2. It may throw a [`NullPointerException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/NullPointerException.html) if an element of the other collection is `null` and this collection does not permit `null` elements.
3. It may also throw a [`NullPointerException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/NullPointerException.html) if the other collection is `null`.

Here is an example of the use of this method:

```java
Collection<String> strings = new ArrayList<>();
strings.add("one");
strings.add("two");
strings.add("three");

Collection<String> first = new ArrayList<>();
first.add("one");
first.add("two");

Collection<String> second = new ArrayList<>();
second.add("one");
second.add("four");

IO.println("Is first contained in strings? " + strings.containsAll(first));
IO.println("Is second contained in strings? " + strings.containsAll(second));
```

Running this code produces the following:

```
Is first contained in strings? true
Is second contained in strings? false
```

The second one is [`addAll()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#addAll(java.util.Collection)). It allows you to add all the elements of a given collection to this collection. As with the [`add()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#add(E)) method, this may fail for some elements in some cases. This method returns `true` if this collection has been modified by this call. This is an important point to understand: getting a `true` value does not mean that all the elements of the other collection have been added; it means that at least one has been added.

You can see [`addAll()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#addAll(java.util.Collection)) in action in the following example:

```java
Collection<String> strings = new ArrayList<>();
strings.add("one");
strings.add("two");
strings.add("three");
strings.add("four");

Collection<String> first = new ArrayList<>();
first.add("one");
first.add("four");

boolean hasChanged = strings.addAll(first);

IO.println("Has strings changed? " + hasChanged);
IO.println("strings = " + strings);
```

Running this code produces the following result:

```
Has strings changed? true
strings = [one, two, three, one, four]
```

You need to be aware that running this code will produce a different result if you change the implementation of [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html). This result stands for [`ArrayList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html), but as you can see in the following example, it is not the same for [`HashSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/HashSet.html). You will learn more about [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html) in the section [Extending Collection with Set, SortedSet and NavigableSet](https://dev.java/learn/api/collections-framework/sets/).

```java
Collection<String> strings = new HashSet<>();
strings.add("one");
strings.add("two");
strings.add("three");
strings.add("four");

Collection<String> first = new ArrayList<>();
first.add("one");
first.add("four");

boolean hasChanged = strings.addAll(first);

IO.println("Has strings changed? " + hasChanged);
IO.println("strings = " + strings);
```

Running this code produces the following result:

```
Has strings changed? false
strings = [four, one, two, three]
```

The third one is [`removeAll()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#removeAll(java.util.Collection)). It removes all the elements of this collection that are contained in the other collection. Just as it is the case for [`contains()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#contains(java.lang.Object)) or [`remove()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#remove(java.lang.Object)), the other collection can be defined on any type; it does not have to be compatible with the one of this collection.

You can see [`removeAll()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#removeAll(java.util.Collection)) in action in the following example:

```java
Collection<String> strings = new ArrayList<>();
strings.add("one");
strings.add("two");
strings.add("three");

Collection<String> toBeRemoved = new ArrayList<>();
toBeRemoved.add("one");
toBeRemoved.add("four");

boolean hasChanged = strings.removeAll(toBeRemoved);

IO.println("Has strings changed? " + hasChanged);
IO.println("strings = " + strings);
```

Running this code produces the following result:

```
Has strings changed? true
strings = [two, three]
```

The last one is [`retainAll()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#retainAll(java.util.Collection)). This operation retains only the elements from this collection that are contained in the other collection; all the others are removed. Once again, as it is the case for [`contains()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#contains(java.lang.Object)) or [`remove()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#remove(java.lang.Object)), the other collection can be defined on any type.

You can see [`retainAll()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#retainAll(java.util.Collection)) in action in the following example:

```java
Collection<String> strings = new ArrayList<>();
strings.add("one");
strings.add("two");
strings.add("three");

Collection<String> toBeRetained = new ArrayList<>();
toBeRetained.add("one");
toBeRetained.add("four");

boolean hasChanged = strings.retainAll(toBeRetained);

IO.println("Has strings changed? " + hasChanged);
IO.println("strings = " + strings);
```

Running this code produces the following result:

```
Has strings changed? true
strings = [one]
```

## Methods That Handle The Collection Itself

Then the last batch of methods deals with the collection itself.

You have two methods to check the content of a collection.

- [`size()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#size()): Returns the number of elements in a collection, as an `int`.
- [`isEmpty()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#isEmpty()): Tells you if the given collection is empty or not.

```java
Collection<String> strings = new ArrayList<>();
strings.add("one");
strings.add("two");
if (!strings.isEmpty()) {
    IO.println("Indeed strings is not empty");
}
IO.println("The number of elements in strings is " + strings.size());
```

Running this code produces the following:

```
Indeed strings is not empty
The number of elements in strings is 2
```

Then you can delete the content of a collection by simply calling [`clear()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#clear()) on it.

```java
Collection<String> strings = new ArrayList<>();
strings.add("one");
strings.add("two");
IO.println("The number of elements in strings is " + strings.size());
strings.clear();
IO.println("After clearing it, this number is now " + strings.size());
```

Running this code produces the following:

```
The number of elements in strings is 2
After clearing it, this number is now 0
```

## Getting an Array of the Elements of a Collection

Even if storing your elements in a collection may make more sense in your application than putting them in an array, there are still cases where getting them in an array is something you will need.

The [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) interface gives you three patterns to get the elements of a collection in an array, in the form of three overloads of a [`toArray()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#toArray()) method.

The first one is a plain [`toArray()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#toArray()) call, with no arguments. This returns your elements in an array of plain objects.

This may not be what you need. If you have a [`Collection<String>`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html), what you could prefer is an array of [`String`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/String.html). You can still cast `Object[]` to `String[]`, but there is no guarantee that this cast will not fail at runtime. If you need type safety, then you can call either of the following methods.

- [`toArray(T[] a)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#toArray(T%5B%5D)) returns an array of `T`: `T[]`.
- [`toArray(IntFunction<T[]> generator)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#toArray(java.util.function.IntFunction)), returns the same type, with a different syntax.

What are the differences between the last two patterns? The first one is readability. Creating an instance of [`IntFunction<T[]>`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/function/IntFunction.html) may look weird at first, but writing it with a method reference is really a no brainer.

Here is the first pattern. In this first pattern, you need to pass an array of the corresponding type.

```java
Collection<String> strings = new ArrayList<>(); // You have 4 elements in that collection
strings.add("one");
strings.add("two");
strings.add("three");
strings.add("four");

String[] tabString1 = strings.toArray(new String[] {}); // you can pass an empty array
IO.println("Tab string 1: " + Arrays.toString(tabString1));
String[] tabString2 = strings.toArray(new String[4]);   // or an array of the right size
IO.println("Tab string 2: " + Arrays.toString(tabString2));
```

Running this code produces the following result:

```
Tab string 1: [one, two, three, four]
Tab string 2: [one, two, three, four]
```

What is the use of this array passed as an argument? If it is big enough to hold all the elements of the collection, then these elements will be copied in the array, and it will be returned. If there is more room in the array than needed, then first unused cell of the array will be set to null. If the array you pass is too small, then a new array of the exact right size is created to hold the elements of the collection.

Here is this pattern in action:

```java
Collection<String> strings = List.of("one", "two");

String[] largerTab = {"three", "three", "three", "I", "was", "there"};
IO.println("largerTab = " + Arrays.toString(largerTab));

String[] result = strings.toArray(largerTab);
IO.println("result = " + Arrays.toString(result));

IO.println("Same arrays? " + (result == largerTab));
```

Running the previous code will give you:

```
largerTab = [three, three, three, I, was, there]
result = [one, two, null, I, was, there]
Same arrays? true
```

You can see that the array was copied in the first cells of the argument array, and `null` was added right after it, thus leaving the last elements of this array untouched. The returned array is the same array as the one you gave as an argument, with a different content.

Here is a second example, with a zero-length array:

```java
Collection<String> strings = List.of("one", "two");

String[] zeroLengthTab = {};
String[] result = strings.toArray(zeroLengthTab);

IO.println("zeroLengthTab = " + Arrays.toString(zeroLengthTab));
IO.println("result = " + Arrays.toString(result));
```

Running this code gives you the following result:

```
zeroLengthTab = []
result = [one, two]
```

A new array has been created in this case.

The second pattern is written using a constructor method reference to implement [`IntFunction<T[]>`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/function/IntFunction.html):

```java
Collection<String> strings = new ArrayList<>(); // You have 4 elements in that collection
strings.add("one");
strings.add("two");
strings.add("three");
strings.add("four");

String[] tabString3 = strings.toArray(String[]::new);
IO.println("Tab string 3: " + Arrays.toString(tabString3));
```

Running this code produces the following result:

```
Tab string 3: [one, two, three, four]
```

In that case, a zero-length array of the right type is created with this function, and this method then calls to [`toArray()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#toArray()) with this array passed as an argument.

This pattern of code was added in JDK 8 to improve the readability of the [`toArray()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#toArray()) calls.

## Filtering out Elements of a Collection with a Predicate

Java SE 8 added a new feature the [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) interface: the possibility to filter out elements of a collection with a predicate.

Suppose you have a [`List<String>`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) and you need to remove all the null strings, the empty strings and the strings longer than 5 characters. In Java SE 7 and earlier, you can use the [`Iterator.remove()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html#remove()) method to do that, calling it in an `if` statement. You will see this pattern along with the [`Iterator`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html) interface. With [`removeIf()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#removeIf(java.util.function.Predicate)), your code becomes much simpler:

```java
Predicate<String> isNull = Objects::isNull;
Predicate<String> isEmpty = String::isEmpty;
Predicate<String> isNullOrEmpty = isNull.or(isEmpty);

Collection<String> strings = new ArrayList<>();
strings.add(null);
strings.add("");
strings.add("one");
strings.add("two");
strings.add("");
strings.add("three");
strings.add(null);

IO.println("strings = " + strings);
strings.removeIf(isNullOrEmpty);
IO.println("filtered strings = " + strings);
```

Running this code produces the following result:

```
strings = [null, , one, two, , three, null]
filtered strings = [one, two, three]
```

Once again, using this method will greatly improve the readability and expressiveness of your application code.

## Choosing an Implementation for the Collection Interface

In all these examples, we used [`ArrayList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html) to implement the [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) interface.

The fact is: the Collections Framework does not provide a direct implementation of the [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) interface. [`ArrayList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html) implements [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html), and because [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) extends [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html), it also implements [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html).

If you decide to use the [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) interface to model the collections in your application, then choosing [`ArrayList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html) as your default implementation is your best choice, most of the time. You will see more discussions on the right implementation to choose later in this tutorial.
