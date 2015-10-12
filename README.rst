==========
Retrospect
==========

**Dynamic logging after the fact**

Classic logging expects perfect foresight, but only hindsight is 20/20!

Usage
-----

Install via pip, then enter in a shell:

.. code-block:: python

    def hello(a, b=2):
        """docstring"""
        a = 1
        c = b * 2
        a = b = c = a * 2 + b * c
        print('output: a={} b={} c={}'.format(a, b, c))
        return a, b, c

    import retrospect
    retro = retrospect.FunctionRetrospector(hello)

Now you can start inspecting lines in real-time:

.. code-block:: python

    >>> retro.implement(lines=True)
    >>> hello(10)
    ((3, SetLineno, 3), {'a': 10, 'b': 2})
    ((4, SetLineno, 4), {'a': 1, 'b': 2})
    ((5, SetLineno, 5), {'a': 1, 'b': 2, 'c': 4})
    ((6, SetLineno, 6), {'a': 10, 'b': 10, 'c': 10})
    output: a=10 b=10 c=10
    ((7, SetLineno, 7), {'a': 10, 'b': 10, 'c': 10})
    ((7, RETURN_VALUE, None), {'a': 10, 'b': 10, 'c': 10})

Or a specific set of lines:

.. code-block:: python

    >>> retro.implement(lines=[4], boundaries=False)
    >>> hello(20)
    ((4, SetLineno, 4), {'a': 1, 'b': 2})
    output: a=10 b=10 c=10

Or only on symbol changes:

.. code-block:: python

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

Or specific opcodes:

.. code-block:: python

    >>> retro.implement(opcodes=['LOAD_CONST'], boundaries='finish')
    >>> hello(40)
    ((3, LOAD_CONST, 1), {'a': 40, 'b': 2})
    ((4, LOAD_CONST, 2), {'a': 1, 'b': 2})
    ((5, LOAD_CONST, 2), {'a': 1, 'b': 2, 'c': 4})
    ((6, LOAD_CONST, 'output: a={} b={} c={}'), {'a': 10, 'b': 10, 'c': 10})
    output: a=10 b=10 c=10
    ((7, RETURN_VALUE, None), {'a': 10, 'b': 10, 'c': 10})

Or return to **exact** original:

.. code-block:: python

    >>> retro.implement()
    >>> hello(50)
    output: a=10 b=10 c=10

Any of the above can be mixed as necessary, eg. ``lines=True, symbols="c"``
