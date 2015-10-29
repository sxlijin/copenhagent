#!/usr/bin/env python


class GenericStruct(object):
    """Implements a generic data structure based on a list."""
    
    def __init__(self):
        self._generic = []
        self._name = 'Generic'
        self._mutate_index = float('nan')
    
    def name(self):
        """Returns name of data structure."""
        return self._name

    def is_empty(self):
        """Returns True iff data structure is empty."""
        return self.size() == 0
    
    def size(self):
        """Returns number of elements in data structure."""
        return len(self._generic)

    def add(self, item, iterable=None):
        """
        Add $item to the data structure.
        If $iterable True, instead calls add_iterable($item).
        """
        if iterable == None: self._generic.append(item)
        elif iterable == True: self.add_iterable(item)
    
    def add_iterable(self, item):
        """Attempt to iterate through $item and add all."""
        try:
            self._generic.extend(item)
        except TypeError:
            print "%s.add_iterable() called on non-iterable." % self.name()
    
    def rm(self):
        """
        Remove from data structure and return the removed element.
        Raises IndexError if data structure is empty.
        """
        try:
            return self._generic.pop(self._mutate_index)
        except IndexError:
            raise IndexError('%s is empty' % self.name())

    def peek(self):
        """
        Return the item that is next to be removed.
        Raises IndexError if data structure is empty.
        """
        try:
            return self._generic[self._mutate_index]
        except IndexError:
            raise IndexError('%s is empty' % self.name())



class Queue(GenericStruct):
    """Implements a standard FIFO queue."""

    def __init__(self):
        """
        Initialize the queue.
        Also binds queue-specific operation names to insertion and deletion.
        """
        super(Queue, self).__init__()
        self._name = 'Queue'
        self._mutate_index = 0
        
        self.enqueue = self.add
        self.enqueue_iterable = self.add_iterable
        self.dequeue = self.rm


class Stack(GenericStruct):
    """Implements a standard LIFO stack."""

    def __init__(self):
        """
        Initialize the stack.
        Also binds stack-specific operation names to insertion and deletion.
        """
        super(Stack, self).__init__()
        self._name = 'Stack'
        self._mutate_index = -1

        self.push = self.add
        self.push_iterable = self.add_iterable
        self.pop = self.rm


class PriorityQueue(GenericStruct):
    """Implements a heap with an optional key() function."""
    
    def __init__(self, key=None):
        """Initialize the heap."""
        super(PriorityQueue, self).__init__()
        self._heap = self._generic
        self._name = 'PriorityQueue'
        self.key = key

        self.heapq = __import__('heapq')

    def add(self, item, iterable=None):
        """
        Add $item to the PriorityQueue.
        If $iterable True, instead calls add_iterable($item).
        """
        if iterable == None: 
            if self.key != None: item = (key(item), item)
            self.heapq.heappush(self._heap, item)
        elif iterable == True: 
            self.add_iterable(item)
                        
    def add_iterable(self, item):
        """Attempt to iterate through $item and add all."""
        try:
            if self.size() < len(item):
                self._heap.extend(item)
                self.heapq.heapify(item)
            else:
                for i in item: self.heapq.heappush(self._heap, i)
        except TypeError:
            print "%s.add_iterable() called on non-iterable." % self.name()

    def rm(self):
        """
        Remove smallest element from the PriorityQueue and return it.
        Raises IndexError if PriorityQueue is empty.
        """
        try:
            if self.key == None:
                return self.heapq.heappop(self._heap)
            else:
                return self.heapq.heappop(self._heap)[1]
        except IndexError:
            raise IndexError('Heap is empty.')

    def peek(self):
        """
        Return the smallest element in the PriorityQueue.
        Raises IndexError if PriorityQueue is empty.
        """
        try:
            if self.key == None:
                return self._heap[0]
            else:
                return self._heap[0][1]
        except IndexError:
            raise IndexError('Heap is empty.')
