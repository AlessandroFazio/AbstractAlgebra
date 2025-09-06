from abc import abstractmethod
from typing import TypeVar
from typing_extensions import Self

from abstract_algebra.core.rings.base import Ring, RingElem

T = TypeVar('T')


class Field(Ring[T]):
    pass

    
class FieldElem(RingElem[T]):
    def __init__(self, field: "Field[T]") -> None:
        self._container = field
        
    def container(self) -> "Field[T]":
        return self._container
        
    @abstractmethod
    def divmod(self, rhs: "Self") -> "Self": ...
    
    # naive implementation - specialized classes should implement more efficient methods for computing the inverse if needed
    def invert(self) -> "Self":
        f = self._container
        for x in f.elems():
            if self * x == f.one():
                return x
        raise ArithmeticError("any element in f should have an inverse")
    
    def pow(self, exp: int) -> "Self":
        if exp < 0:
            return self.invert().pow(-exp)
        return super().pow(exp)
    
    def __divmod__(self, rhs: "Self") -> "Self":
        return self.divmod(rhs)
    
    def __truediv__(self, rhs: "Self") -> "Self":
        return self * rhs.invert()
    
    def __itruediv__(self, rhs: "Self") -> "Self":
        return self / rhs

    def __imod__(self, rhs: "Self") -> "Self":
        return self % rhs