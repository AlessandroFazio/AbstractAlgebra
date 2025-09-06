from itertools import islice
import struct
from typing import Optional, Tuple
from typing_extensions import Self

from abstract_algebra.core.fields.gf2 import GF2Field, GF2
from abstract_algebra.core.rings.poly import Polynomial
from abstract_algebra.utils.binary import BinaryUtils


class ReedSolomonCodec:
    _ENC_FMT_MAP = {1: "B", 2: "H", 4: "I", 8: "Q"}
     
    def __init__(self, k: int, n: int, q: Tuple[int, int]) -> None:
        k_bytes = BinaryUtils.byte_length(k)
        if k < 0:
            raise ValueError()
        if k_bytes not in self._ENC_FMT_MAP:
            raise ValueError("")
        if k >= n or n > (1 << q[0]):
            raise ValueError()
        self.k = k
        self.n = n
        self._alphabet = GF2Field.of(q[0], q[1])
        self._xs = list(islice(self._alphabet.elems(), self.n))
        self._enc_block_fmt = f"<{self._ENC_FMT_MAP[k_bytes]}{self.n}s"
        self._enc_block_len = struct.calcsize(self._enc_block_fmt)
        
    def encode(self, data: bytes) -> bytes:
        return b"".join(self._encode_block(data[i:i+self.k]) 
                        for i in range(0, len(data), self.k))

    def decode(self, data: bytes) -> bytes:
        return b"".join(self._decode_block(data[i:i+self._enc_block_len]) 
                        for i in range(0, len(data), self._enc_block_len))
        
    def _decode_block(self, block: bytes) -> bytes:
        length, message = struct.unpack(self._enc_block_fmt, block)
        ys = [self._alphabet.elem_of(b) for b in message[:self.k]]
        poly = Polynomial[GF2].interpolate(self._xs[:self.k], ys)
        return bytes(c.x for c in poly.coeffs[:length])
            
    def _pad_chunk(self, chunk: bytes) -> Tuple[bytes, int]:
        orig_len = len(chunk)
        padded = chunk.ljust(self.k, b"\x00")
        return padded, orig_len
            
    def _encode_block(self, chunk: bytes) -> bytes:
        chunk, length = self._pad_chunk(chunk)
        poly = Polynomial[GF2].of([self._alphabet.elem_of(b) for b in chunk])
        message = bytes(y.x for y in poly.eval_all(self._xs))
        return struct.pack(self._enc_block_fmt, length, message)
    
    @classmethod
    def of(cls, code_rate: Optional[float] = 0.8) -> Self:
        if code_rate < 0 or code_rate > 1:
            raise ValueError()
        m = 8
        n = 2 ** m
        k = max(min(int(code_rate * n), n-1), 1)
        return cls(k, n, (m, 283))