from z3 import *

class KnownBits:
    knownZeros=None
    knownOnes=None
    width=None

    def __init__(self, width, knownZeros, knownOnes):
        self.width=width
        self.knownZeros=knownZeros
        self.knownOnes=knownOnes

    @classmethod
    def from_string(cls, str):
        width = len(str)
        knownOnes = 0
        knownZeros = 0
        for i in range(len(str)):
            if str[i] == '0':
                knownZeros |= (1 << i)
            elif str[i] == '1':
                knownOnes |= (1 << i)
        return KnownBits(width,knownZeros,knownOnes)

    @classmethod
    def from_constant(cls,width,val):
        zero=0
        one=0
        for i in range(width):
            if (val&(1<<i))==1:
                one|=(1<<i)
            else:
                zero|=(1<<i)
        return KnownBits(width,zero,one)

    def getMaxValue(self):
        return ((1<<self.width)-1)^self.knownZeros

    def getMinValue(self):
        return self.knownOnes

    def to_string(self):
        str=""
        for i in range(self.width):
            if (self.knownOnes&(1<<i))!=0:
                str+='1'
            elif (self.knownZeros&(1<<i))!=0:
                str+='0'
            else:
                str+='X'
        return str

    def hasConflict(self):
        return 0!=(self.knownOnes&self.knownZeros)

    def getIthBit(self, i):
        assert i<self.width and "i has to be less than width"
        zero = self.knownZeros&(1<<i)
        one=self.knownZeros&(1<<i)
        if one:
            return 1
        elif zero:
            return 0
        else:
            return -1