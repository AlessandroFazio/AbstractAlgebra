import math
from typing import Generic, TypeVar, Union, Any, List, Tuple
from typing_extensions import Self
from abstract_algebra.core.fields.base import Field, FieldElem
from abstract_algebra.core.rings.base import Ring, RingElem


T = TypeVar('T', bound=FieldElem)


class MatrixRing(Ring[T]):
    def __init__(self, rows: int, cols: int, coeff_field: Field[T]) -> None:
        self.rows = rows
        self.cols = cols
        self.coeff_field = coeff_field

    def num_elems(self) -> int:
        coeff_size = self.coeff_field.num_elems()
        if coeff_size == -1:
            return -1
        return coeff_size ** (self.rows * self.cols)

    def elems(self) -> None:
        raise NotImplementedError

    def elem_of(self, x: FieldElem[T]) -> "Matrix[T]":
        raise NotImplementedError

    def one(self) -> "Matrix[T]":
        if self.rows != self.cols:
            raise RuntimeError("")
        return SquareMatrix.identity(self.rows, self.coeff_field)

    def zero(self):
        return Matrix.zero(self.rows, self.cols, self.coeff_field)

    def eq(self, other: object) -> bool:
        return isinstance(other, MatrixRing) and self.rows == other.rows and self.cols == other.cols
    
    def hash(self) -> int:
        return hash((self.rows, self.cols, self.coeff_field))

    def to_str(self) -> str:
        return f"M[{self.rows}, {self.cols}]"


class Matrix(RingElem[List[List[T]]], Generic[T]):
    def __init__(self, rows: int, cols: int, data: List[FieldElem[T]]) -> None:
        if rows < 0 or cols < 0:
            raise ValueError("")
        if not len(data):
            raise ValueError("")
        self.rows = rows
        self.cols = cols
        self.data = data
        self._coeff_field = data[0].container()
        super().__init__(MatrixRing[T](self.rows, self.cols, self._coeff_field))
        
    def shape(self) -> Tuple[int, int]:
        return (self.rows, self.cols)

    def add(self, rhs: Self) -> Self:
        assert self.shape() == rhs.shape()
        data = list(a + b for a,b in zip(self.data, rhs.data))
        return Matrix[T](self.rows, self.cols, data)
    
    def neg(self) -> Self:
        return Matrix(self.rows, self.cols, [-e for e in self.data])
    
    def mul(self, rhs: Self) -> Self:
        assert self.cols == rhs.rows
        m = self._container.zero()
        for i in range(self.rows):
            for j in range(rhs.cols):
                for k in range(self.cols):
                    m[i, j] += self[i, k] * rhs[k, j]
        return m
    
    def to_str(self) -> str:
        wrap = lambda s: f"[{s}]"
        def row_to_str(i: int) -> str:
            return wrap(" ".join(str(self[i, j]) for j in range(self.cols)))
        return wrap("\n".join(row_to_str(i) for i in range(self.rows)))
    
    def copy(self, shallow: bool=True) -> Self:
        data = None
        if shallow:
            data = [d for d in self.data]
        else:
            data = [d.copy() for d in self.data]
        return Matrix[T](self.rows, self.cols, data)
    
    def eq(self, other: object) -> bool:
        return isinstance(other, Matrix) and \
            self.rows == other.rows and \
            self.cols == other.cols and \
            all(a == b for a,b in zip(self.data, other.data))
            
    def hash(self) -> int:
        return hash((self._container, tuple(self.data)))
    
    def _offset(self, r: int, c: int) -> int:
        return self.cols * r + c
    
    def _check_idx(self, key: Any) -> tuple:
        if not isinstance(key, tuple) or len(key) != 2:
            raise IndexError("Matrix requires two indices")
        return key
    
    def _normalize_idx(self, idx: Union[int, slice], size: int) -> range:
        """Turn an int or slice into a range of indices."""
        if isinstance(idx, int):
            # normalize negative indices
            if idx < 0:
                idx += size
            if idx < 0 or idx >= size:
                raise IndexError("index out of range")
            return range(idx, idx + 1)
        elif isinstance(idx, slice):
            return range(*idx.indices(size))
        else:
            raise TypeError("indices must be int or slice")
        
    def _slice(self, r_range: range, c_range: range) -> Self:
        rows, cols = 0, 0
        data = []
        for i in r_range:
            for j in c_range:
                e = self.data[self._offset(i, j)]
                data.append(e)
        return Matrix[T](rows, cols, data)
    
    def __getitem__(self, key: tuple) -> Union[FieldElem[T], Self]:
        r_idx, c_idx = self._check_idx(key)
        r_range = self._normalize_idx(r_idx, self.rows)
        c_range = self._normalize_idx(c_idx, self.cols)
        if isinstance(r_idx, int) and isinstance(c_idx, int):
            i = self._offset(r_idx, c_idx)
            return self.data[i]
        return self._slice(r_range, c_range)
    
    def __setitem__(self, key: tuple, value: FieldElem[T]) -> None:
        r_idx, c_idx = self._check_idx(key)
        assert isinstance(r_idx, int) and isinstance(c_idx, int)
        assert isinstance(value, FieldElem)
        i = self._offset(r_idx, c_idx)
        self.data[i] = value
    
    @classmethod
    def zero(cls, rows: int, cols: int, coeff_field: Field[T]) -> Self:
        return cls(rows, cols, [coeff_field.zero() for _ in range(rows * cols)])
    
    @classmethod
    def from_rows(cls, row_data: List[List[FieldElem[T]]]) -> Self:
        rows = len(row_data)
        cols = 0
        if rows == 0:
            raise ValueError("")
        for col in row_data:
            if cols == 0:
                cols = len(col)
            else:
                if cols != len(col):
                    raise ValueError()
        if cols == 0:
            raise ValueError()
        return cls(rows, cols, [c for r in row_data for c in r])
    

