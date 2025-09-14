from codechain.core.base import Codec
from codechain.core.crypto.base import Cipher
from codechain.utils.binary import stable_hash


class SymmetricCryptoCodec(Codec):
    def __init__(self, cipher: Cipher) -> None:
        self.cipher = cipher

    def encode(self, data: bytes) -> tuple[dict[str, bytes], bytes]:
        return {}, self.cipher.encrypt(data)

    def decode(self, meta: dict[str, bytes], payload: bytes) -> bytes:
        return self.cipher.decrypt(payload)
    
    def hash(self) -> int:
        return stable_hash(("SymmetricCryptoCodec", self.cipher.hash()))
    
    def eq(self, other: object) -> bool:
        return isinstance(other, SymmetricCryptoCodec) and self.cipher == other