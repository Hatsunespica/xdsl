from z3 import *
from xdsl.utils.BitVector import *


class KnownBits:
    knownZeros = None
    knownOnes = None

    def __init__(self, knownZeros, knownOnes):
        self.knownZeros = knownZeros
        self.knownOnes = knownOnes

    # This function is required
    def getConstraint(self):
        return [self.knownOnes & self.knownZeros == 0]

    # This function is required
    def getInstanceConstraint(self, inst):
        return [(~inst | self.knownZeros) == ~inst, (inst | self.knownOnes) == inst]

    @classmethod
    def from_string(cls, str):
        width = len(str)
        knownOnes = 0
        knownZeros = 0
        for i in range(width):
            if str[i] == '0':
                knownZeros |= (1 << i)
            elif str[i] == '1':
                knownOnes |= (1 << i)
        return KnownBits(BitVector(width, knownZeros), BitVector(width, knownOnes))

    @classmethod
    def from_constant(cls, width, val):
        zero = 0
        one = 0
        for i in range(width):
            if (val & (1 << i)) != 0:
                one |= (1 << i)
            else:
                zero |= (1 << i)
        return KnownBits(BitVector(width, zero), BitVector(width, one))

    def getMaxValue(self):
        return ~self.knownZeros

    def getMinValue(self):
        return self.knownOnes

    def to_string(self):
        str = ""
        for i in range(self.knownOnes.width):
            if (self.knownOnes.bits & (1 << i)) != 0:
                str += '1'
            elif (self.knownZeros.bits & (1 << i)) != 0:
                str += '0'
            else:
                str += 'X'
        return str

    def hasConflict(self):
        return 0 != (self.knownOnes & self.knownZeros)

    def getIthBit(self, i):
        assert i < self.knownOnes.size() and "i has to be less than width"
        zero = self.knownZeros.bits & (1 << i)
        one = self.knownZeros.bits & (1 << i)
        if one:
            return 1
        elif zero:
            return 0
        else:
            return -1


def OR(x, y):
    return x | y


def orImpl(x: KnownBits, y: KnownBits):
    return KnownBits(x.knownZeros & y.knownZeros, x.knownOnes | y.knownOnes)


def AND(x, y):
    return x & y


def AndImpl(x: KnownBits, y: KnownBits):
    return KnownBits(x.knownZeros | y.knownZeros, x.knownOnes & y.knownOnes)


def XOR(x, y):
    return x ^ y


def XorImpl(x: KnownBits, y: KnownBits):
    return KnownBits((x.knownZeros & y.knownZeros) | (x.knownOnes & y.knownOnes),
                     (x.knownZeros & y.knownOnes) | (x.knownOnes & y.knownZeros))


def ADD(x, y):
    return x + y


def AddImpl(x: KnownBits, y: KnownBits):
    possibleSumZero = x.getMaxValue() + y.getMaxValue()
    possibleSumOne = x.getMinValue() + y.getMinValue()

    carryKnownZero = ~(possibleSumZero ^ x.knownZeros ^ y.knownZeros)
    carryKnownOne = possibleSumOne ^ x.knownOnes ^ y.knownOnes

    LHSKnownUnion = x.knownZeros | x.knownOnes
    RHSKnownUnion = y.knownZeros | y.knownOnes

    carryKnownUnion = carryKnownZero | carryKnownOne
    known = carryKnownUnion & LHSKnownUnion & RHSKnownUnion
    return KnownBits(~possibleSumZero & known, possibleSumOne & known)


NEED_VERIFY = ((ADD, AddImpl), (AND, AndImpl), (OR, orImpl), (XOR, XorImpl))
