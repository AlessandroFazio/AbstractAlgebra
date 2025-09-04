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
    def of(self, x: T) -> "RingElem[T]": ...
    
    @abstractmethod
    def one(self) -> "RingElem[T]": ...
    
    @abstractmethod
    def zero(self) -> "RingElem[T]": ...

    
class RingElem(ABC, Generic[T]):
    @abstractmethod
    def add(self, rhs: "Self[T]") -> "Self[T]": ... 
    
    @abstractmethod
    def neg(self) -> "Self[T]": ...
    
    @abstractmethod
    def mul(self, rhs: "Self[T]") -> "Self[T]": ...
    
    @abstractmethod
    def eq(self, other: object) -> bool: ...
    
    @abstractmethod
    def to_str(self) -> str: ...
    
    @abstractmethod
    def copy(self) -> "Self[T]": ...
    
    def __add__(self, rhs: "Self[T]") -> "Self[T]":
        return self.add(rhs)
    
    def __neg__(self) -> "Self[T]":
        return self.neg()
    
    def __mul__(self, rhs: "Self[T]") -> "Self[T]":
        return self.mul(rhs)
    
    def __sub__(self, rhs: "Self[T]") -> "Self[T]":
        return self + (-rhs)

    def __eq__(self, other: object) -> bool:
        return self.eq(other)
    
    def __repr__(self) -> str:
        return self.to_str()