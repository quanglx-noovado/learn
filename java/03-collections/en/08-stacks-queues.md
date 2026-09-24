# Storing Elements in Stacks and Queues

> Source: <https://dev.java/learn/api/collections-framework/stacks-queues/> — dev.java (last update: September 14, 2021)
> Raw English content, kept for reference alongside the Vietnamese translation.

## Finding Your Way in the Queue Hierarchy

Java SE 5 saw the addition of a new interface in the Collections Framework: the [`Queue`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html) interface, further extended in Java SE 6 by the [`Deque`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html) interface. The [`Queue`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html) interface is an extension of the [`Collection`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html) interface.

![The Queue Interface Hierarchy](https://dev.java/assets/images/collections-framework/02_queue-hierarchy.png)

The Queue Interface Hierarchy

## Pushing, Popping and Peeking

The stack and queue structures are classic data structures in computing. Stacks are also called LIFO stacks, where LIFO stands for Last In, First Out. Queues are known as FIFO: First In First Out.

These structures are very simple and give you three main operations.

- *push(element)*: adds an element to the queue, or the stack
- *pop()*: removes an element from the stack, that is, the youngest element added
- *poll()*: removes an element from the queue, that is, the oldest element added
- *peek()*: allows you to see the element you will get with a *pop()* or a *poll()*, but without removing it from the queue of the stack.

There are two reasons to explain the success of these structures in computing. The first one is their simplicity. Even in the very early days of computing, implementing these was simple. The second one is their usefulness. Many algorithms use stacks for their implementations.

## Modeling Queues and Stacks

The Collections Framework gives you two interfaces to model queues and stacks:

- the [`Queue`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html) interface models a queue;
- the [`Deque`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html) interface models a double ended queue (thus the name). You can push, pop, poll and peek elements on both the tail and the head of a [`Deque`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html), making it both a queue and a stack.

Stacks and queues are also widely used in concurrent programming. These interfaces are further extended by more interfaces, adding methods useful in this field. These interfaces, [`BlockingQueue`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/concurrent/BlockingQueue.html), [`BlockingDeque`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/concurrent/BlockingDeque.html) and [`TransferQueue`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/concurrent/TransferQueue.html), are at the intersection of the Collections Framework and concurrent programming in Java, which is outside the scope of this tutorial.

Both the [`Queue`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html) and the [`Deque`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html) interfaces add behavior to these three fundamental operations to deal with two corner cases.

- A queue may be full and not able to accept more elements
- A queue may be empty and cannot return an element with a *pop*, *poll*, nor the *peek* operation.

In fact this question needs to be answered: how does an implementation should behave in these two cases?

## Modeling FIFO Queues with Queue

The [`Queue`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html) interface gives you two ways of dealing with these corner cases. An exception can be thrown, or a special value can be returned.

Here is the table of the methods [`Queue`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html) gives you.

| Operation | Method | Behavior when the queue is full or empty |
| --- | --- | --- |
| push | [`add(element)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html#add(E)) | throws an [`IllegalStateException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/IllegalStateException.html) |
|  | [`offer(element)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html#offer(E)) | returns `false` |
| poll | [`remove()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html#remove()) | throws a [`NoSuchElementException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NoSuchElementException.html) |
|  | [`poll()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html#poll()) | returns `null` |
| peek | [`element()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html#element()) | throws a [`NoSuchElementException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NoSuchElementException.html) |
|  | [`peek()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html#peek()) | returns `null` |

## Modeling LIFO Stacks and FIFO Queues with Deque

Java SE 6 added the [`Deque`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html) interface as an extension of the [`Queue`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html) interface. Of course, the methods defined in [`Queue`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html) are still available in [`Deque`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html), but [`Deque`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html) brought a new naming convention. So these methods have been duplicated in [`Deque`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html), following this new naming convention.

Here is the table of the methods defined in [`Deque`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html) for the FIFO operations.

| FIFO Operation | Method | Behavior when the queue is full or empty |
| --- | --- | --- |
| push | [`addLast(element)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#addLast(E)) | throws an [`IllegalStateException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/IllegalStateException.html) |
|  | [`offerLast(element)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#offerLast(E)) | returns `false` |
| poll | [`removeFirst()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#removeFirst()) | throws a [`NoSuchElementException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NoSuchElementException.html) |
|  | [`pollFirst()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#pollFirst()) | returns `null` |
| peek | [`getFirst()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#getFirst()) | throws a [`NoSuchElementException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NoSuchElementException.html) |
|  | [`peekFirst()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#peekFirst()) | returns `null` |

And here is the table of the methods defined in [`Deque`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html) for the LIFO operations.

| LIFO Operation | Method | Behavior when the queue is full or empty |
| --- | --- | --- |
| push | [`addFirst(element)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#addFirst(E)) | throws an [`IllegalStateException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/IllegalStateException.html) |
|  | [`offerFirst(element)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#offerFirst(E)) | returns `false` |
| pop | [`removeFirst()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#removeFirst()) | throws a [`NoSuchElementException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NoSuchElementException.html) |
|  | [`pollFirst()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#pollFirst()) | returns `null` |
| peek | [`getFirst()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#getFirst()) | throws a [`NoSuchElementException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NoSuchElementException.html) |
|  | [`peekFirst()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#peekFirst()) | returns `null` |

The [`Deque`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html) naming convention is straightforward and is the same as the one followed in the [`Queue`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html) interface. There is one difference though: the peek operations are named [`getFirst()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#getFirst()) and [`getLast()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#getLast()) in [`Deque`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html), and [`element()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html#element()) in [`Queue`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html).

Moreover, [`Deque`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html) also defines the methods you would expect in any queue or stack class:

- [`push(element)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#push(E)): adds the given `element` to the head of the double ended queue. This method throws an [`IllegalStateException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/IllegalStateException.html) if the double ended queue cannot accept the element.
- [`pop()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#pop()): removes and returns the element at the head of the double ended queue. This method throws a [`NoSuchElementException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NoSuchElementException.html) if there is no element to pop.
- [`poll()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#poll()): does the same at the head of the double ended queue. This method returns `null` if there is no element to poll.
- [`peek()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#peek()): shows you the element at the head of the double ended queue. This method returns `null` if there is no element to peek.

## Implementing Queue and Deque

The Collections Framework gives you three implementations of [`Queue`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html) and [`Deque`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html), outside the concurrent programming space:

- [`ArrayDeque`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayDeque.html): which implements both. This implementation is backed by an array. The capacity of this class automatically grows as elements are added. So this implementation always accepts new elements.
- [`LinkedList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/LinkedList.html): which also implements both. This implementation is backed by a linked list, making the access to its first and last element very efficient. A [`LinkedList`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/LinkedList.html) will always accept new elements.
- [`PriorityQueue`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/PriorityQueue.html): that only implements [`Queue`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html). This queue is based on a priority heap that keeps its elements sorted by their natural order or by an order specified by a [`Comparator`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Comparator.html). The head of this queue is always the least element of the queue with respect to the specified ordering. The capacity of this class automatically grows as elements are added. Inserting objects that do not implement [`Comparable`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Comparable.html) will throw a [`ClassCastException`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/ClassCastException.html).

## Staying Away from the Stack Class

It may seem tempting to use the [`Stack`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Stack.html) class offered by the JDK. This class is simple to use and to understand. It has the three expected methods [`push(element)`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Stack.html#push(E)), [`pop()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Stack.html#pop()), and [`peek()`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Stack.html#peek()), and seeing this class referenced in your code makes it perfectly readable.

It turns out that this class is an extension of the [`Vector`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Vector.html) class. Back in the days before the Collections Framework was introduced, [`Vector`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Vector.html) was your best choice to work with a list. Although [`Vector`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Vector.html) is not deprecated, its usage is discouraged. So is the usage of the [`Stack`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Stack.html) class.

The [`Vector`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Vector.html) class is thread safe, and so is [`Stack`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Stack.html). If you do not need the thread safety, then you can safely replace its usage with [`Deque`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html) and [`ArrayDeque`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayDeque.html). If what you need is a thread-safe stack, then you should explore the implementations of the [`BlockingQueue`](https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/concurrent/BlockingQueue.html) interface.
