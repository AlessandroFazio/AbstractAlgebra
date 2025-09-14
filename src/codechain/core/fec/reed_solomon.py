from __future__ import annotations
from typing import List, Literal
import numpy as np

from codechain.core.algebra.gf256 import GF256

from abc import ABC, abstractmethod
from typing import List, Tuple

from codechain.core.base import Codec
from codechain.utils.binary import stable_hash


class BlockCodecStrategy(ABC):
    @abstractmethod
    def encode(self, data: bytes) -> bytes: ...
    @abstractmethod
    def decode(self, data: bytes, valid_indices: List[int], message_len: int) -> bytes: ...
    @abstractmethod
    def hash(self) -> int: ...
    @abstractmethod
    def eq(self, other: object) -> bool: ...
    
    def __hash__(self) -> int:
        return self.hash()
    
    def __eq__(self, other: object) -> bool:
        return self.eq(other)


class PolyBlockCodecStrategy(BlockCodecStrategy):
    """
    RS encode/decode via polynomial viewpoint:
      - encode: y_i = p(x_i)
      - decode: interpolate from any k valid (x_i, y_i)
    """
    def __init__(self, n: int, k: int) -> None:
        self.n = n
        self.k = k
        self.gf = GF256()
        # evaluation points: 0, exp[0],exp[1],..., distinct of length n
        xs = [np.uint8(0)]
        xs.extend(self.gf.exp[:255].tolist())
        self.xs = np.array(xs[:n], dtype=np.uint8)

    def encode(self, data: bytes) -> bytes:
        coeffs = np.frombuffer(data, dtype=np.uint8)
        cc = np.zeros(self.k, dtype=np.uint8)
        cc[:coeffs.size] = coeffs
        enc = self.gf.poly_eval(cc, self.xs)   # length n
        return enc.tobytes()

    def decode(self, data: bytes, valid_indices: List[int]) -> bytes:
        if len(valid_indices) < self.k:
            raise ValueError("insufficient symbols")
        cw = np.frombuffer(data, dtype=np.uint8)
        idx = np.array(valid_indices[:self.k], dtype=np.int64)
        xs = self.xs[idx]
        ys = cw[idx]
        coeffs = self.gf.poly_interpolate(xs, ys)  # length k
        return coeffs.tobytes()
    
    def hash(self) -> int:
        return stable_hash(("PolyBlockCodec", self.n, self.k))
    
    def eq(self, other: object) -> bool:
        return isinstance(other, PolyBlockCodecStrategy) and \
            self.n == other.n and \
            self.k == other.k


class LinAlgBlockCodecStrategy(BlockCodecStrategy):
    """
    RS via linear algebra:
      - Build Vandermonde V (nxk), take the top-left (kxk), invert to make systematic G.
    """
    def __init__(self, n: int, k: int) -> None:
        self.n = n
        self.k = k
        self.gf = GF256()
        xs = np.arange(n, dtype=np.uint8)
        V = self.gf.vander_mat(xs, k)                 # (n×k)
        Vk = V[:k, :k]                             # (k×k)
        Vk_inv = self.gf.inv_mat(Vk)               # GF inverse
        self.G = self.gf.matmul(V, Vk_inv)         # (n×k) generator (systematic)

    def encode(self, data: bytes) -> bytes:
        msg = np.frombuffer(data, dtype=np.uint8)
        v = np.zeros(self.k, dtype=np.uint8)
        v[:msg.size] = msg
        enc = self.gf.matmul(self.G, v.reshape(self.k, 1)).ravel()
        return enc.tobytes()

    def decode(self, data: bytes, valid_indices: List[int]) -> bytes:
        enc = np.frombuffer(data, dtype=np.uint8)
        idx = np.array(valid_indices[:self.k], dtype=np.int64)
        A = self.G[idx, :]                      # (k×k)
        b = enc[idx]                            # (k,)
        x = self.gf.solve(A, b)                 # (k,)
        return x.tobytes()
    
    def hash(self) -> int:
        return stable_hash(("LinAlgBlockCodec", self.n, self.k))
    
    def eq(self, other: object) -> bool:
        return isinstance(other, LinAlgBlockCodecStrategy) and \
            self.n == other.n and \
            self.k == other.k


class ReedSolomonCodec(Codec):
    def __init__(self, code_rate: float = 0.8, strategy: Literal["linalg","poly"] = "poly") -> None:
        n = 256
        k = max(min(int(code_rate * n), n-1), 1)
        self.n = n
        self.k = k
        self._block_codec = PolyBlockCodecStrategy(n, k) if strategy=="poly" else LinAlgBlockCodecStrategy(n, k)
        
    def encode(self, data: bytes) -> tuple[dict[str, bytes], bytes]:
        k = self.k
        msg_length = len(data)
        encoded = bytearray()
        for i in range(0, msg_length, k):
            encoded.extend(self._block_codec.encode(data[i:i + k]))
        meta = {"msg_length": msg_length.to_bytes(8, 'little')}
        return meta, bytes(encoded)

    def decode(self, meta: tuple[str, bytes], payload: bytes) -> bytes:
        n = self.n
        msg_length = int.from_bytes(meta["msg_length"], 'little')
        decoded = bytearray()
        valid = list(range(n)) # TODO: handle erasures 
        for i in range(0, len(payload), n):
            decoded.extend(self._block_codec.decode(payload[i:i + n], valid))
        return decoded[:msg_length]
    
    def hash(self) -> int:
        return stable_hash(("ReedSolomonCodec", self._block_codec.hash()))
    
    def eq(self, other: object) -> bool:
        return isinstance(other, ReedSolomonCodec) and self._block_codec.eq(other._block_codec)
    
    def _unpack_erasures(self, meta: dict[str, bytes]) -> List[Tuple[int, int]]:
        if "erasures" not in meta:
            return []
        raw = meta["erasures"]
        if len(raw) == 0:
            return []
        if len(raw) % 2:
            raise ValueError("incorrect format for erasures")
        return list(zip(raw[::2], raw[1::2]))
    
    def _erasures_from_existing(self, pairs: List[Tuple[int, int]], max_erasures: int) -> List[Tuple[int, int]]:
        valid = self._valid_from_erasures(pairs)
        to_erase = max_erasures - (self.n - len(valid))
        if to_erase > 0:
            to_erase = min(to_erase, len(valid) - 1)
            pairs.append((valid[0], valid[to_erase]))
        return pairs
    
    def _valid_from_erasures(self, pairs: List[Tuple[int, int]]) -> List[int]:
        if not pairs:
            return list(range(self.n))
        erased = set([i for s,e in pairs for i in range(s, e)])
        valid = [i for i in range(self.n) if i not in erased]
        if len(valid) < self.k:
            raise ValueError("not enough valid bytes after erasures in stream to decode message")
        return valid


    