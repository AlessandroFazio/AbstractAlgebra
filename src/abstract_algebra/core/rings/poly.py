from __future__ import annotations

from typing import Generic, List, Tuple, TypeVar
from typing_extensions import Self

from abstract_algebra.core.fields.base import Field
from abstract_algebra.core.rings.base import Ring, RingElem

T = TypeVar("T", bound=RingElem)


class PolynomialRing(Ring["List[T]"], Generic[T]):
    def __init__(self, coeff_ring: Ring[T]) -> None:
        self.coeff_ring = coeff_ring

    def num_elems(self) -> int:
        return -1  # infinite ring

    def elems(self) -> List[Polynomial[T]]:
        raise NotImplementedError("Enumerating all polynomials is infinite")

    def elem_of(self, x: List[T]) -> Polynomial[T]:
        return Polynomial[T](x)

    def one(self) -> Polynomial[T]:
        return Polynomial[T].of_scalar(self.coeff_ring.one())

    def zero(self) -> Polynomial[T]:
        return Polynomial[T].of_scalar(self.coeff_ring.zero())

    def eq(self, other: object) -> bool:
        return (
            isinstance(other, PolynomialRing)
            and self.coeff_ring == other.coeff_ring
        )
        
    def hash(self) -> int:
        return hash(self.coeff_ring)

    def to_str(self) -> str:
        return f"{self.coeff_ring}[x]"


class Polynomial(RingElem["List[T]"], Generic[T]):
    def __init__(self, coeffs: List[T]) -> None:
        coeffs = self._trim_coeffs(coeffs)
        if not coeffs:
            raise ValueError("Polynomial cannot have empty coefficient list")

        self.coeffs: List[T] = coeffs
        self._coeff_ring: Ring[T] = coeffs[0].container()
        super().__init__(PolynomialRing[T](self._coeff_ring))

    # ---------- internal helpers ----------

    def _align_coeffs(self, a: List[T], b: List[T]) -> Tuple[List[T], List[T]]:
        cr = self._coeff_ring
        len_a, len_b = len(a), len(b)
        n = max(len_a, len_b)
        a = a + [cr.zero()] * (n - len_a)
        b = b + [cr.zero()] * (n - len_b)
        return a, b

    def _trim_coeffs(self, coeffs: List[T]) -> List[T]:
        if not coeffs:
            return coeffs
        cr = coeffs[0].container()
        while len(coeffs) > 1 and coeffs[-1] == cr.zero():
            coeffs.pop()
        return coeffs

    # ---------- ring element interface ----------

    def add(self, rhs: Self) -> Self:
        a, b = self._align_coeffs(self.coeffs, rhs.coeffs)
        return Polynomial[T]([a_i + b_i for a_i, b_i in zip(a, b)])

    def mul(self, rhs: Self) -> Self:
        cr = self._coeff_ring
        m: List[T] = [cr.zero()] * (self.degree() + rhs.degree() + 1)
        for i, a_i in enumerate(self.coeffs):
            if a_i == cr.zero():
                continue
            for j, b_j in enumerate(rhs.coeffs):
                if b_j == cr.zero():
                    continue
                m[i + j] = m[i + j] + a_i * b_j
        return Polynomial[T](m)

    def neg(self) -> Self:
        return Polynomial[T]([-a for a in self.coeffs])

    def eq(self, other: object) -> bool:
        if not isinstance(other, Polynomial):
            return False
        a, b = self._align_coeffs(self.coeffs, other.coeffs)
        return all(x == y for x, y in zip(a, b))
    
    def hash(self) -> int:
        return hash((self._container, tuple(self.coeffs)))

    def to_str(self) -> str:
        mono = []
        for i in range(len(self.coeffs)):
            coeff = self.coeffs[i]
            if coeff == 0:
                continue
            if i == 0:
                mono.append(str(coeff))
            else:
                if coeff == self._coeff_ring.one():
                    mono.append(f"x^{i}")
                else:
                    mono.append(f"{coeff}x^{i}")
        if not mono:
            mono.append(str(self._coeff_ring.zero()))
        return " + ".join(mono)

    def copy(self) -> Self:
        return Polynomial[T]([c for c in self.coeffs])

    # ---------- polynomial-specific ops ----------

    def degree(self) -> int:
        return len(self.coeffs) - 1

    def eval(self, x: T) -> T:
        cr = self._coeff_ring
        r = cr.zero()
        for a_i in reversed(self.coeffs):
            r = r * x + a_i
        return r

    def eval_all(self, xs: List[T]) -> List[T]:
        return [self.eval(x) for x in xs]

    def scale(self, s: T) -> Self:
        return Polynomial[T].of_scalar(s) * self

    # ---------- factories ----------

    @classmethod
    def of_scalar(cls, s: T) -> Self:
        return cls([s])

    @classmethod
    def of(cls, coeffs: List[T]) -> Self:
        return cls(coeffs)

    @classmethod
    def interpolate(cls, xs: List[T], ys: List[T]) -> Self:
        n = len(xs)
        if n == 0:
            raise ValueError("Need at least one point to interpolate")
        if n != len(ys):
            raise ValueError("Mismatched number of x and y values")
        if len(set(xs)) != n:
            raise ValueError("Duplicate x values not allowed")

        coeff_f = xs[0].container()
        if not isinstance(coeff_f, Field):
            raise ValueError("")
        if coeff_f != ys[0].container():
            raise ValueError("Mismatched coefficient fields")

        p = Polynomial[T].of_scalar(coeff_f.zero())
        z = Polynomial[T].of_scalar(coeff_f.one())

        for x_k, y_k in zip(xs, ys):
            k = (y_k - p.eval(x_k)) / z.eval(x_k)
            p = p + z.scale(k)
            z = z * Polynomial[T]([-x_k, coeff_f.one()])

        return p
