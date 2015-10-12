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
        self._function_ref = weakref.ref(function)
        self._function_code = function.__code__

    def _emission_opcodes(self, emit=None, context=None,
                          globals=globals, locals=locals):
        # TODO: Maybe use our own code here with MAKE_CLOSURE + LOAD_CLOSURE
        # to inject a closure, binding the context to our new function, and
        # enabling emit to then "ask" it for globals/locals/sym as/if needed.
        return [(byteplay.LOAD_CONST, emit or _emit),
                (byteplay.LOAD_CONST, context),
                (byteplay.LOAD_CONST, globals),
                (byteplay.CALL_FUNCTION, 0),
                (byteplay.LOAD_CONST, locals),
                (byteplay.CALL_FUNCTION, 0),
                (byteplay.CALL_FUNCTION, 3),
                (byteplay.POP_TOP, None)]

    def implement(self, **kwds):
        function = self._function_ref()
        if function is None:
            raise FunctionVanished(self)

        if not kwds:
            function.__code__ = self._function_code
            return

        # defaults
        kwds.setdefault('boundaries', ('start', 'finish'))

        # TODO: move elsewhere
        poi = dict()
        for point in ('symbols', 'lines', 'bytecode', 'boundaries'):
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
        editable = byteplay.Code.from_code(self._function_code)
        for opcode, oparg in editable.code:
            emit_before = emit_after = False
            if opcode == byteplay.SetLineno:
                if lineno == 0:
                    if poi['boundaries'] is True or 'start' in poi['boundaries']:
                        emit_before = True
                if poi['lines'] is True or oparg in poi['lines']:
                    emit_before = True
                lineno = oparg
            elif opcode == byteplay.RETURN_VALUE:
                if poi['boundaries'] is True or 'finish' in poi['boundaries']:
                    # about to leave the frame
                    emit_before = True
            elif opcode == byteplay.STORE_FAST:
                if poi['symbols'] is True or oparg in poi['symbols']:
                    # inspect before and after the call
                    emit_before = True
                    emit_after = True
            elif poi['bytecode'] is True or str(opcode) in poi['bytecode']:
                # TODO: need to provide top-of-stack
                emit_before = True

            # TODO: list of reason(s) needed for future filtering
            reason = (lineno, opcode, oparg)
            if emit_before:
                instructions.extend(self._emission_opcodes(context=reason))
            instructions.append((opcode, oparg))
            if emit_after:
                instructions.extend(self._emission_opcodes(context=reason))

        editable.code = instructions
        function.__code__ = editable.to_code()


def _emit(_context, _globals, _locals):
    from pprint import pprint as pp
    pp((_context, _locals))
