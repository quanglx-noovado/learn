# Creating and Processing Data with the Collections Factory Methods

> Source: <https://dev.java/learn/api/collections-framework/factory-methods/> — dev.java (last update: September 14, 2021)
> Raw English content, kept for reference alongside the Vietnamese translation.

## Creating Unmodifiable Collections

Java SE 9 saw the addition of a set of factory methods to the [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) and [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html) interfaces to create lists and sets. The pattern is very simple: just call the [`List.of()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#of(E...)) or [`Set.of()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html#of(E...)) static method, pass the elements of your list and set, and that's it.

```java
List<String> stringList = List.of("one", "two", "three");
IO.println("String list: " + stringList);
Set<String> stringSet = Set.of("one", "two", "three");
IO.println("String set : " + stringSet);
```

Running this code produces the following result:

```
String list: [one, two, three]
String set : [one, three, two]
```

Several points are worth noting though.

The implementation you get in return may vary with the number of elements you put in your list or set. None of them is [`ArrayList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html) or [`HashSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/HashSet.html); your code should not rely on anything beyond the basic [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) and [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html) interfaces.

Both the list and the set you get are unmodifiable structures. You cannot add or modify elements in them, and you cannot modify these elements. If the objects of these structures are mutable, you can still mutate them.

These structures do not accept null values. If you try to add a `null` value in such a list or set, you will get an exception.

The [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html) interface does not allow duplicates: this is what a set is about. Because it would not make sense to create such a set with duplicate values, it is assumed that writing such a code is a bug. So you will get an exception if you try to do that.

The implementations you get are [`Serializable`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/io/Serializable.html).

These `of()` methods are commonly referred to as *convenience factory methods for collections*.

## Getting an Unmodifiable Copy of a Collection

Following the success of the convenience factory methods for collections, another set of convenience methods have been added in Java SE 10 to create unmodifiable copies of collections.

There are two of them: [`List.copyOf()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#copyOf(java.util.Collection)) and [`Set.copyOf()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html#copyOf(java.util.Collection)). They both follow the same pattern:

```java
Collection<String> strings = Arrays.asList("one", "two", "three");

List<String> list = List.copyOf(strings);
IO.println("List: "  + list);
Set<String> set   = Set.copyOf(strings);
IO.println("Set:  "  + set);
```

Running this code produces the following result:

```
List: [one, two, three]
Set:  [two, one, three]
```

In all cases, the collection you need to copy should not be null and should not contain any null elements. If this collection has duplicates, only one of these elements will be kept in the case of [`Set.copyOf()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html#copyOf(java.util.Collection)).

What you get in return is an unmodifiable copy of the collection passed as an argument. So modifying this collection will not be reflected in the list or set you get as a copy.

None of the implementations you get accept `null` values. If you try to copy a collection with `null` values, you will get a [`NullPointerException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/NullPointerException.html).

## Wrapping an Array in a List

The Collections Framework has a class called [`Arrays`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Arrays.html) with about 200 methods to handle arrays. Most of them are implementing various algorithms on arrays, like sorting, merging, searching, and are not covered in this section.

There is one though that is worth mentioning: [`Arrays.asList()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Arrays.html#asList(T...)). This method takes a vararg as an argument and returns a [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) of the elements you passed, preserving their order. This method is not part of the *convenience factory methods for collections* but is still very useful.

This [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) acts as a wrapper on an array, and behaves in the same way, which maybe a little confusing at first. Once you have set the size of an array, you cannot change it. It means that you cannot add an element to an existing array, nor can you remove an element from it. All you can do is replace an existing element with another one, possibly null.

The [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) you get by calling [`Arrays.asList()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Arrays.html#asList(T...)) does exactly this.

- If you try to add or remove an element, you will get an [`UnsupportedOperationException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/UnsupportedOperationException.html), whether you do that directly or through the iterator.
- Replacing existing elements is OK.

So this list is not unmodifiable, but there are restrictions on how you can change it.

## Using the Collections Factory Class to Process a Collection

The Collections Framework comes with another factory class: [`Collections`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html), with a set of methods to manipulate collections and their content. There are about 70 methods in this class, it would be tedious so examine them one-by-one, so let us present a subset of them.

### Extracting the Minimum or the Maximum from a Collection

The [`Collections`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html) class gives you two methods for that: the [`min()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html#min(java.util.Collection)) and the [`max()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html#max(java.util.Collection)). Both methods take the collection as an argument from which the min or the max is extracted. Both methods have an overload that also takes a comparator as a further argument.

If no comparator is provided then the elements of the collection must implement [`Comparable`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Comparable.html). If not, a [`ClassCastException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/ClassCastException.html) will be raised. If a comparator is provided, then it will be used to get the min or the max, whether the elements of the collection are comparable or not.

Getting the min or the max of an empty collection with this method will raise a [`NoSuchElementException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NoSuchElementException.html).

### Finding a Sublist in a List

Two methods locate a given sublist in a bigger list:

- [`indexOfSublist(List<?> source, List<?> target)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html#indexOfSubList(java.util.List,java.util.List)): returns the first index of the first element of the `target` list in the `source` list, or -1 if it does not exist;
- [`lastIndexOfSublist(List<?> source, List<?> target)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html#lastIndexOfSubList(java.util.List,java.util.List)): return the last of these indexes.

### Changing the Order of the Elements of a List

Several methods can change the order of the elements of a list:

- [`sort()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html#sort(java.util.List)) sorts the list in place. This method may take a comparator as an argument. As usual, if no comparator is provided, then the elements of the list must be comparable. If a comparator is provided, then it will be used to compare the elements. Starting with Java SE 8, you should favor the [`sort()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#sort(java.util.Comparator)) method from the [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) interface.
- [`shuffle()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html#shuffle(java.util.List)) randomly shuffles the elements of the provided list. You can provide your instance of [`Random`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Random.html) if you need a random shuffling that you can repeat.
- [`rotate()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html#rotate(java.util.List,int)) rotates the elements of the list. After a rotation the element at index 0 will be found at index 1 and so on. The last elements will be moved to the first place of the list. You can combine [`subList()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#subList(int,int)) and [`rotate()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html#rotate(java.util.List,int)) to remove an element at a given index and to insert it in another place in the list. This can be done with the following code:

```java
List<String> strings = Arrays.asList("0", "1", "2", "3", "4");
IO.println(strings);
int fromIndex = 1;
int toIndex = 4;
Collections.rotate(strings.subList(fromIndex, toIndex), -1);
IO.println(strings);
```

The result is the following:

```
[0, 1, 2, 3, 4]
[0, 2, 3, 1, 4]
```

The element at index `fromIndex` has been removed from its place, the list has been reorganized accordingly, and the element has been inserted at index `toIndex - 1`.

- [`reverse()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html#reverse(java.util.List)): reverse the order of the elements of the list.
- [`swap()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html#swap(java.util.List,int,int)): swaps two elements from the list.

### Wrapping a Collection in an Unmodifiable Collection

The [`Collections`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html) factory class gives you several methods to create unmodifiable wrappers for your collections or maps. The content of the structure is not duplicated; what you get is a wrapper around your structure. All the attempts to modify it will raise exceptions.

All these methods start with `unmodifiable`, followed by the name of the type of your structure. For instance, to create an unmodifiable wrapper of a list, you can call:

```java
List<String> strings = Arrays.asList("0", "1", "2", "3", "4");
IO.println("Strings: " + strings);
List<String> unmodifiableStrings = Collections.unmodifiableList(strings);
IO.println("Unmodifiable strings: " + strings);
```

Running this code produces the following result:

```
Strings: [0, 1, 2, 3, 4]
Unmodifiable strings: [0, 1, 2, 3, 4]
```

Just a word of warning: it is not possible to modify the collection returned by these factory methods. But this wrapper is backed by the collection you passed to the factory method. So if this collection is modifiable, and you modify it, this modification will be reflected in the wrapper. Let us see that in the following code:

```java
List<String> strings = new ArrayList<>(Arrays.asList("0", "1", "2", "3", "4"));
List<String> unmodifiableStrings = Collections.unmodifiableList(strings);
IO.println(unmodifiableStrings);
strings.add("5");
IO.println(unmodifiableStrings);
```

Running this example will give you the following:

```
[0, 1, 2, 3, 4]
[0, 1, 2, 3, 4, 5]
```

If you plan to create an unmodifiable collection using this pattern, defensively copying it first may be a safe precaution.

### Wrapping a Collection in a Synchronized Collection

In the same way as you can create unmodifiable wrappers for your maps and collections, the [`Collections`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html) factory class can create synchronized wrappers for them. The patterns follow the same naming convention as the names for methods that create unmodifiable wrappers: the methods are called `synchronized` followed by [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html), [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html), [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html), etc...

There are two precautions you need to follow.

- All the accesses to your collection should be made through the wrapper you get
- Traversing your collection with an iterator or a stream should be synchronized by the calling code on the list itself.

Not following these rules will expose your code to race conditions.

Synchronizing collections using the [`Collections`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html) factory methods may not be your best choice. The Java Util Concurrent framework (in the [`java.util.concurrent`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/concurrent/package-summary.html) package) has better solutions to offer.
