#!/usr/bin/env python


class GenericStruct(object):
    """Implements a generic data structure based on a list."""
    
    def __init__(self):
        self._generic = []
        self._name = 'Generic'
    
    def name(self):
        """Returns name of data structure."""
        return self._name

    def is_empty(self):
        """Returns True iff data structure is empty."""
        return self.size() == 0
    
    def size(self):
        """Returns number of elements in data structure."""
        return len(self._generic)


class Queue(GenericStruct):
    """Implements a standard FIFO queue."""

    def __init__(self):
        """
        Initialize the queue.
        Also binds self.add() and self.rm() to queue insertion and deletion.
        """
        super(Queue, self).__init__()
        self._queue = self._generic
        self._name = 'Queue'
        (self.add, self.rm) = (self.enqueue, self.dequeue)

    def enqueue(self, item, iterable=None):
        """Enqueue $item; if $iterable True, does enqueue_iterable($item)."""
        if iterable == None: self._queue.append(item)
        elif iterable == True: self.enqueue_iterable(item)
    
    def enqueue_iterable(self, item):
        """Attempt to iterate through $item and enqueue all."""
        try:
            self._queue.extend(item)
        except TypeError:
            print "Queue.enqueue_iterable() called on non-iterable."
    
    def dequeue(self):
        """Dequeue and return; raises IndexError if queue is empty."""
        if self.is_empty():
            raise IndexError('%s is empty' % self.name())
        else:   
            return self._queue.pop(0)


class Stack(GenericStruct):
    """Implements a standard LIFO stack."""

    def __init__(self):
        """
        Initialize the stack.
        Also binds self.add() and self.rm() to stack insertion and deletion.
        """
        super(Stack, self).__init__()
        self._stack = self._generic
        self._name = 'Stack'
        (self.add, self.rm) = (self.push, self.pop)
    
    def push(self, item, iterable=None):
        """Push $item; if $iterable True, does push_iterable($item)."""
        if iterable == None: self._stack.append(item)
        elif iterable == True: self.push_iterable(item)
    
    def push_iterable(self, item):
        """Attempt to iterate through $item and push all."""
        try:
            self._stack.extend(item)
        except TypeError:
            print 'Stack.push_iterable() called on non-iterable.'
    
    def pop(self):
        """Pop and return; raises IndexError if empty."""
        if self.is_empty():
            raise IndexError('%s is empty' % self.name())
        else:   
            return self._stack.pop()
