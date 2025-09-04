from typing import Iterator, Tuple
from typing_extensions import Self
from abstract_algebra.core.groups.fields.base import Field, FieldElem
from abstract_algebra.utils.binary import BinaryUtils


class GF2(Field[int]):
    def __init__(self, k: int, q: int) -> None:
        if k < 1:
            raise ValueError("")
        if not BinaryUtils.bit_at(q, k):
            raise ValueError("")
        self.k = k
        self.q = q
    
    def num_elems(self) -> int:
        return 1 << self.k
    
    def elems(self) -> Iterator["GF2Elem"]:
        for i in range(self.num_elems()):
            yield GF2Elem(i, self) 
    
    def of(self, x: int) -> "FieldElem[int]":
        if x < 0 or x >= self.num_elems():
            raise ValueError("")
        return GF2Elem(x, self)
    
    def one(self) -> "FieldElem[int]":
        return GF2Elem(1, self)
    
    def zero(self) -> "FieldElem[int]":
        return GF2Elem(0, self)


class GF2Elem(FieldElem[int]):
    def __init__(self, x: int, field: "GF2") -> None:
        self.x = x
        super().__init__(field)
    
    def _add_raw(self, a: int, b: int) -> "int":
        return a ^ b
    
    def _neg_raw(self, a: int) -> "int":
        return a
    
    def _sub_raw(self, a: int, b: int) -> "int":
        return a ^ b
    
    def _mul_raw(self, a: int, b: int) -> "int":
        k, q = self.field.k, self.field.q
        c = 0
        for i in range(k):
            if BinaryUtils.bit_at(b, i):
                c ^= a
            a <<= 1
            if BinaryUtils.bit_at(a, k):
                a ^= q
        return c
    
    def _divmod_raw(self, a: int, b: int) -> Tuple["int", "int"]:
        dividend, divisor = a, b
        if divisor == 0:
            raise ZeroDivisionError("")
        
        divisor_deg = divisor.bit_length() - 1
        dividend_deg = dividend.bit_length() - 1
        quotient = 0
        
        while dividend_deg >= divisor_deg:
            shift = dividend_deg - divisor_deg
            quotient ^= 1 << (shift)
            dividend ^= divisor << shift
            dividend_deg = dividend.bit_length() - 1
        
        return quotient, dividend

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
        return self.field.of(s)
    
    def neg(self) -> "Self":
        neg = self._neg_raw(self.x)
        return self.field.of(neg)
    
    def mul(self, rhs: "Self") -> "Self":
        m = self._mul_raw(self.x, rhs.x)
        return self.field.of(m)
    
    def divmod(self, rhs: "Self") -> Tuple["Self", "Self"]:
        f = self.field
        q, r = self._divmod_raw(self.x, rhs.x)
        return f.of(q), f.of(r)
        
    def gcd(self, rhs: "Self") -> Tuple["Self", "Self", "Self"]:
        r, x, y = self._gcd_raw(self.x, rhs.x)
        f = self.field
        return f.of(r), f.of(x), f.of(y)
    
    def invert(self) -> "Self":
        f = self.field
        assert isinstance(f, GF2)
        _, x, _ = self._gcd_raw(self.x, f.q)
        return f.of(x)
            
    def eq(self, other: object) -> bool:
        return other is self or (isinstance(other, GF2Elem) and self.x == other.x)
    
    def copy(self) -> "Self":
        return GF2Elem(self.x, self.field)
    
    def to_str(self) -> str:
        return f"GF2({self.x})"