# encoding: utf8


from __future__ import print_function
from __future__ import absolute_import

import time
import weakref
import byteplay


class FunctionVanished(Exception):

    pass


class FunctionRetrospector(object):

    def __init__(self, function):
        self.function_ref = weakref.ref(function, self._dead_function_cb)
        self.function_code = function.__code__

    def _dead_function_cb(self, *args, **kwds):
        print('>>> _dead_function_cb: {} {}'.format(args, kwds))

    def emission_opcodes(self, *context):
        return [(byteplay.LOAD_CONST, emit),
                (byteplay.LOAD_CONST, locals),
                (byteplay.CALL_FUNCTION, 0),
                (byteplay.LOAD_CONST, globals),
                (byteplay.CALL_FUNCTION, 0),
                (byteplay.LOAD_CONST, context),
                (byteplay.CALL_FUNCTION, 3),
                (byteplay.POP_TOP, None)]

    def implement(self, **kwds):
        function = self.function_ref()
        if function is None:
            raise FunctionVanished(self)

        if not kwds:
            function.__code__ = self.function_code
            return

        key = str(time.time())

        # strategies
        poi = dict()
        for point in ('symbols', 'lines', 'bytecode'):
            # start with what the user sent else default empty
            interest = kwds.pop(point, None) or tuple()

            # do we care about something more specific than "everything"?
            if interest is not True:
                try:
                    # does it look like an int?
                    interest = (int(interest),)
                except (TypeError, ValueError) as e:
                    # does it look like a str?
                    if interest[0:0] == '':
                        interest = (interest,)
                # maybe copy
                interest = tuple(interest)

            poi[point] = interest

        lineno = 0
        instructions = list()
        editable = byteplay.Code.from_code(self.function_code)
        for opcode, oparg in editable.code:
            # TODO: provide context
            emit_before = emit_after = False

            if poi['bytecode'] is True or opcode in poi['bytecode']:
                # TODO: need to provide top-of-stack
                emit_before = True
            if opcode == byteplay.SetLineno:
                if poi['lines'] is True or oparg in poi['lines']:
                    emit_before = True
            if opcode == byteplay.RETURN_VALUE:
                # about to leave the frame
                emit_before = True
            if opcode == byteplay.STORE_FAST:
                if poi['symbols'] is True or oparg in poi['symbols']:
                    # inspect before and after the call
                    emit_before = True
                    emit_after = True

            if emit_before:
                instructions.extend(self.emission_opcodes(None))
            instructions.append((opcode, oparg))
            if emit_after:
                instructions.extend(self.emission_opcodes(None))

            if opcode == byteplay.SetLineno:
                lineno = oparg

        editable.code = instructions
        function.__code__ = editable.to_code()


class Retrospector(object):

    def __init__(self, fun):
        if not hasattr(fun, '__code__'):
            raise TypeError('function needs __code__')

        self.fun = fun

    def trace(self, **kwds):
        fun = self.fun
        key = frozenset(kwds.items()) or None
        tracer = cache.get(key)
        if tracer is None:
            tracer = cache[key] = cache[None].implement(**kwds)

        fun.__code__ = tracer.code
        return self


def retrospect(fun):
    fun = getattr(fun, '__func__', fun)
    rspect = getattr(fun, '__retrospect__', None)
    if rspect:
        return rspect

    rspect = fun.__retrospect__ = Retrospector(fun)
    return rspect


def emit(l, g, c=None):
    from pprint import pprint
    pprint(l)
