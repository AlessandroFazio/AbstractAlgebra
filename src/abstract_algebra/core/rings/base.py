from abc import ABC, abstractmethod
from typing import Generic, Iterator, TypeVar
from typing_extensions import Self

T = TypeVar('T')


class Ring(ABC, Generic[T]):
    @abstractmethod
    def num_elems(self) -> int: ...
    
    @abstractmethod
    def elems(self) -> Iterator["RingElem[T]"]: ...
    
    @abstractmethod
    def elem_of(self, x: T) -> "RingElem[T]": ...
    
    @abstractmethod
    def one(self) -> "RingElem[T]": ...
    
    @abstractmethod
    def zero(self) -> "RingElem[T]": ...
    
    @abstractmethod
    def eq(self, other: object) -> bool: ...
    
    @abstractmethod
    def hash(self) -> int: ...
    
    @abstractmethod
    def to_str(self) -> str: ...
    
    def __eq__(self, other: object) -> bool:
        return self.eq(other)

    def __str__(self) -> str:
        return self.to_str()
    
    def __hash__(self) -> int:
        return self.hash()

    
class RingElem(ABC, Generic[T]):
    def __init__(self, ring: "Ring[T]") -> None:
        self._container = ring
        
    def container(self) -> "Ring[T]":
        return self._container
        
    @abstractmethod
    def add(self, rhs: Self) -> Self: ... 
    
    @abstractmethod
    def neg(self) -> Self: ...
    
    @abstractmethod
    def mul(self, rhs: Self) -> Self: ...
    
    @abstractmethod
    def eq(self, other: object) -> bool: ...
    
    @abstractmethod
    def hash(self) -> int: ...
    
    @abstractmethod
    def to_str(self) -> str: ...
    
    @abstractmethod
    def copy(self) -> Self: ...
    
    def pow(self, exp: int) -> Self:
        if exp < 0:
            raise ValueError("")
        result = self._container.one()
        base = self.copy()
        while exp > 0:
            if exp & 1:
                result *= base
            base *= base
            exp >>= 1
        return result
    
    def __add__(self, rhs: Self) -> Self:
        return self.add(rhs)
    
    def __neg__(self) -> Self:
        return self.neg()
    
    def __mul__(self, rhs: Self) -> Self:
        return self.mul(rhs)
    
    def __sub__(self, rhs: Self) -> Self:
        return self + (-rhs)
    
    def __iadd__(self, rhs: Self) -> Self:
        return self + rhs
    
    def __isub__(self, rhs: Self) -> Self:
        return self - rhs
    
    def __imul__(self, rhs: Self) -> Self:
        return self * rhs

    def __eq__(self, other: object) -> bool:
        return self.eq(other)
    
    def __hash__(self) -> int:
        return self.hash()
    
    def __repr__(self) -> str:
        return self.to_str()