==========
Retrospect
==========

**Dynamic and adaptive logging AFTER the fact**

Classic logging expects perfect foresight, but everyone knows only hindsight
is 20/20!

Usage
-----

Install via pip, then::

    >>> def hello(a=1):
    >>>    a += 1
    >>>    b = 2
    >>>    print(a + b)
    >>>
    >>> import retrospect
    >>> r = retrospect.retrospect(hello)
    >>>
    >>> r.trace_lines().fun()
    {'a': 1}
    {'a': 2}
    {'a': 2, 'b': 2}
    4
    {'a': 2, 'b': 2}
    >>> r.trace_none().fun()
    4
