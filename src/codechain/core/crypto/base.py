from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

from codechain.core.base import PaddingScheme
from codechain.core.padding import PKCS7
from codechain.utils.binary import stable_hash


class CipherKind(Enum):
    BLOCK = "block"
    STREAM = "stream"
    MODE = "mode"


class Cipher(ABC):
    @property
    @abstractmethod
    def kind(self) -> CipherKind: ...
    
    @abstractmethod
    def encrypt(self, plaintext: bytes) -> bytes: ...
    @abstractmethod
    def decrypt(self, ciphertext: bytes) -> bytes: ...
    @abstractmethod
    def hash(self) -> int: ...
    @abstractmethod
    def eq(self, other: object) -> bool: ...
    
    def __hash__(self) -> int:
        return self.hash()
    
    def __eq__(self, other: object) -> bool:
        return self.eq(other)


class BlockCipher(Cipher):
    kind = CipherKind.BLOCK
    block_size: int = 16
    

class BlockCipherMode(Cipher):
    """cipher mode is itself a Cipher, but always wraps a BlockCipher."""
    kind = CipherKind.MODE

    def __init__(self, block_cipher: BlockCipher, padding_scheme: Optional[PaddingScheme] = None) -> None:
        self.block_cipher = block_cipher
        self.padding_scheme = padding_scheme or PKCS7()
        
    def hash(self) -> int:
        return stable_hash((self.block_cipher, self.padding_scheme))
    
    def eq(self, other: object) -> bool:
        return isinstance(other, BlockCipherMode) and \
            self.block_cipher.eq(other.block_cipher) and \
            self.padding_scheme.eq(other.padding_scheme)


class StreamCipher(Cipher):
    kind = CipherKind.STREAM

    @abstractmethod
    def keystream(self, nbytes: int) -> bytes: ...

    def encrypt(self, plaintext: bytes) -> bytes:
        ks = self.keystream(len(plaintext))
        return bytes(a ^ b for a, b in zip(plaintext, ks))

    def decrypt(self, ciphertext: bytes) -> bytes:
        return self.encrypt(ciphertext)