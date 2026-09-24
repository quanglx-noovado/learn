# Iterating over the Elements of a Collection

> Source: <https://dev.java/learn/api/collections-framework/iterating/> — dev.java (last update: September 14, 2021)
> Raw English content, kept for reference alongside the Vietnamese translation.

## Using the for-each Pattern

Your simplest choice to iterate over the elements of a collection is to use the for-each pattern.

```java
Collection<String> strings = List.of("one", "two", "three");

for (String element: strings) {
    IO.println(element);
}
```

Running this code produces the following result:

```
one
two
three
```

This pattern is very efficient, as long as you only need to read the elements of your collection. The [`Iterator`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html) pattern allows to remove some of the elements of your collection while you are iterating over them. If you need to do that, then you want to use the [`Iterator`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html) pattern.

## Using an Iterator on a Collection

Iterating over the elements of a collection uses a special object, an instance of the [`Iterator`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html) interface. You can get an [`Iterator`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html) object from any extension of the [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) interface. The [`iterator()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#iterator()) method is defined on the [`Iterable`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Iterable.html) interface, extended by the [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) interface, and further extended by all the interfaces of the collection hierarchy.

Iterating over the elements of a collection using this object is a two-step process.

1. First you need to check if there are more elements to be visited with the [`hasNext()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html#hasNext()) method
2. Then you can advance to the next element with the [`next()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html#next()) method.

If you call the [`next()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html#next()) method but there are no more elements in the collection, you will get a [`NoSuchElementException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NoSuchElementException.html). Calling [`hasNext()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html#hasNext()) is not mandatory, it is there to help you to make sure that there is indeed a next element.

Here is the pattern:

```java
Collection<String> strings = List.of("one", "two", "three", "four");
for (Iterator<String> iterator = strings.iterator(); iterator.hasNext();) {
    String element = iterator.next();
    if (element.length() == 3) {
        IO.println(element);
    }
}
```

This code produces the following result:

```
one
two
```

The [`Iterator`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html) interface has a third method: [`remove()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html#remove()). Calling this method removes the current element from the collection. There are cases though where this method is not supported, it will throw an [`UnsupportedOperationException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/UnsupportedOperationException.html). Quite obviously, calling [`remove()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html#remove()) on an immutable collection cannot work, so this is one of the cases. The implementation of [`Iterator`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html) you get from [`ArrayList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html), [`LinkedList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/LinkedList.html) and [`HashSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/HashSet.html) all support this remove operation.

## Updating a Collection While Iterating over It

If you happen to modify the content of a collection while iterating over it, you may get a [`ConcurrentModificationException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ConcurrentModificationException.html). Getting this exception may be a little confusing, because this exception is also used in concurrent programming. In the context of the Collections Framework, you may get it without touching multithreaded programming.

The following code throws a [`ConcurrentModificationException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ConcurrentModificationException.html).

```java
Collection<String> strings = new ArrayList<>();
strings.add("one");
strings.add("two");
strings.add("three");

Iterator<String> iterator = strings.iterator();
while (iterator.hasNext()) {

    String element = iterator.next();
    strings.remove(element);
}
```

If what you need is to remove the elements of a collection that satisfy a given criteria, you may use the [`removeIf()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#removeIf(java.util.function.Predicate)) method.

## Implementing the Iterable Interface

Now that you saw what an iterator is in the Collections Framework, you can create a simple implementation of the [`Iterable`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Iterable.html) interface.

Suppose you need to create a `Range` class that models a range of integers between two limits. All you need to do is iterate from the first integer to the last one.

You can implement the [`Iterable`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Iterable.html) interface with a record, a feature introduced in Java SE 16:

```java
// lower bound is included, upper bound is excluded
record Range(int start, int end) implements Iterable<Integer> {

    @Override
    public Iterator<Integer> iterator() {
        return new Iterator<>() {
            private int index = start;

            @Override
            public boolean hasNext() {
                return index < end;
            }

            @Override
            public Integer next() {
                if (index >= end) {
                    throw new NoSuchElementException("" + index);
                }
                int currentIndex = index;
                index++;
                return currentIndex;
            }
        };
    }
}
```

You can do the same with a plain class, in case your application does not support Java SE 16 yet. Note that the code of the implementation of [`Iterator`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html) is exactly the same.

```java
class Range implements Iterable<Integer> {

    private final int start;
    private final int end;

    public Range(int start, int end) {
        this.start = start;
        this.end = end;
    }

    @Override
    public Iterator<Integer> iterator() {
        return new Iterator<>() {
            private int index = start;

            @Override
            public boolean hasNext() {
                return index < end;
            }

            @Override
            public Integer next() {
                if (index >= end) {
                    throw new NoSuchElementException("" + index);
                }
                int currentIndex = index;
                index++;
                return currentIndex;
            }
        };
    }
}
```

In both cases, you can use an instance of `Range` in a for-each statement, since it implements [`Iterable`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Iterable.html):

```java
record Range(int start, int end) implements Iterable<Integer> {

    @Override
    public Iterator<Integer> iterator() {
        return new Iterator<>() {
            private int index = start;

            @Override
            public boolean hasNext() {
                return index < end;
            }

            @Override
            public Integer next() {
                if (index >= end) {
                    throw new NoSuchElementException("" + index);
                }
                int currentIndex = index;
                index++;
                return currentIndex;
            }
        };
    }
}

for (int i : new Range(0, 5)) {
    IO.println("i = " + i);
}
```

Running this code gives you the following result:

```
i = 0
i = 1
i = 2
i = 3
i = 4
```
