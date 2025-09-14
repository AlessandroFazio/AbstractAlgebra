from codechain.core.base import PaddingScheme
from codechain.utils.binary import stable_hash


class PKCS7(PaddingScheme):
    def pad(self, data: bytes, block_size: int) -> bytes:
        pad_len = block_size - (len(data) % block_size)
        return data + bytes([pad_len]) * pad_len

    def unpad(self, data: bytes, block_size: int) -> bytes:
        pad_len = data[-1]
        if pad_len == 0 or pad_len > block_size:
            raise ValueError("Invalid PKCS#7 padding")
        if data[-pad_len:] != bytes([pad_len]) * pad_len:
            raise ValueError("Corrupted PKCS#7 padding")
        return data[:-pad_len]
    
    def hash(self) -> int:
        return stable_hash("PKCS7")    
    
    def eq(self, other: object) -> bool:
        return isinstance(other, PKCS7)


class ZeroPadding(PaddingScheme):
    def pad(self, data: bytes, block_size: int) -> bytes:
        pad_len = block_size - (len(data) % block_size)
        return data + b"\x00" * pad_len

    def unpad(self, data: bytes, _: int) -> bytes:
        return data.rstrip(b"\x00")

    def hash(self) -> int:
        return stable_hash("ZeroPadding")    
    
    def eq(self, other: object) -> bool:
        return isinstance(other, ZeroPadding)