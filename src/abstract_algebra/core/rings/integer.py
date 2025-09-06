from typing import Iterator
from typing_extensions import Self

from abstract_algebra.core.rings.base import Ring, RingElem


class Z(Ring[int]):
    def num_elems(self) -> int:
        return -1

    def elems(self) -> Iterator[RingElem[int]]:
        e = self.zero()
        while True:
            yield e
            e += self.one()

    def elem_of(self, x: int) -> RingElem[int]:
        return ZElem(x, self)

    def one(self) -> RingElem[int]:
        return self.elem_of(1)

    def zero(self) -> RingElem[int]:
        return self.elem_of(0)

    def eq(self, other: object) -> bool:
        return isinstance(other, Z)

    def hash(self) -> int:
        return hash("Z")

    def to_str(self) -> str:
        return "Z"


class ZElem(RingElem[int]):
    def __init__(self, x: int, ring: Z) -> None:
        super().__init__(ring)
        self.x = x
        
    def add(self, rhs: Self) -> Self:
        return self._container.elem_of(self.x + rhs.x)

    def neg(self) -> Self:
        return self._container.elem_of(-self.x)

    def mul(self, rhs: Self) -> Self:
        return self._container.elem_of(self.x * rhs.x)

    def eq(self, other: object) -> bool:
        return isinstance(other, ZElem) and self.x == other.x

    def hash(self) -> int:
        return hash(self.x)

    def to_str(self) -> str:
        return str(self.x)

    def copy(self) -> Self:
        return self._container.elem_of(self.x)

    