from xdsl.utils.BitVector import *
from z3 import *


def bit_add_no_overflow(x: BitVector, y: BitVector):
    return x.bits + y.bits < (1 << x.width)


def bvadd_no_overflow(x, y, signed=False):
    assert x.ctx_ref() == y.ctx_ref()
    tmp = Z3_mk_bvadd_no_overflow(x.ctx_ref(), x.as_ast(), y.as_ast(), signed)
    return BoolRef(tmp)


def bit_sub_no_overflow(x: BitVector, y: BitVector):
    return x.bits >= y.bits


def bvsub_no_overflow(x, y, signed=False):
    assert x.ctx_ref() == y.ctx_ref()
    tmp = Z3_mk_bvsub_no_underflow(x.ctx_ref(), x.as_ast(), y.as_ast(), signed)
    return BoolRef(tmp)


def If(cond, x, y):
    if cond:
        return x
    return y


def Or(x, y):
    return x or y


def And(x, y):
    return x and y


def ULE(x, y):
    return x <= y


class ConstantIntRange:
    umin = None
    umax = None

    def __init__(self, umin, umax):
        self.umin = umin
        self.umax = umax

    @classmethod
    def from_constant(cls, val: BitVector):
        return ConstantIntRange(val, val)

    @classmethod
    def maxRange(cls, width):
        return ConstantIntRange(0, (1 << width) - 1)

    # This function is required
    def getConstraint(self):
        return [ULE(self.umin, self.umax)]

    # This function is required
    def getInstanceConstraint(self, inst):
        return [ULE(self.umin, inst), ULE(inst, self.umax)]


def add(x, y):
    return x + y


def addImpl(x: ConstantIntRange, y: ConstantIntRange):
    minOverflow = bit_add_no_overflow(x.umin, y.umin)
    maxOverflow = bit_add_no_overflow(x.umax, y.umax)
    cond = And(minOverflow, maxOverflow)
    retA = ConstantIntRange.maxRange(x.umin.size())
    retB = ConstantIntRange(x.umin + y.umin, x.umax + y.umax)
    return ConstantIntRange(If(cond, retB.umin, retA.umin),
                            If(cond, retB.umax, retA.umax))


def sub(x, y):
    return x - y


def subImpl(x: ConstantIntRange, y: ConstantIntRange):
    minOverflow = bit_sub_no_overflow(x.umin, y.umax)
    maxOverflow = bit_sub_no_overflow(x.umax, y.umin)
    cond = And(minOverflow, maxOverflow)
    retA = ConstantIntRange.maxRange(x.umin.size())
    retB = ConstantIntRange(x.umin - y.umax, x.umax - y.umin)
    return ConstantIntRange(If(cond, retB.umin, retA.umin),
                            If(cond, retB.umax, retA.umax))


FUNC_MAPPING = {"bit_add_no_overflow": bvadd_no_overflow, "bit_sub_no_overflow": bvsub_no_overflow}

NEED_VERIFY = ((sub, subImpl),(add,addImpl))
