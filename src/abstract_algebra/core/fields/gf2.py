from typing import Iterator, Tuple
from typing_extensions import Self
from abstract_algebra.core.fields.base import Field, FieldElem
from abstract_algebra.utils.binary import BinaryUtils


class GF2Field(Field[int]):
    def __init__(self, k: int, q: int) -> None:
        if k < 1:
            raise ValueError("")
        if not BinaryUtils.bit_at(q, k):
            raise ValueError("")
        self.k = k
        self.q = q
    
    def num_elems(self) -> int:
        return 1 << self.k
    
    def elems(self) -> Iterator["GF2"]:
        for i in range(self.num_elems()):
            yield GF2(i, self) 
    
    def elem_of(self, x: int) -> "GF2":
        if x < 0 or x >= self.num_elems():
            raise ValueError("")
        return GF2(x, self)
    
    def one(self) -> "GF2":
        return GF2(1, self)
    
    def zero(self) -> "GF2":
        return GF2(0, self)
    
    def eq(self, other: object) -> bool:
        return isinstance(other, GF2Field) and self.k == other.k and self.q == self.q
    
    def hash(self) -> int:
        return hash((self.k, self.q))

    def to_str(self) -> str:
        return f"GF({self.num_elems()})"
    
    @classmethod
    def of(cls, k: int, q: int) -> "GF2Field":
        return cls(k, q)

class GF2(FieldElem[int]):
    def __init__(self, x: int, field: "GF2Field") -> None:
        self.x = x
        super().__init__(field)
    
    def _add_raw(self, a: int, b: int) -> "int":
        return a ^ b
    
    def _neg_raw(self, a: int) -> "int":
        return a
    
    def _sub_raw(self, a: int, b: int) -> "int":
        return a ^ b
    
    def _mul_raw(self, a: int, b: int) -> "int":
        f = self._container
        assert isinstance(f, GF2Field)
        c = 0
        for i in range(f.k):
            if BinaryUtils.bit_at(b, i):
                c ^= a
            a <<= 1
            if BinaryUtils.bit_at(a, f.k):
                a ^= f.q
        return c
    
    def _divmod_raw(self, a: int, b: int) -> Tuple["int", "int"]:
        dvd, div = a, b
        if div == 0:
            raise ZeroDivisionError("")
        
        dvd_deg = dvd.bit_length() - 1
        div_deg = div.bit_length() - 1
        q = 0
        
        while dvd_deg >= div_deg:
            shift = dvd_deg - div_deg
            q ^= 1 << (shift)
            dvd ^= div << shift
            dvd_deg = dvd.bit_length() - 1
            
        return q, dvd

    def _gcd_raw(self, a: int, b: int) -> Tuple["int", "int", "int"]:
        if b == 0:
            return a, 1, 0
        old_x, x = 1, 0
        old_y, y = 0, 1
        while b != 0:
            q, r = self._divmod_raw(a, b)
            a, b = b, r
            old_x, x = x, self._sub_raw(old_x, self._mul_raw(q, x))
            old_y, y = y, self._sub_raw(old_y, self._mul_raw(q, y))
        return a, old_x, old_y
    
    def add(self, rhs: "Self") -> "Self":
        s = self._add_raw(self.x, rhs.x)
        return self._container.elem_of(s)
    
    def neg(self) -> "Self":
        neg = self._neg_raw(self.x)
        return self._container.elem_of(neg)
    
    def mul(self, rhs: "Self") -> "Self":
        m = self._mul_raw(self.x, rhs.x)
        return self._container.elem_of(m)
    
    def divmod(self, rhs: "Self") -> Tuple["Self", "Self"]:
        f = self._container
        q, r = self._divmod_raw(self.x, rhs.x)
        return f.elem_of(q), f.elem_of(r)
        
    def gcd(self, rhs: "Self") -> Tuple["Self", "Self", "Self"]:
        r, x, y = self._gcd_raw(self.x, rhs.x)
        f = self._container
        return f.elem_of(r), f.elem_of(x), f.elem_of(y)
    
    def invert(self) -> "Self":
        f = self._container
        assert isinstance(f, GF2Field)
        _, x, _ = self._gcd_raw(self.x, f.q)
        return f.elem_of(x)
            
    def eq(self, other: object) -> bool:
        return other is self or (isinstance(other, GF2) and self.x == other.x)
    
    def hash(self) -> int:
        return hash((self._container, self.x))
    
    def copy(self) -> "Self":
        return GF2(self.x, self._container)
    
    def to_str(self) -> str:
        return str(self.x)