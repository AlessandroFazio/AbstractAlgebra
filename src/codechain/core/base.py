from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Tuple


class CodecMode(Enum):
    BLOCK = "block"
    STREAM = "stream"


class Codec(ABC):
    @abstractmethod
    def encode(self, data: bytes) -> Tuple[Dict[str, bytes], bytes]: ...
    @abstractmethod
    def decode(self, meta: Dict[str, bytes], payload: bytes) -> bytes: ...
    @abstractmethod
    def hash(self) -> int: ...
    @abstractmethod
    def eq(self, other: object) -> bool: ...
    
    def __hash__(self) -> int:
        return self.hash()
    
    def __eq__(self, other: object) -> bool:
        return self.eq(other)
    

class PaddingScheme(ABC):
    @abstractmethod
    def pad(self, data: bytes, block_size: int) -> bytes: ...
    @abstractmethod
    def unpad(self, data: bytes, block_size: int) -> bytes: ...
    @abstractmethod
    def hash(self) -> int: ...
    @abstractmethod
    def eq(self, other: object) -> bool: ...
    
    def __hash__(self) -> int:
        return self.hash()
    
    def __eq__(self, other: object) -> bool:
        return self.eq(other)