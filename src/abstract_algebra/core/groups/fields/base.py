from abc import abstractmethod
from typing import TypeVar
from typing_extensions import Self

from abstract_algebra.core.groups.rings.base import Ring, RingElem

T = TypeVar('T')


class Field(Ring[T]):
    pass

    
class FieldElem(RingElem[T]):
    def __init__(self, field: "Field[T]") -> None:
        self.field = field
        
    @abstractmethod
    def divmod(self, rhs: "Self[T]") -> "Self[T]": ...
    
    # naive implementation - specialized classes should implement more efficient methods for computing the inverse if needed
    def invert(self) -> "Self[T]":
        f = self.field
        for x in f.elems():
            if self * x == f.one():
                return x
        raise ArithmeticError("any element in f should have an inverse")
    
    def __divmod__(self, rhs: "Self[T]") -> "Self[T]":
        return self.divmod(rhs)
    
    def __truediv__(self, rhs: "Self[T]") -> "Self[T]":
        return self * rhs.invert()