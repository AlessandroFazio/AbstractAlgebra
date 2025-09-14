from typing import Iterator, Literal
from typing_extensions import Self


class CRC:
    _Q_MAP = {
        8: 0x07,       # CRC-8 (ATM HEC)
        16: 0x8005,    # CRC-16-IBM
        32: 0x04C11DB7 # CRC-32 (Ethernet, ZIP, etc.)
    }
    
    def __init__(self, n: int, q: int) -> None:
        self.n = n
        self.q = q
        self.value = 0
        self.n_minus_8 = self.n - 8
        self.max = (1 << self.n) - 1
        self._build_table()
        
    def _build_table(self) -> None:
        msb = 1 << (self.n - 1)
        table = []
        for b in range(256):
            v = b << self.n_minus_8
            for _ in range(8):
                if v & msb:
                    v = ((v << 1) ^ self.q) & self.max
                else:
                    v = (v << 1) & self.max
            table.append(v)
        self.table = table
        
    def append_byte(self, byte: int) -> None:
        idx = ((self.value >> self.n_minus_8) ^ byte) & 0xFF
        self.value = ((self.value << 8) & self.max) ^ self.table[idx]
        
    def flip(self) -> int:
        return (~self.value) & self.max
        
    @classmethod
    def of(cls, n: Literal[8, 16, 32]) -> Self:
        if n not in cls._Q_MAP:
            raise ValueError(f"CRC-{n} is not supported. Valid values for n are: [8, 16, 32]")
        return CRC(n, cls._Q_MAP[n])

    @classmethod
    def checksum(cls, data: Iterator[int], n: Literal[8, 16, 32] = 32) -> int:
        crc = cls.of(n)
        length = 0
        for b in data:
            crc.append_byte(b)
            length += 1

        while length != 0:
            crc.append_byte(length & 0xFF)
            length >>= 8

        for _ in range(n // 8):
            crc.append_byte(0)

        # return bitwise NOT
        return crc.flip()