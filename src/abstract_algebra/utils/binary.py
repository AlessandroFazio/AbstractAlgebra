class BinaryUtils:
    @classmethod
    def bit_at(cls, n: int, i: int) -> int:
        return (n >> i) & 1
    
    @classmethod
    def byte_length(cls, n: int) -> int:
        return (n.bit_length() + 7) // 8