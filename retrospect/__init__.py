# encoding: utf8


from __future__ import print_function
from __future__ import absolute_import

import time
import types
from collections import namedtuple

from . import dis


CODE_ARGS = (
    'argcount',
    'nlocals',
    'stacksize',
    'flags',
    'codestring',
    'constants',
    'names',
    'varnames',
    'filename',
    'name',
    'firstlineno',
    'lnotab',
    'freevars',
    'cellvars',
    )

CODE_ATTRS = (
    'co_argcount',
    'co_nlocals',
    'co_stacksize',
    'co_flags',
    'co_code',
    'co_consts',
    'co_names',
    'co_varnames',
    'co_filename',
    'co_name',
    'co_firstlineno',
    'co_lnotab',
    'co_freevars',
    'co_cellvars',
    )


class defaultproperty(object):
    """
    @property-like descriptor with lower precedence than instance.__dict__

    @property defines __set__ (data-descriptor), taking precedence over
    instance.__dict__, but we want the opposite (non-data-descriptor)
    see: https://docs.python.org/2/howto/descriptor.html#descriptor-protocol
    """

    def __init__(self, default):
        self.default = default

    def __get__(self, obj, typ=None):
        if obj is None:
            return self

        return self.default(obj)


class Code(namedtuple('Code', CODE_ARGS)):

    _attrs = CODE_ATTRS

    def __new__(cls, fun):
        supr = super(Code, cls)
        args = (getattr(fun.__code__, f) for f in cls._attrs)
        self = supr.__new__(cls, *args)
        self.fun = fun
        return self

    @defaultproperty
    def code(self):
        co = self.code = types.CodeType(*self)
        return co

    @defaultproperty
    def bytecode(self):
        bytecode = self.bytecode = dis.Bytecode(self.code)
        return bytecode

    def _instructions(self, key, names, constants):
        #TODO consts
        EMIT = '.retrospect.emit'
        LOCALS = '.retrospect.locals'
        GLOBALS = '.retrospect.globals'

        if EMIT not in names:
            names.append(EMIT)
        if LOCALS not in names:
            names.append(LOCALS)
        if GLOBALS not in names:
            names.append(GLOBALS)
        if key not in constants:
            constants.append(key)

        ins = dis.Instruction(*[None]*8)
        pop_top = ins._replace(opcode=1, opname='POP_TOP')
        load_const = ins._replace(opcode=100, opname='LOAD_CONST')
        load_global = ins._replace(opcode=116, opname='LOAD_GLOBAL')
        call_function = ins._replace(opcode=131, opname='CALL_FUNCTION')

        ins_branch = [
            load_global._replace(arg=names.index(EMIT)),
            load_global._replace(arg=names.index(LOCALS)),
            call_function._replace(arg=0),
            load_global._replace(arg=names.index(GLOBALS)),
            call_function._replace(arg=0),
            load_const._replace(arg=constants.index(key)),
            call_function._replace(arg=3),
            pop_top,
            ]

        return ins_branch

    def implement(self, **kwds):
        key = str(time.time())
        names = list(self.names)
        constants = list(self.constants)

        # strategies
        poi = dict()
        for point in ('symbols', 'lines', 'bytecode'):
            interest = kwds.pop(point, None) or list()
            if interest is not True:
                try:
                    interest = [int(interest)]
                except (TypeError, ValueError) as e:
                    if interest[0:0] == '':
                        interest = [interest]
                    interest = list(interest)
            poi[point] = interest

        def context():
            return (self.fun.__retrospect__, None)

        ins_all = list()
        for ins in self.bytecode:
            emit_ins_before = emit_ins_after = False

            if poi['bytecode'] or ins.opname == 'RETURN_VALUE':
                emit_ins_before = True

            if ins.opname == 'STORE_FAST':
                if poi['symbols'] is True or ins.argval in poi['symbols']:
                    emit_ins_before = True
                    emit_ins_after = True

            if ins.starts_line is not None:
                if poi['lines'] is True or ins.starts_line in poi['lines']:
                    emit_ins_before = True

            if emit_ins_before:
                ins_all.extend(self._instructions(key, names, constants))
            ins_all.append(ins)
            if emit_ins_after:
                ins_all.extend(self._instructions(key, names, constants))

        #TODO: lists
        lnotab = ''
        codestring = ''
        bytecode_offset = 0
        source_offset = self.firstlineno
        for ins in ins_all:
            if ins.starts_line:
                bytecode_buf = len(codestring) - bytecode_offset
                source_buf = ins.starts_line - source_offset

                while bytecode_buf > 255:
                    lnotab += '\xff\x00'
                    bytecode_buf -= 255
                while source_buf > 255:
                    lnotab += '\x00\xff'
                    source_buf -= 255

                lnotab += chr(bytecode_buf) + chr(source_buf)
                bytecode_offset = len(codestring)
                source_offset = ins.starts_line
            codestring += ins.codestring

        clone = self._replace(
            names=tuple(names),
            constants=tuple(constants),
            codestring=codestring,
            lnotab=lnotab,
            )

        return clone


class Retrospector(object):

    def __init__(self, fun):
        self._original_fun = fun
        if not hasattr(fun, '__code__'):
            raise TypeError('function needs __code__')

        if not hasattr(fun, '_code_cache'):
            fun._code_cache = {None: Code(fun)}

        self.fun = fun

    def trace(self, **kwds):
        fun = self.fun
        cache = self.fun._code_cache
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


try:
    import builtins
except ImportError:
    import __builtin__ as builtins
if not hasattr(builtins, '.retrospect.emit'):
    setattr(builtins, '.retrospect.emit', emit)
if not hasattr(builtins, '.retrospect.locals'):
    setattr(builtins, '.retrospect.locals', locals)
if not hasattr(builtins, '.retrospect.globals'):
    setattr(builtins, '.retrospect.globals', globals)
