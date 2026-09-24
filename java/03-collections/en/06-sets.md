# Extending Collection with Set, SortedSet and NavigableSet

> Source: <https://dev.java/learn/api/collections-framework/sets/> — dev.java (last update: September 14, 2021)
> Raw English content, kept for reference alongside the Vietnamese translation.

## Exploring the Set Interface

The [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html) interface does not bring any new methods to the [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) interface. The main implementation of [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html) the Collections Framework gives you is the [`HashSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/HashSet.html) class. Internally, a [`HashSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/HashSet.html) wraps an instance of [`HashMap`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/HashMap.html), a class that will be covered later, that acts as a delegate for [`HashSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/HashSet.html).

As you already saw, what a [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html) brings to a [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) is that it forbids duplicates. What you lose over the [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) interface is that your elements are stored in no particular order. There is very little chance that you will iterate over them in the same order as you added them to your set.

You can see this in the following example:

```java
List<String> strings = List.of("one", "two", "three", "four", "five", "six");
Set<String> set = new HashSet<>();
set.addAll(strings);
set.forEach(IO::println);
```

Running this code will produce the following:

```
six
four
one
two
three
five
```

Some implementations of [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html) always give you the same order when you iterate over their elements, but since this is not guaranteed, your code should not rely on that.

If you want to iterate over the elements in a particular, reproducible order, then you can use the [`LinkedHashSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/LinkedHashSet.html) implementation, that combines a set and an internal linked list.

## Extending Set with SortedSet

The first extension of [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html) is the [`SortedSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html) interface. The [`SortedSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html) interface keeps its elements sorted according to a certain comparison logic. The Collections Framework gives you one implementation of [`SortedSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html), called [`TreeSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/TreeSet.html).

A [`TreeSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/TreeSet.html) is an implementation that needs to compare the objects it contains. You can provide a [`Comparator`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Comparator.html) when you build a [`TreeSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/TreeSet.html), or you implement the [`Comparable`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Comparable.html) interface for the elements you put in the [`TreeSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/TreeSet.html). If you do both, then the [`Comparator`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Comparator.html) takes precedence.

The [`SortedSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html) interface adds new methods to [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html).

- [`first()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/TreeSet.html#first()) and [`last()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/TreeSet.html#last()) return the lowest and the largest elements of the set
- [`headSet(toElement)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/TreeSet.html#headSet(E)) and [`tailSet(fromElement)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/TreeSet.html#tailSet(E)) return you subsets containing the elements lower than `toElement` or greater than or equal to `fromElement`
- [`subSet(fromElement, toElement)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/TreeSet.html#subSet(E,E)) gives you a subset of the elements between `fromElement` and `toElement`.

The `toElement` and `fromElement` do not have to be elements of the main set. If they are, then `toElement` is not included in the result and `fromElement` is, following the usual convention.

Consider the following example:

```java
SortedSet<String> strings = new TreeSet<>(Set.of("a", "b", "c", "d", "e", "f"));
SortedSet<String> subSet = strings.subSet("aa", "d");
IO.println("sub set = " + subSet);
```

Running this code will give you the following:

```
sub set = [b, c]
```

The three subsets that these methods return are *views* on the main set. No copy is made, meaning that any change you make to these subsets will be reflected in the set, and the other way round.

You can remove or add elements to the main set through these subsets. There is one point you need to keep in mind though. These three subsets remember the limits on which they have been built. For consistency reasons, it is not legal to add an element through a subset outside its limits. For instance, if you take a [`headSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html#headSet(E)) and try to add an element greater than or equal to `toElement`, then you will get an [`IllegalArgumentException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/IllegalArgumentException.html).

## Extending SortedSet with NavigableSet

Java SE 6 saw the introduction of an extension of [`SortedSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html) with the addition of more methods. It turns out that the [`TreeSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/TreeSet.html) class was retrofitted to implement [`NavigableSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html). So you can use the same class for both interfaces.

Some methods are overloaded by [`NavigableSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html).

- [`headSet()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#headSet(E,boolean)), [`tailSet()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#tailSet(E,boolean)), and [`subSet()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#subSet(E,boolean,E,boolean)) may take a further `boolean` argument to specify whether the limits (`toElement` or `fromElement`) are to be included in the resulting subset.

Other methods have been added.

- [`ceiling(element)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#ceiling(E)), and [`floor(element)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#floor(E)) return the lowest element greater or equal, or the greatest element lesser or equal than the provided `element`. If there is no such element then `null` is returned.
- [`lower(element)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#lower(E)), and [`higher(element)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#higher(E)) return the greatest element less than, or the lowest element greater than the provided `element`. If there is no such element then `null` is returned.
- [`pollFirst()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#pollFirst()), and [`pollLast()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#pollLast()) return and remove the lowest or the greatest element of the set.

Furthermore, [`NavigableSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html) also allows you to iterate over its elements in descending order. There are two ways to do this.

- You can call [`descendingIterator()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#descendingIterator()): it gives you a regular [`Iterator`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html) that traverses the set in the descending order.
- You can also call [`descendingSet()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#descendingSet()). What you get in return is another [`NavigableSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html) that is a view on this set and that makes you think you have the same set, sorted in the reversed order.

The following example demonstrates this.

```java
NavigableSet<String> sortedStrings = new TreeSet<>(Set.of("a", "b", "c", "d", "e", "f"));
IO.println("sorted strings = " + sortedStrings);
NavigableSet<String> reversedStrings = sortedStrings.descendingSet();
IO.println("reversed strings = " + reversedStrings);
```

Running this code will give you the following:

```
sorted strings = [a, b, c, d, e, f]
reversed strings = [f, e, d, c, b, a]
```
