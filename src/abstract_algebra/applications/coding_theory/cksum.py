import ctypes

Q = 0x04C11DB7  # CRC-32 generator polynomial

class CRC:
    def __init__(self) -> None:
        # c_uint32 wraps the integer into a 32-bit unsigned register
        self.value = ctypes.c_uint32(0)

    def append_bit(self, bit: int) -> None:
        v = self.value.value
        msb = (v >> 31) & 1

        # shift left inside 32-bit register
        v = ctypes.c_uint32(v << 1).value

        if msb == 1:
            v ^= Q

        # feed in the new bit at the LSB
        v ^= bit

        # wrap back into 32-bit
        self.value = ctypes.c_uint32(v)

    def append_byte(self, byte: int) -> None:
        # process each bit (LSB first, matches your original code)
        for i in range(8):
            self.append_bit((byte >> i) & 1)


class Checksum:
    @classmethod
    def of(cls, data: bytes) -> int:
        crc = CRC()
        for b in data:
            crc.append_byte(b)

        length = len(data)
        while length != 0:
            crc.append_byte(length & 0xFF)
            length >>= 8

        for _ in range(32):
            crc.append_bit(0)

        # return bitwise NOT, masked into 32 bits
        return ctypes.c_uint32(~crc.value.value).value
