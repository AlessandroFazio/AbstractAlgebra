import unittest
from codechain.core.crypto.ciphers.aes import AES


class TestAES(unittest.TestCase):

    def _run_vector(self, key_hex: str, pt_hex: str, ct_hex: str):
        key = bytes.fromhex(key_hex)
        pt = bytes.fromhex(pt_hex)
        expected_ct = bytes.fromhex(ct_hex)

        aes = AES.from_key_bytes(key)

        ct = aes.encrypt(pt)
        self.assertEqual(
            ct, expected_ct,
            f"AES-{len(key)*8} encryption mismatch! Got {ct.hex()}, expected {ct_hex}"
        )

        dec = aes.decrypt(ct)
        self.assertEqual(
            dec, pt,
            f"AES-{len(key)*8} decryption mismatch! Got {dec.hex()}, expected {pt_hex}"
        )

    def test_aes128(self):
        self._run_vector(
            "000102030405060708090a0b0c0d0e0f",
            "00112233445566778899aabbccddeeff",
            "69c4e0d86a7b0430d8cdb78070b4c55a"
        )

    def test_aes192(self):
        self._run_vector(
            "000102030405060708090a0b0c0d0e0f1011121314151617",
            "00112233445566778899aabbccddeeff",
            "dda97ca4864cdfe06eaf70a0ec0d7191"
        )

    def test_aes256(self):
        self._run_vector(
            "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f",
            "00112233445566778899aabbccddeeff",
            "8ea2b7ca516745bfeafc49904b496089"
        )


if __name__ == "__main__":
    unittest.main()
