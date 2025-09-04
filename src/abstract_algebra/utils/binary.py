class BinaryUtils:
    @classmethod
    def bit_at(cls, n: int, i: int) -> int:
        return (n >> i) & 1