class BitVector:
    bits = None
    width = None

    def __init__(self, width, bits):
        assert width >= 1 and "Width should be larger than 1"
        bits %= (1 << width)
        self.width = width
        self.bits = bits

    def __add__(self, other):
        assert self.width == other.width and "Both bit vectors should have the same width!"
        return BitVector(self.width, (self.bits + other.bits))

    def __sub__(self, other):
        assert self.width == other.width and "Both bit vectors should have the same width!"
        return BitVector(self.width(self.bits + (1 << self.width) - other.bits))

    def __and__(self, other):
        assert self.width == other.width and "Both bit vectors should have the same width!"
        return BitVector(self.width, self.bits & other.bits)

    def __or__(self, other):
        assert self.width == other.width and "Both bit vectors should have the same width!"
        return BitVector(self.width, self.bits | other.bits)

    def __xor__(self, other):
        assert self.width == other.width and "Both bit vectors should have the same width!"
        return BitVector(self.width, self.bits ^ other.bits)

    def __invert__(self):
        bits = self.bits
        for i in range(self.width):
            bits ^= (1 << i)
        return BitVector(self.width, bits)

    def size(self):
        return self.width
