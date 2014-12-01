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

    def implement(self, *symbols, **kwds):
        signature = [locals, globals, None]
        constants = list(self.constants) + [emit] + signature[:-1]

        ins = dis.Instruction(*[None]*8)
        ins_pop_top = ins._replace(opcode=1, opname='POP_TOP')
        ins_load_const = ins._replace(opcode=100, opname='LOAD_CONST')
        ins_call_function = ins._replace(opcode=131, opname='CALL_FUNCTION')

        ins_new = [
            ins_load_const._replace(arg=constants.index(emit)),
            ]
        for arg in signature:
            ins_new.extend((
                arg and ins_load_const._replace(arg=constants.index(arg)),
                arg and ins_call_function._replace(arg=0),
                ))
        ins_new.extend((
            ins_call_function._replace(arg=len(signature)),
            ins_pop_top,
            ))

        def context():
            return (self.fun.__retrospect__, None)

        ins_all = list()
        for ins in self.bytecode:
            if ins.starts_line is not None or ins.opname in (
                    'RETURN_VALUE',
                    ):
                #TODO: opcode.EXTENDED_ARG?
                # creates many constants... need to ensure correct
                #def context(self=self, lineno=ins.starts_line):
                #    return (self, lineno)
                if context not in constants:
                    constants.append(context)
                ins_ctx = ins_load_const._replace(arg=constants.index(context))
                ins_ctx_call = ins_call_function._replace(arg=0)
                ins_starts_line = ins_new[:]
                ins_starts_line[-4:-2] = [ins_ctx, ins_ctx_call]
                ins_all.extend(ins_starts_line)
            ins_all.append(ins)

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

    def trace_none(self):
        fun = self.fun
        cache = self.fun._code_cache
        tracer = cache[None]

        fun.__code__ = tracer.code
        return self

    def trace_lines(self):
        fun = self.fun
        cache = self.fun._code_cache
        tracer = cache.get('lines')
        if tracer is None:
            tracer = cache['lines'] = cache[None].implement(lines=True)

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
