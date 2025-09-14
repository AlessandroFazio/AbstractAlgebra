from codechain.core.crypto.base import BlockCipherMode
from codechain.utils.binary import stable_hash


class ECBMode(BlockCipherMode):

    def encrypt(self, data: bytes) -> bytes:
        bs = self.block_cipher.block_size
        data = self.padding_scheme.pad(data, bs)
        out = []
        for i in range(0, len(data), bs):
            block = data[i:i+bs]
            out.append(self.block_cipher.encrypt(block))
        return b"".join(out)

    def decrypt(self, data: bytes) -> bytes:
        bs = self.block_cipher.block_size
        out = []
        for i in range(0, len(data), bs):
            block = data[i:i+bs]
            out.append(self.block_cipher.decrypt(block))
        data = b"".join(out)
        data = self.padding_scheme.unpad(data, bs)
        return data

    def hash(self) -> int:
        return stable_hash(("ECBMode", super().hash()))
    
    def eq(self, other: object) -> bool:
        return isinstance(other, ECBMode) and super() == other