class SquareMatrix(Matrix[T], FieldElem[T]):
    def __init__(self, data: List[FieldElem[T]]) -> None:
        n = math.sqrt(len(data))
        if not n.is_integer():
            raise ValueError("")
        super().__init__(n, n, data)
        self._lu_factor: Tuple[Self, Self, List[int]] = None
    
    def _compute_lu(self) -> Tuple[List[int], Self, Self]:
        rows, cols = self.rows, self.cols
        A = self.copy()
        L = self.zero(rows, cols, self._coeff_field)
        U = self.zero(rows, cols, self._coeff_field)
        P = [i for i in range(rows)]
        
        for k in range(cols):
            found = False
            for i in range(k, rows):
                if A[P[i], k] != self._coeff_field.zero():
                    if i != k:
                        P[k], P[i] = P[i], P[k]
                    found = True
                    break
            
            if not found:
                raise ArithmeticError("Matrix is singular, cannot perform PLU factorization")
            
            pivot = A[P[k], k]
            
            for j in range(cols):
                U[k, j] = A[P[k], j]
                
            L[P[k], k] = self._coeff_field.one()
            for i in range(k+1, rows):
                L[P[i], k] = A[P[i], k] / pivot
                
            for i in range(k+1, rows):
                m = L[P[i], k]
                for j in range(k+1, cols):
                    A[P[i], j] -= m * A[P[k], j]
        
        return P, L, U
    
    def _solve_lower(self, L: Self, b: Self, permute: List[int]) -> "Matrix[T]":
        assert b.cols == 1
        assert b.rows == L.rows
        
        n = L.rows
        b = b.copy()
        y = Matrix[T].zero(n, 1, self._coeff_field)
        for j in range(n):
            elt = b[permute[j], 0] / L[permute[j], j]
            y[j, 0] = elt
            
            for i in range(j+1, n):
                b[permute[i], 0] -= L[permute[i], j] * elt
        
        return y

    def _solve_upper(self, U: Self, y: Self) -> "Matrix[T]":
        assert y.rows == U.rows
        assert y.cols == 1
        
        n = U.rows
        y = y.copy()
        x = Matrix[T].zero(n, 1, self._coeff_field)
        for j in reversed(range(n)):
            elt = y[j, 0] / U[j, j]
            x[j, 0] = elt
            
            for i in reversed(range(0, j)):
                y[i, 0] -= U[i, j] * elt
                
        return x
    
    def lu_factor(self) -> Tuple[Self, Self, List[int]]:
        if not self._lu_factor:
            self._lu_factor = self._compute_lu()
        return self._lu_factor
    
    def solve(self, b: Self) -> "Matrix[T]":
        assert b.cols == 1
        assert self.rows == b.rows
        P, L, U = self.lu_factor()
        y = self._solve_lower(L, b, P)
        x = self._solve_upper(U, y)
        return x
    
    def invert(self) -> Self:
        n = self.rows
        inv = self.zero(n, n, self._coeff_field)
        for j in range(n):
            b = self.zero(n, 1, self._coeff_field)
            b[j, 0] = self._coeff_field.one()
            x = self.solve(b)
            for i in range(n):
                inv[i, j] = x[i, 0]
        return inv
    
    def divmod(self, rhs: Self) -> Tuple[Self, Self]:
        return self * rhs.invert(), self.zero(self.rows, self.cols, self._coeff_field)
    
    @classmethod
    def identity(cls, n: int, coeff_field: Field[T]) -> Self:
        data = [coeff_field.zero() for _ in range(n ** 2)]
        for i in range(0, n ** 2, n):
            data[i] = coeff_field.one()
        return cls(data)