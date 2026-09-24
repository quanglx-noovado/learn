# Extending Collection with List

> Source: <https://dev.java/learn/api/collections-framework/lists/> — dev.java (last update: September 14, 2021)
> Raw English content, kept for reference alongside the Vietnamese translation.

## Exploring the List Interface

If you are eager to practice the most common list operations on some real code, you can jump directly to the end of this page: [Practicing List Operations](https://dev.java/learn/api/collections-framework/lists/#practicing)

The [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) interface brings two new functionalities to plain collections.

- This order in which you iterate over the elements of a list is always the same, and it respects the order in which the elements have been added to this list.
- The elements of a list have an index.

## Choosing your Implementation of the List Interface

While the [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) interface has no specific implementation in the Collections Framework (it relies on the implementations of its sub-interfaces), the [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) interface has 2: [`ArrayList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html) and [`LinkedList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/LinkedList.html). As you may guess, the first one is built on an internal array, and the second on a doubly-linked list.

Is one of these implementations better than the other? If you are not sure which one to choose, then your best choice is probably [`ArrayList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html).

What was true for linked lists when computing was invented in the 60's does not hold anymore, and the capacity of linked lists to outperform arrays on insertion and deletion operations is greatly diminished by modern hardware, CPU caches, and pointer chasing. Iterating over the elements of an [`ArrayList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html) is much faster than over the elements of a [`LinkedList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/LinkedList.html), mainly due to pointer chasing and CPU cache misses.

There are still cases where a linked list is faster than an array. A doubly-linked list can access its first and last element faster than an [`ArrayList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html) can. This is the main use case that makes [`LinkedList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/LinkedList.html) better than [`ArrayList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html). So if your application needs a Last In, First Out (LIFO, covered later in this tutorial) stack, or a First In, First Out (FIFO, also covered later) waiting queue, and does not use any other [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) method, then choosing a [`LinkedList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/LinkedList.html) is probably a better choice than an [`ArrayList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html). The [`ArrayDeque`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayDeque.html) may also be an interesting implementation, which does not accept null values.

On the other hand, if you plan to iterate through the elements of your list, or to access them randomly by their index, then the [`ArrayList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html) is probably your best bet.

You can find a more in-depth discussion of the differences between [`ArrayList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html) and [`LinkedList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/LinkedList.html) at the end of this chapter, on this page: [Choosing the Right Implementation Between ArrayList and LinkedList](https://dev.java/learn/api/collections-framework/arraylist-vs-linkedlist/).

## Accessing the Elements Using an Index

The [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) interface brings several methods to the [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) interface, that deal with indexes.

### Accessing a Single Object

- [`add(index, element)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#add(int,E)): inserts the given object at the `index`, adjusting the index of the remaining elements, if any
- [`get(index)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#get(int)): returns the object at the given `index`
- [`set(index, element)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#set(int,E)): replaces the element at the given index with the new element
- [`remove(index)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#remove(int)): removes the element at the given `index`, adjusting the index of the remaining elements.

Calling these methods works only for valid indexes. If the given index is not valid then an [`IndexOutOfBoundsException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/IndexOutOfBoundsException.html) exception will be thrown.

### Finding the Index of an Object

The methods [`indexOf(element)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#indexOf(java.lang.Object)) and [`lastIndexOf(element)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#lastIndexOf(java.lang.Object)) return the index of the given element in the list, or -1 if the element is not found.

### Getting a SubList

The [`subList(start, end)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#subList(int,int)) returns a list consisting of the elements between indexes `start` and `end - 1`. If the indexes are invalid then an [`IndexOutOfBoundsException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/IndexOutOfBoundsException.html) exception will be thrown.

Note that the returned list is a view on the main list. Thus, any modification operation on the sublist is reflected on the main list and vice-versa.

For instance, you can clear a portion of the content of a list with the following pattern:

```java
List<String> strings = new ArrayList<>(List.of("0", "1", "2", "3", "4", "5"));
IO.println(strings);
strings.subList(2, 5).clear();
IO.println(strings);
```

Running this code gives you the following result:

```
[0, 1, 2, 3, 4, 5]
[0, 1, 5]
```

### Inserting a Collection

The last pattern of this list is about inserting a collection at a given index: [`addAll(int index, Collection collection)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#addAll(int,java.util.Collection)).

```java
List<String> strings = new ArrayList<>(List.of("0", "1", "5"));
List<String> toBeInserted = List.of("2", "3", "4");
IO.println("Strings: " + strings);
IO.println("To be inserted: " + toBeInserted);
IO.println("Inserting at index 2");
strings.addAll(2, toBeInserted);
IO.println("Strings: " + strings);
```

Running this code gives you the following result:

```
Strings: [0, 1, 5]
To be inserted: [2, 3, 4]
Inserting at index 2
Strings: [0, 1, 2, 3, 4, 5]
```

## Sorting the Elements of a List

A list keeps its elements in a known order. This is the main difference with a plain collection. So it makes sense to sort the elements of a list. This is the reason why a [`sort()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#sort(java.util.Comparator)) method has been added to the [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) interface in JDK 8.

In Java SE 7 and earlier, you could sort the elements of your [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) by calling [`Collections.sort()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html#sort(java.util.List)) and pass your list as an argument, along with a comparator if needed.

Starting with Java SE 8 you can call [`sort()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#sort(java.util.Comparator)) directly on your list and pass your comparator as an argument. There is no overload of this method that does not take any argument. Calling it with a null comparator will assume that the elements of your [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) implement [`Comparable`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Comparable.html), and you will get a [`ClassCastException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/ClassCastException.html) if this is not the case.

If you do not like calling methods will null arguments (and you are right!), you can still call it with [`Comparator.naturalOrder()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Comparator.html#naturalOrder()) to achieve the same result.

## Iterating over the Elements of a List

The [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) interface gives you one more way to iterate over its elements with the [`ListIterator`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html). You can get such an iterator by calling [`listIterator()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#listIterator()). You can call this method with no argument, or pass an integer index to it. In that case, the iteration will start at this index.

The [`ListIterator`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html) interface extends the regular [`Iterator`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html) that you already know. It adds several methods to it.

- [`hasPrevious()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#hasPrevious()) and [`previous()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#previous()): to iterate in the descending order rather than the ascending order
- [`nextIndex()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#nextIndex()) and [`previousIndex()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#previousIndex()): to get the index of the element that will be returned by the next [`next()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#next()) call, or the next [`previous()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#previous()) call
- [`add(element)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#add(E)): to insert the given element in the list. It is inserted right before the element returned by the next call to [`next()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#next()), if any, and after the element returned by a call to [`previous()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#previous()), if any. If the list is empty, then the element is simply added to this list. This insertion has two consequences. First, a subsequent call to [`previous()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#previous()) will return the inserted element. A subsequent call to [`next()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#next()) is unaffected. And second, the value returned by a subsequent call to [`nextIndex()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#nextIndex()) or [`previousIndex()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#previousIndex()) is increased by one.
- [`set(element)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#set(E)): to update the last element returned by [`next()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#next()) or [`previous()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#previous()). If neither of these methods have been called on this iterator then an [`IllegalStateException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/IllegalStateException.html) is raised.

Let us see this [`set()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#set(E)) method in action:

```java
List<String> numbers = Arrays.asList("one", "two", "three");
for (ListIterator<String> iterator = numbers.listIterator(); iterator.hasNext();) {
    String nextElement = iterator.next();
    if (Objects.equals(nextElement, "two")) {
        iterator.set("2");
    }
}
IO.println("numbers = " + numbers);
```

Running this code will give you the following result:

```
numbers = [one, 2, three]
```

## Practicing List Operations

### Creating and Populating a List

You can create lists and add elements to them with the following pattern. Note that you will see more patterns in the following examples.

```java
List<String> fruits = new ArrayList<>();
fruits.add("apple");
fruits.add("banana");
fruits.add("cherry");
fruits.add("date");
IO.println("Fruits: " + fruits);
```

Running the previous code prints the following.

```
Fruits: [apple, banana, cherry, date]
```

### Accessing the First and the Last Element of a List

Lists give you direct access to their first and last element.

```java
var fruits = List.of("apple", "banana", "cherry", "date");
// make the list modifiable
fruits = new ArrayList<>(fruits);

// Accessing the first and last element
IO.println("First element: " + fruits.getFirst());
IO.println("Last element:  " + fruits.getLast());

// Modifying the first and last element
IO.println("Adding apricot at the beginning of the list");
fruits.addFirst("apricot");
IO.println("Adding mango at the end of the list");
fruits.addLast("mango");
IO.println("First element: " + fruits.getFirst());
IO.println("Last element:  " + fruits.getLast());
```

Running the previous code prints the following.

```
First element: apple
Last element:  date
Adding apricot at the beginning of the list
Adding mango at the end of the list
First element: apricot
Last element:  mango
```

### Accessing an Element by its Index

Lists give you access to their elements using their indexes, as you can see on the following example.

```java
var fruits = List.of("apple", "banana", "cherry", "date");
// make the list modifiable
fruits = new ArrayList<>(fruits);

// Accessing elements by index
IO.println("Element at index 0: " + fruits.get(0));
IO.println("Element at index 1: " + fruits.get(1));
IO.println("Last element: " + fruits.get(fruits.size() - 1));

// Insert at specific position
fruits.add(1, "blueberry");
IO.println("After inserting blueberry at index 1: " + fruits);

// Replace element
fruits.set(2, "blackberry");
IO.println("After replacing index 2 with blackberry: " + fruits);
```

Running the previous code prints the following.

```
Element at index 0: apple
Element at index 1: banana
Last element: date
After inserting blueberry at index 1: [apple, blueberry, banana, cherry, date]
After replacing index 2 with blackberry: [apple, blueberry, blackberry, cherry, date]
```

If the element you are searching is present several times in the list, then you can use the following pattern to find all of them.

```java
var fruits = List.of("apple", "banana", "cherry", "banana", "banana", "apricot");

// It gives you the first index
var index = fruits.indexOf("banana");
var nextIndex = 0;
IO.println("First banana is at index " + index);
while (nextIndex != -1) {
   // search again, starting at index + 1
   nextIndex = fruits.subList(index + 1, fruits.size()).indexOf("banana");
   if (nextIndex != -1) {
      index = index + 1 + nextIndex;
      IO.println("Next banana is at index " + index);
   } else {
      IO.println("No more banana");
   }
}
```

Running the previous code prints the following.

```
First banana is at index 1
Next banana is at index 3
Next banana is at index 4
No more banana
```

### Working with Indexes of an Element

You can find the index of a given element in a list, as you can see in the following example.

```java
var fruits = List.of("apple", "banana", "cherry", "date");
// make the list modifiable
fruits = new ArrayList<>(fruits);

// Finding indexes
IO.println("Index of 'cherry': " + fruits.indexOf("cherry"));
IO.println("Index of 'grape' (not found): " + fruits.indexOf("grape"));

// Remove elements by index
fruits.remove(0);  // Remove by index
IO.println("After removals: " + fruits);
```

Running the previous code prints the following.

```
Index of 'cherry': 2
Index of 'grape' (not found): -1
After removals: [banana, cherry, date]
```

### Working with Sublists

You can get a sublist from a list. Note that this sublist is a modifiable view on the original list.

```java
var fruits = List.of("apple", "banana", "cherry", "date");
// make the list modifiable
fruits = new ArrayList<>(fruits);

// Getting a sublist
var middleFruits = fruits.subList(1, 4);
IO.println("Sublist (indices 1-3): " + middleFruits);

// Adding an element in a sublist
middleFruits.add("apricot");
IO.println("Middle fruits: " + middleFruits);
IO.println("A sublist is a modifiable view on the original list");
IO.println("Fruits: " + fruits);

middleFruits.clear();
IO.println("Fruits after clearing the sublist: " + fruits);
```

Running the previous code prints the following.

```
Sublist (indices 1-3): [banana, cherry, date]
Middle fruits: [banana, cherry, date, apricot]
A sublist is a modifiable view on the original list
Fruits: [apple, banana, cherry, date, apricot]
Fruits after clearing the sublist: [apple]
```

### Sorting a List

You can sort a list by passing a [`Comparator`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Comparator.html).

```java
var fruits = List.of("peach", "plum", "cherry", "apple", "date");
// make the list modifiable
fruits = new ArrayList<>(fruits);

fruits.sort(Comparator.naturalOrder());
IO.println("Fruits, sorted ascending order: " + fruits);

fruits.sort(Comparator.<String>naturalOrder().reversed());
IO.println("Fruits, sorted descending order: " + fruits);
```

Running the previous code prints the following.

```
Fruits, sorted ascending order: [apple, cherry, date, peach, plum]
Fruits, sorted descending order: [plum, peach, date, cherry, apple]
```

### Reversing a List

You can reorder a list in the reverse order.

```java
var fruits = List.of("peach", "plum", "cherry", "apple", "date");
// make the list modifiable
fruits = new ArrayList<>(fruits);

IO.println("Original order: " + fruits);
var reversed = fruits.reversed();
IO.println("Reverse order: " + reversed);
IO.println("Adding an apricot at index 2");
fruits.add(2, "apricot");
IO.println("Original order: " + fruits);
IO.println("Reverse order: " + reversed);
```

Running the previous code prints the following. Remember that what [`List.reversed()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SequencedCollection.html#reversed()) returns is a view on the original list.

```
Original order: [peach, plum, cherry, apple, date]
Reverse order: [date, apple, cherry, plum, peach]
Adding an apricot at index 2
Original order: [peach, plum, apricot, cherry, apple, date]
Reverse order: [date, apple, cherry, apricot, plum, peach]
```
