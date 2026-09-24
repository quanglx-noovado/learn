# Getting to Know the Collection Hierarchy

> Source: <https://dev.java/learn/api/collections-framework/organization/> — dev.java (last update: September 14, 2021)
> Raw English content, kept for reference alongside the Vietnamese translation.

## Avoiding Getting Lost in the Collection Hierarchy

The Collections Framework is divided in several hierarchies of interfaces and classes. The first one you need to understand is the following: the Collection interface hierarchy.

![The Collection Interface Hierarchy](https://dev.java/assets/images/collections-framework/01_interfaces-hierarchy.png)

The Collection Interface Hierarchy

Note that some interfaces have been omitted, which you will see later.

## The Iterable Interface

The first interface of this hierarchy is the [`Iterable`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Iterable.html) interface, and it is in fact not part of the Collections Framework. It is still worth mentioning here because it is the super interface of the [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) interface, and thus of all the interfaces of this hierarchy.

The [`Iterable`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Iterable.html) interface is an addition of Java SE 5 (2004). An object that implements [`Iterable`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Iterable.html) is an object that you can iterate over. It has been added in Java SE 5 along with the *for each* pattern of code.

You may already be familiar with this way of iterating over the elements of a [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html):

```java
Collection<String> collection = new ArrayList<>();
collection.add("Duke");
collection.add("loves");
collection.add("Java");

for (String element: collection) {
    IO.println(element);
}
```

Running this code produces the following result:

```
Duke
loves
Java
```

You may already know that you can iterate over any collection using this pattern, or any array. It turns out that in fact any instance of [`Iterable`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Iterable.html) may be used here.

To implement the [`Iterable`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Iterable.html) interface is really easy: all you need to do is provide an instance of another interface, [`Iterator`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html), that you are going to see in the following.

## Storing Elements in a Container with the Collection Interface

All the other interfaces are about storing elements in containers.

The two interfaces [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) and [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html) both share a common behavior, which is modeled by the [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) interface. The [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) interface models several operations on containers of elements. Without diving in the technical details (yet!), here is what you can do with a [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html):

- add or remove elements;
- test for the presence of a given element;
- ask for the number of elements contained, or if this collection is empty;
- clear this content.

Since a [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) is a set of elements, there are also set operations defined on the [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) interface:

- testing for the inclusion of a set in another set;
- union;
- intersection;
- complement.

Lastly, the [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) interface also models different ways of accessing its elements:

- you can iterate over the elements of a collection, through the use of an iterator;
- you can create a stream on these elements, that can be parallel.

Of course, all these operations are also available on [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) and [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html). One might ask: what makes the difference between a plain instance of [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) and an instance of [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html) or an instance of [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html)?

## Extending Collection with List

The difference between a [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) of elements and a [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) of elements, is that a [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) remembers in what order its elements have been added.

The first consequence is that if you iterate over the elements of a list, the first element you will get is the first that has been added. Then you will get the second one, and so on until all the elements have been seen. So the order you will iterate over the elements is always the same, and it is fixed by the order in which these elements have been added. You do not have this guarantee with a plain [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) nor for a [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html).

It turns out that some implementations of [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html) provided by the Collections Framework happen to always iterate over the elements in the same order. This may be an accidental effect. Unless you are using an implementation of [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html) that guarantees a stable encounter order, your code should not rely on this behavior.

There is a second consequence, maybe not as clear as the first one, which is that the elements of a list have an index. Querying a collection for its *first* element does not make sense. Querying a list for its first element does make sense, since a list does remember that.

How are those indexes handled? Well, once again, this is the responsibility of the implementation. The first role of an interface is to specify a behavior, not to tell how an implementation should achieve that.

As you will see, the [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) interface adds new operations to the [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) interface. As the elements of a list have an index, you can do the following with that index.

- Get an element at a specific index, or delete it
- Insert an element or replace an element at a specific position
- Get a range of elements between two indexes.

## Extending Collection with Set

The difference between a [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html) of elements and a [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) of elements, is that you cannot have duplicates in a [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html). You can have several instances of the same class that are equal in a [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html), or even the same instance more than once. This is not allowed in a [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html). How is this enforced is the responsibility of the implementation, you will see that later in this tutorial.

One of the consequences of this behavior, is that adding an element to a [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html) may fail.

Then you may ask yourself: can I have a container that prevents having duplicates, and in which elements have an index? The answer is not that simple. The Collections Framework gives you an implementation of [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html) with which you will iterate over the elements always in the same order, but these elements do not have an index, so this class does not implement [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html).

This difference in behavior does not bring any new operations in the [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html) interface.

## Sorting the elements of a Set with SortedSet and NavigableSet

The [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html) interface has itself two extensions: [`SortedSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html) and [`NavigableSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html).

The [`SortedSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html) interface maintains its elements sorted in ascending order. Once again, how this is enforced is the responsibility of the implementation, as you will see later.

To be able to sort them, a [`SortedSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html) needs to compare your elements. How can it achieve that? Well, there are two standard mechanisms defined in the Java language for that.

- Your elements may implement the [`Comparable`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Comparable.html) interface, and provide a [`compareTo()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Comparable.html#compareTo(T)) method
- You give a [`Comparator`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Comparator.html) to the [`SortedSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html) so that it can compare them.

Even if your elements are [`Comparable`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Comparable.html), you can still provide a [`Comparator`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Comparator.html) when building a [`SortedSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html). This may prove useful if you need to sort your elements in an order that is different from the one implemented in the [`compareTo()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Comparable.html#compareTo(T)) method.

What is the difference between sorting and ordering? A [`List`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html) keeps its elements in the order they have been added, and a [`SortedSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html) keeps them sorted. Sorting elements means that the first element you get while traversing a set will be the lowest one, in the sense of a given comparison logic. Ordering elements means that the order in which you added them in a list is kept throughout the life of this list. So the first element you get while traversing a list is the first that has been added to it.

The [`SortedSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html) adds several operations to [`Set`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html). Here is what you can do with a [`SortedSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html).

- You can get the lowest element of the set with the [`first()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html#first()) and [`getFirst()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html#getFirst()) methods.
- You can get the largest element of the set with the [`last()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html#last()) and [`getLast()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html#getLast()) methods.
- You can extract a [`headSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html#headSet(E)) and a [`tailSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html#tailSet(E)) of all the elements less than, or greater than or equal than a given element.

Iterating over the elements of a [`SortedSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html) will be made from the lowest element to the greatest.

The [`NavigableSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html) does not change the behavior of a [`SortedSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html). It adds several very useful operations on [`SortedSet`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html), among them the possibility to iterate over the elements in the descending order. You will see more details on that later.
