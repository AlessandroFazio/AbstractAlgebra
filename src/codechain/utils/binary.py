def bit_at(n: int, i: int) -> int:
        return (n >> i) & 1

def byte_length(n: int) -> int:
    return (n.bit_length() + 7) // 8


import hashlib
import pickle
from typing import Any

def stable_hash(obj: Any) -> int:
    """
    Deterministic hash of arbitrary Python objects, stable across runs and platforms.
    Uses SHA-256 under the hood and truncates to a Python int.
    """
    # Pickle object with highest protocol (ensures consistent serialization)
    data = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
    # Compute SHA-256
    digest = hashlib.sha256(data).digest()
    # Convert first 8 bytes into int
    return int.from_bytes(digest[:8], "big", signed=False)