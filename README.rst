==========
Retrospect
==========

**Dynamic logging after the fact**

Classic logging expects perfect foresight, but only hindsight is 20/20!

Usage
-----

Install via pip, then enter a shell and define a function::

    >>> def hello(a, b=2):
    >>>     """docstring"""
    >>>     a = 1
    >>>     c = b * 2
    >>>     a = b = c = a * 2 + b * c
    >>>     print('output: a={} b={} c={}'.format(a, b, c))
    >>>     return a, b, c

Attach a ``retrospect.FunctionRetrospector`` to it::

    >>> import retrospect
    >>> retro = retrospect.FunctionRetrospector(hello)

Now you can start inspecting lines in real-time::

    >>> # emit at all line changes and function start/finish
    >>> retro.implement(lines=True)
    >>> hello(10)
    ((3, SetLineno, 3), {'a': 10, 'b': 2})
	((4, SetLineno, 4), {'a': 1, 'b': 2})
	((5, SetLineno, 5), {'a': 1, 'b': 2, 'c': 4})
	((6, SetLineno, 6), {'a': 10, 'b': 10, 'c': 10})
	output: a=10 b=10 c=10
	((7, SetLineno, 7), {'a': 10, 'b': 10, 'c': 10})
	((7, RETURN_VALUE, None), {'a': 10, 'b': 10, 'c': 10})

Or a specific set of lines::

    >>> # emit only at line 4
    >>> retro.implement(lines=[4], boundaries=False)
    >>> hello(20)
    ((4, SetLineno, 4), {'a': 1, 'b': 2})
    output: a=10 b=10 c=10

Or only on symbol changes::

    >>> # emit before/after STORE_FAST and at function start
    >>> retro.implement(symbols=True, boundaries='start')
    >>> hello(30)
    ((3, SetLineno, 3), {'a': 30, 'b': 2})
    ((3, STORE_FAST, 'a'), {'a': 30, 'b': 2})
    ((3, STORE_FAST, 'a'), {'a': 1, 'b': 2})
    ((4, STORE_FAST, 'c'), {'a': 1, 'b': 2})
    ((4, STORE_FAST, 'c'), {'a': 1, 'b': 2, 'c': 4})
    ((5, STORE_FAST, 'a'), {'a': 1, 'b': 2, 'c': 4})
    ((5, STORE_FAST, 'a'), {'a': 10, 'b': 2, 'c': 4})
    ((5, STORE_FAST, 'b'), {'a': 10, 'b': 2, 'c': 4})
    ((5, STORE_FAST, 'b'), {'a': 10, 'b': 10, 'c': 4})
    ((5, STORE_FAST, 'c'), {'a': 10, 'b': 10, 'c': 4})
    ((5, STORE_FAST, 'c'), {'a': 10, 'b': 10, 'c': 10})
    output: a=10 b=10 c=10

Or specific opcodes::

    >>> # emit before LOAD_CONST and RETURN_VALUE
    >>> retro.implement(bytecode=['LOAD_CONST'], boundaries='finish')
    >>> hello(40)
    ((3, LOAD_CONST, 1), {'a': 40, 'b': 2})
    ((4, LOAD_CONST, 2), {'a': 1, 'b': 2})
    ((5, LOAD_CONST, 2), {'a': 1, 'b': 2, 'c': 4})
    ((6, LOAD_CONST, 'output: a={} b={} c={}'), {'a': 10, 'b': 10, 'c': 10})
    output: a=10 b=10 c=10
    ((7, RETURN_VALUE, None), {'a': 10, 'b': 10, 'c': 10})

Or return to exact original::

    >>> retro.implement()
    >>> hello(50)
    output: a=10 b=10 c=10

Any of the above can be mixed as necessary, eg. lines=4 symbols=c
