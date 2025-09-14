import numpy as np


_Q = 0x11B
_PRIM = 0x03

class GF256:
    def __init__(self, Q: int = _Q, prim: int = _PRIM) -> None:
        self.Q = Q
        self.prim = prim
        self._build_tables()

    def _build_tables(self) -> None:
        exp = np.zeros(510, dtype=np.uint8)
        log = np.full(256, -1, dtype=np.int16)     # NOTE int16 to hold -1
        x = 1
        for i in range(255):
            exp[i] = x
            log[x] = i
            x = self._mul(x, self.prim)
        
        exp[255:] = exp[:255]
        self.exp = exp 
        self.log = log
        
    def _mul(self, a: int, b: int) -> int:
        r = 0
        while b:
            if b & 1:
                r ^= a
            b >>= 1
            a = self._xtime(a)
        return r
        
    def _xtime(self, x: int) -> int:
        x <<= 1
        if x & 0x100:
            x ^= self.Q
        return x & 0xFF

    # ---- elementwise field ops (broadcasting-friendly) ----

    @staticmethod
    def add(a: np.ndarray | np.uint8, b: np.ndarray | np.uint8) -> np.ndarray:
        # GF(2) addition = XOR
        return np.bitwise_xor(a, b, dtype=np.uint8)

    def mul(self, a: np.ndarray | np.uint8, b: np.ndarray | np.uint8) -> np.ndarray:
        a = np.asarray(a, dtype=np.uint8)
        b = np.asarray(b, dtype=np.uint8)
        la = self.log[a]
        lb = self.log[b]
        zero = (la < 0) | (lb < 0)
        out = self.exp[la + lb]
        if np.isscalar(out):
            return np.uint8(0) if zero else np.uint8(out)
        return np.where(zero, 0, out).astype(np.uint8)

    def inv(self, a: np.ndarray | np.uint8) -> np.ndarray:
        a = np.asarray(a, dtype=np.uint8)
        la = self.log[a]
        if a.ndim == 0:
            return np.uint8(0) if la < 0 else self.exp[(255 - la) % 255]
        out = np.zeros_like(a, dtype=np.uint8)
        nz = la >= 0
        out[nz] = self.exp[(255 - la[nz]) % 255]
        return out

    def div(self, a: np.ndarray | np.uint8, b: np.ndarray | np.uint8) -> np.ndarray:
        a = np.asarray(a, dtype=np.uint8)
        b = np.asarray(b, dtype=np.uint8)
        la = self.log[a]
        lb = self.log[b]
        zero = (la < 0) | (lb < 0)
        out = self.exp[(la - lb) % 255]
        if np.isscalar(out):
            return np.uint8(0) if zero else out.astype(np.uint8)
        return np.where(zero, 0, out).astype(np.uint8)

    # ---- polynomials over GF(256) ----

    # Horner with coeffs in increasing degree [c0,c1,...,c_{k-1}]
    def poly_eval(self, coeffs: np.ndarray, xs: np.ndarray) -> np.ndarray:
        coeffs = np.asarray(coeffs, dtype=np.uint8)
        xs = np.asarray(xs, dtype=np.uint8)
        y = np.zeros(xs.shape, dtype=np.uint8)
        for c in coeffs:              # highest degree first
            y = self.mul(y, xs)
            y = self.add(y, c)
        return y

    def _poly_mul_linear_monic(self, P: np.ndarray, a: int) -> np.ndarray:
        n = P.size
        out = np.empty(n + 1, dtype=np.uint8)
        out[0] = P[0]
        for i in range(1, n):
            out[i] = self.add(P[i], self.mul(P[i-1], a))
        out[-1] = self.mul(a, P[-1])
        return out
    
    def _poly_build_prod(self, xs: np.ndarray) -> np.ndarray:
        P = np.array([1], dtype=np.uint8)
        for a in xs:
           P = self._poly_mul_linear_monic(P, a)
        return P

    def _poly_synth_div_monic(self, P: np.ndarray, a: np.uint8) -> np.ndarray:
        # Quotient Q(z) = P(z)/(z - a), length len(P)-1
        m = P.size - 1
        Q = np.empty(m, dtype=np.uint8)
        Q[0] = P[0]
        for i in range(1, m):
            Q[i] = self.add(P[i], self.mul(a, Q[i-1]))
        return Q

    def poly_interpolate(self, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
        # Lagrange via global product; returns coeffs length n, degree < n
        xs = np.asarray(xs, dtype=np.uint8)
        ys = np.asarray(ys, dtype=np.uint8)
        n = xs.size
        
        if np.unique(xs).size != n:
            raise ValueError("Interpolation nodes must be distinct")
        if ys.size != n:
            raise ValueError("xs and ys must have same length")
        
        P = self._poly_build_prod(xs)           # ∏(z - x_i), length n+1
        coeffs = np.zeros(n, dtype=np.uint8)
        for i in range(n):
            xi = xs[i]
            Pi = self._poly_synth_div_monic(P, xi)   # length n
            denom = self.poly_eval(Pi, np.array([xi], dtype=np.uint8))[0]  # P_i(x_i)
            if denom == 0:
                raise ZeroDivisionError("P_i(x_i)=0 (duplicate node)")
            wi = self.inv(denom)                     # 1 / P_i(x_i)
            scale = self.mul(ys[i], wi)              # y_i * w_i
            coeffs = self.add(coeffs, self.mul(Pi, scale))
        return coeffs

    # Vandermonde with increasing powers (n×k)
    def vander_mat(self, xs: np.ndarray, k: int) -> np.ndarray:
        xs = np.asarray(xs, dtype=np.uint8)
        n = xs.size
        VT = np.ones((k, n), dtype=np.uint8)
        for i in range(1, k):
            VT[i, :] = self.mul(VT[i-1, :], xs)     # geometric progression rowwise
        return VT.T

    # ---- GF(256) linear algebra (vectorized) ----

    def matmul(self, A: np.ndarray, B: np.ndarray) -> np.ndarray:
        # (m×p) @ (p×n) over GF(256)
        A = np.asarray(A, dtype=np.uint8)
        B = np.asarray(B, dtype=np.uint8)
        m, p = A.shape
        p2, n = B.shape
        assert p == p2
        C = np.zeros((m, n), dtype=np.uint8)
        # accumulate outer products A[:,t] * B[t,:]
        for t in range(p):
            C = self.add(C, self.mul(A[:, t:t+1], B[t:t+1, :]))
        return C

    def solve(self, A: np.ndarray, b: np.ndarray) -> np.ndarray:
        # Gaussian elimination (Gauss–Jordan) over GF(256), b is (n,) or (n,1)
        A = np.asarray(A, dtype=np.uint8).copy()
        b = np.asarray(b, dtype=np.uint8).copy()
        n = A.shape[0]
        if b.ndim == 1:
            b = b.reshape(n, 1)

        for k in range(n):
            # pivot search
            pivot = -1
            for i in range(k, n):
                if A[i, k] != 0:
                    pivot = i
                    break
            if pivot < 0:
                raise ArithmeticError("singular")
            if pivot != k:
                A[[k, pivot]] = A[[pivot, k]]
                b[[k, pivot]] = b[[pivot, k]]
            inv_p = self.inv(A[k, k])
            A[k, :] = self.mul(A[k, :], inv_p)
            b[k, :] = self.mul(b[k, :], inv_p)
            # eliminate other rows
            for i in range(n):
                if i == k: 
                    continue
                if A[i, k] != 0:
                    factor = A[i, k]
                    A[i, :] = self.add(A[i, :], self.mul(factor, A[k, :]))
                    b[i, :] = self.add(b[i, :], self.mul(factor, b[k, :]))
        return b.ravel() if b.shape[1] == 1 else b

    def inv_mat(self, A: np.ndarray) -> np.ndarray:
        A = np.asarray(A, dtype=np.uint8)
        n = A.shape[0]
        I = np.eye(n, dtype=np.uint8)
        X = self.solve(A, I)
        return X