from typing import TypeVar, Union, Any, List, Tuple
from typing_extensions import Self
from abstract_algebra.core.groups.fields.base import Field, FieldElem
from abstract_algebra.core.groups.rings.base import RingElem


T = TypeVar('T')

class Matrix(RingElem[T]):
    def __init__(self, rows: int, cols: int, data: List[FieldElem[T]], coeff_field: Field[T]) -> None:
        self.rows = rows
        self.cols = cols
        self.data = data
        self.coeff_field = coeff_field
        self._lu_factor: Tuple["Self[T]", "Self[T]", List[int]] = None
        
    def shape(self) -> Tuple[int, int]:
        return (self.rows, self.cols)

    def add(self, rhs: "Self[T]") -> "Self[T]":
        assert self.shape() == rhs.shape()
        data = list(a + b for a,b in zip(self.data, rhs.data))
        return Matrix[T](self.rows, self.cols, data, self.coeff_field)
    
    def neg(self) -> "Self[T]":
        return Matrix(self.rows, self.cols, [-e for e in self.data], self.coeff_field)
    
    def mul(self, rhs: "Self[T]") -> "Self[T]":
        assert self.cols == rhs.rows
        m = self.zero(self.rows, rhs.cols, self.coeff_field)
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
    
    def copy(self, shallow: bool=True) -> "Self[T]":
        data = None
        if shallow:
            data = [d for d in self.data]
        else:
            data = [d.copy() for d in self.data]
        return Matrix[T](self.rows, self.cols, data, self.coeff_field)
    
    def eq(self, other: object) -> bool:
        return isinstance(other, Matrix) and \
            self.rows == other.rows and \
            self.cols == other.cols and \
            all(a == b for a,b in zip(self.data, other.data))
    
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
        
    def _slice(self, r_range: range, c_range: range) -> "Self[T]":
        rows, cols = 0, 0
        data = []
        for i in r_range:
            for j in c_range:
                e = self.data[self._offset(i, j)]
                data.append(e)
        return Matrix[T](rows, cols, data, self.coeff_field)
    
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
    def zero(cls, rows: int, cols: int, coeff_field: Field[T]) -> "Self[T]":
        return cls(rows, cols, [coeff_field.zero() for _ in range(rows * cols)], coeff_field)
    
    @classmethod
    def from_rows(cls, row_data: List[List[FieldElem[T]]], field: Field[T]) -> "Self[T]":
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
        return cls(rows, cols, [c for r in row_data for c in r], field)
    

class SquareMatrix(Matrix[T], FieldElem[T]):
    def __init__(self, rows: int, cols: int, data: List[FieldElem[T]], coeff_field: Field[T]) -> None:
        super().__init__(rows, cols, data, coeff_field)
        if self.rows != self.cols:
            raise ValueError("")
    
    def _compute_lu(self) -> Tuple[List[int], "Self[T]", "Self[T]"]:
        rows, cols = self.rows, self.cols
        A = self.copy()
        L = self.zero(rows, cols, self.coeff_field)
        U = self.zero(rows, cols, self.coeff_field)
        P = [i for i in range(rows)]
        
        for k in range(cols):
            found = False
            for i in range(k, rows):
                if A[P[i], k] != self.coeff_field.zero():
                    if i != k:
                        P[k], P[i] = P[i], P[k]
                    found = True
                    break
            
            if not found:
                raise ArithmeticError("Matrix is singular, cannot perform PLU factorization")
            
            pivot = A[P[k], k]
            
            for j in range(cols):
                U[k, j] = A[P[k], j]
                
            L[P[k], k] = self.coeff_field.one()
            for i in range(k+1, rows):
                L[P[i], k] = A[P[i], k] / pivot
                
            for i in range(k+1, rows):
                m = L[P[i], k]
                for j in range(k+1, cols):
                    A[P[i], j] = A[P[i], j] - m * A[P[k], j]
        
        return P, L, U
    
    def _solve_lower(self, L: "Self[T]", b: "Self[T]", permute: List[int]) -> "Matrix[T]":
        assert b.cols == 1
        assert b.rows == L.rows
        
        n = L.rows
        b = b.copy()
        y = Matrix[T].zero(n, 1, self.coeff_field)
        for j in range(n):
            elt = b[permute[j], 0] / L[permute[j], j]
            y[j, 0] = elt
            
            for i in range(j+1, n):
                b[permute[i], 0] = b[permute[i], 0] - L[permute[i], j] * elt
        
        return y

    def _solve_upper(self, U: "Self[T]", y: "Self[T]") -> "Matrix[T]":
        assert y.rows == U.rows
        assert y.cols == 1
        
        n = U.rows
        y = y.copy()
        x = Matrix[T].zero(n, 1, self.coeff_field)
        for j in reversed(range(n)):
            elt = y[j, 0] / U[j, j]
            x[j, 0] = elt
            
            for i in reversed(range(0, j)):
                y[i, 0] = y[i, 0] - U[i, j] * elt
                
        return x
    
    def lu_factor(self) -> Tuple["Self[T]", "Self[T]", List[int]]:
        if not self._lu_factor:
            self._lu_factor = self._compute_lu()
        return self._lu_factor
    
    def solve(self, b: "Self[T]") -> "Matrix[T]":
        assert b.cols == 1
        assert self.rows == b.rows
        P, L, U = self.lu_factor()
        y = self._solve_lower(L, b, P)
        x = self._solve_upper(U, y)
        return x
    
    def invert(self) -> "Self[T]":
        n = self.rows
        inv = self.zero(n, n, self.coeff_field)
        for j in range(n):
            b = self.zero(n, 1, self.coeff_field)
            b[j, 0] = self.coeff_field.one()
            x = self.solve(b)
            for i in range(n):
                inv[i, j] = x[i, 0]
        return inv
    
    def divmod(self, rhs: "Self") -> Tuple["Self", "Self"]:
        return self * rhs.invert(), self.zero(self.rows, self.cols, self.coeff_field)
    
    @classmethod
    def identity(cls, n: int, coeff_field: Field[T]) -> "Self[T]":
        data = [coeff_field.zero() for _ in range(n ** 2)]
        for i in range(0, n ** 2, n):
            data[i] = coeff_field.one()
        return cls(n, n, data, coeff_field)