import os
from typing import Optional
from codechain.core.base import PaddingScheme
from codechain.core.crypto.base import BlockCipher, BlockCipherMode
from codechain.utils.binary import stable_hash


class CBCMode(BlockCipherMode):
    def __init__(self, block_cipher: BlockCipher, padding_scheme: Optional[PaddingScheme] = None, iv: Optional[bytes] = None) -> None:
        super().__init__(block_cipher, padding_scheme)
        self.iv = iv or os.urandom(block_cipher.block_size)

    def encrypt(self, data: bytes) -> bytes:
        bs = self.block_cipher.block_size
        data = self.padding_scheme.pad(data, bs)
        out, prev = [], self.iv
        for i in range(0, len(data), bs):
            block = data[i:i+bs]
            xored = bytes(a ^ b for a, b in zip(block, prev))
            enc = self.block_cipher.encrypt(xored)
            out.append(enc)
            prev = enc
        return self.iv + b"".join(out)

    def decrypt(self, data: bytes) -> bytes:
        bs = self.block_cipher.block_size
        iv, rest = data[:bs], data[bs:]
        out, prev = [], iv
        for i in range(0, len(rest), bs):
            enc = rest[i:i+bs]
            dec = self.block_cipher.decrypt(enc)
            block = bytes(a ^ b for a, b in zip(dec, prev))
            out.append(block)
            prev = enc
        data = b"".join(out)
        data = self.padding_scheme.unpad(data, bs)
        return data
    
    def hash(self) -> int:
        return stable_hash(("CBCMode", super().hash()))
    
    def eq(self, other: object) -> bool:
        return super().eq(other) and isinstance(other, CBCMode) and self.iv == other.iv