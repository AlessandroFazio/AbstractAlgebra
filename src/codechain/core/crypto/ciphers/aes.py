from functools import reduce
from typing import Callable
from typing_extensions import Self
import numpy as np

from codechain.core.algebra.gf256 import GF256
from codechain.core.crypto.base import BlockCipher
from codechain.utils.binary import stable_hash


class AES(BlockCipher):
    _SUPPORTED_NK = {4, 6, 8}
    _NK_TO_NR = {
        4: 10, 
        6: 12, 
        8: 14
    }
    
    def __init__(self, K: np.ndarray, Nb: int, Nr: int) -> None:
        self._K = K
        self._Nb = Nb
        self._Nr = Nr
        self._Nk = self._K.shape[1]
        self._ax = np.array([0x02, 0x01, 0x01, 0x03], dtype=np.uint8)
        self._inv_ax = np.array([0x0e, 0x09, 0x0d, 0x0b], dtype=np.uint8)
        self._gf = GF256()
        self._build_SB()
        self._build_SR()
        self._build_M()
        self._build_T()
        self._build_K_sched()
        
    def _build_SB_idx_tlu(self) -> np.ndarray:
        tlu = np.empty((8, 4), dtype=np.uint8)
        for i in range(8):
            tlu[i, :] = np.fromiter(((i + j + 4) % 8 for j in range(4)), dtype=np.uint8)
        return tlu
        
    def _build_SB(self) -> None:
        SB = np.arange(256, dtype=np.uint8)
        inv_SB = np.empty_like(SB)
        idx_tlu = self._build_SB_idx_tlu()

        for i in range(256):
            inv = self._gf.inv(np.uint8(i))
            y = 0
            for bit in range(8):
                b = (inv >> bit) & 1
                for j in range(4):
                    b ^= (inv >> idx_tlu[bit, j]) & 1
                b ^= (0x63 >> bit) & 1
                y |= (b << bit)
            SB[i] = y
            inv_SB[y] = i

        self._SB = SB
        self._inv_SB = inv_SB
        
    def _build_Rcon(self) -> np.ndarray:
        Rcon = np.zeros((self._Nr + 1, 4), dtype=np.uint8)
        x = 1
        for i in range(1, self._Nr + 1):
            Rcon[i, 0] = x
            x = self._gf.mul(x, np.uint8(2))
        return Rcon

    def _build_K_sched(self) -> None:
        Nb, Nk, Nr = self._Nb, self._Nk, self._Nr
        nwords = Nb * (Nr + 1)
        Rcon = self._build_Rcon()
        K_sched = np.empty((4, nwords), dtype=np.uint8)
        K_sched[:, :Nk] = self._K[:, :]
        
        for r in range(Nk, nwords):
            tmp = K_sched[:, r-1]
            if r % Nk == 0:
                tmp = self._gf.add(self._sub_word(self._rot_word(tmp)), Rcon[r // Nk])
            elif self._Nk > 6 and r % self._Nk == 4:
                tmp = self._sub_word(tmp)
            K_sched[:, r] = self._gf.add(K_sched[:, r - Nk], tmp)
        
        K_sched = K_sched.reshape(4, Nr + 1, Nb).transpose(0, 2, 1)
        self._K_sched = K_sched
        
        inv_K_sched = np.copy(K_sched)
        for r in range(1, Nr):
            inv_K_sched[:, :, r] = self._gf.matmul(self._inv_M, inv_K_sched[:, :, r])
        self._inv_K_sched = inv_K_sched
    
    def _build_SR(self) -> None:
        Nb = self._Nb
        indices = np.arange(Nb, dtype=np.uint8)
        SR = np.empty((Nb, Nb), dtype=np.uint8)
        inv_SR = np.empty((Nb, Nb), dtype=np.uint8)
        
        for i in range(4):
            SR[i, :] = (indices + i) % Nb
            inv_SR[i, :] = (indices - i) % Nb
        
        self._SR = SR
        self._inv_SR = inv_SR
        
    def _build_M(self) -> None:
        indices = np.arange(4, dtype=np.uint8)
        M = np.empty((4, 4), dtype=np.uint8)
        inv_M = np.empty((4, 4), dtype=np.uint8)
        
        for i in range(4):
            idx = (i - indices) % 4
            M[i, :] = self._ax[idx]
            inv_M[i, :] = self._inv_ax[idx]
        
        self._M = M
        self._inv_M = inv_M
        
    def _build_T(self) -> None:
        T = np.empty((4, 256, 4), dtype=np.uint8)
        inv_T = np.empty((4, 256, 4), dtype=np.uint8)
        for r in range(4):
            v = self._M[:, r]
            inv_v = self._inv_M[:, r]
            T[r, :, :] = self._gf.mul(self._SB[:, None], v[None, :])
            inv_T[r, :, :] = self._gf.mul(self._inv_SB[:, None], inv_v[None, :])
        self._T = T
        self._inv_T = inv_T
        
    def _do_lookup_T_table(self, S: np.ndarray, T: np.ndarray, shift_fn: Callable[[int, int], int]) -> np.ndarray:
        S_new = np.empty_like(S, dtype=np.uint8)
        for c in range(self._Nb):
            col = (T[r, S[r, shift_fn(r, c)]] for r in range(4))
            S_new[:, c] = reduce(self._gf.add, col)
        return S_new
    
    def _lookup_T(self, S: np.ndarray) -> np.ndarray:
        return self._do_lookup_T_table(S, self._T, lambda r, c: (c + r) % 4)
    
    def _inv_lookup_T(self, S: np.ndarray) -> np.ndarray:
        return self._do_lookup_T_table(S, self._inv_T, lambda r, c: (c - r) % 4)
    
    def _sub_word(self, w: np.ndarray) -> np.ndarray:
        return self._SB[w[:]]
    
    def _rot_word(self, w: np.ndarray) -> np.ndarray:
        out = np.empty_like(w, dtype=np.uint8)
        out[:-1] = w[1:]
        out[-1] = w[0]
        return out
    
    def _add_round_key(self, S: np.ndarray, round: int) -> np.ndarray:
        return self._gf.add(S, self._K_sched[:, :, round])
    
    def _inv_add_round_key(self, S: np.ndarray, round: int) -> np.ndarray:
        return self._gf.add(S, self._inv_K_sched[:, :, round])
    
    def _sub_bytes(self, S: np.ndarray) -> np.ndarray:
        return self._SB[S]
    
    def _shift_rows(self, S: np.ndarray) -> np.ndarray:
        r = np.arange(4)[:, None]
        return S[r, self._SR]
    
    def _mix_columns(self, S: np.ndarray) -> np.ndarray:
        return self._gf.matmul(self._M, S)
    
    def _inv_sub_bytes(self, S: np.ndarray) -> np.ndarray:
        return self._inv_SB[S]
    
    def _inv_shift_rows(self, S: np.ndarray) -> np.ndarray:
        r = np.arange(4)[:, None]
        return S[r, self._inv_SR]
    
    def _inv_mix_columns(self, S: np.ndarray) -> np.ndarray:
        return self._gf.matmul(self._inv_M, S)
        
    def encrypt(self, plaintext: bytes) -> bytes:
        Nb, Nr = self._Nb, self._Nr
        
        if len(plaintext) != 4 * Nb:
            raise ValueError("")
        
        S = self._buffer_to_words(plaintext, Nb)
        S = self._add_round_key(S, 0)
        
        for i in range(1, Nr):
            S = self._lookup_T(S)
            S = self._add_round_key(S, i)
        
        S = self._sub_bytes(S)
        S = self._shift_rows(S)
        S = self._add_round_key(S, Nr)
        
        return self._words_to_buffer(S)
            
    def decrypt(self, ciphertext: bytes) -> bytes:
        Nb, Nr = self._Nb, self._Nr
        
        if len(ciphertext) != 4 * Nb:
            raise ValueError("")
        
        S = self._buffer_to_words(ciphertext, Nb)
        S = self._inv_add_round_key(S, Nr)
        
        for i in reversed(range(1, Nr)):
            S = self._inv_lookup_T(S)
            S = self._inv_add_round_key(S, i)
        
        S = self._inv_shift_rows(S)
        S = self._inv_sub_bytes(S)
        S = self._inv_add_round_key(S, 0)
        
        return self._words_to_buffer(S)
    
    def hash(self) -> int:
        return stable_hash((f"AES-{self._Nk * 32}", self._K.tobytes()))
    
    def eq(self, other: object) -> bool:
        return isinstance(other, AES) and np.array_equal(self._K, other._K)
    
    @classmethod
    def _buffer_to_words(cls, buf: bytes, nwords: int) -> np.ndarray:
        return np.frombuffer(buf, dtype=np.uint8).reshape(nwords, 4).T
    
    @classmethod
    def _words_to_buffer(cls, w: np.ndarray) -> bytes:
        return w.T.flatten().tobytes()
    
    @classmethod
    def from_key_bytes(cls, key_bytes: bytes) -> Self:
        key_bits = len(key_bytes) * 8
        key_err_msg = f"Invalid cipher key. Length must be of 128, 192 or 256 bits, got '{key_bits}'"
        
        if key_bits % 32 != 0:
            raise ValueError(key_err_msg)
        
        Nk = key_bits // 32
        if Nk not in cls._SUPPORTED_NK:
            raise ValueError(key_err_msg)
        
        Nr = cls._NK_TO_NR[Nk]
        K = cls._buffer_to_words(key_bytes, Nk)
        return cls(K, 4, Nr)
    