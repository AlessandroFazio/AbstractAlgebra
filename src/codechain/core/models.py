from typing import List, Literal, Optional, Union
from typing_extensions import Self
from pydantic import BaseModel, Field, model_validator


# ---------- Common ----------
class PaddingSpec(BaseModel):
    kind: Literal["pkcs7", "ansi-x923", "iso7816"] = "pkcs7"


# ---------- Symmetric Crypto (flat shape) ----------
class SymmetricCryptoSpec(BaseModel):
    """
    Flat, user-friendly schema:

    kind: symmetric_crypto
    cipher: "aes" | "chacha20"
    # AES branch:
      mode: "ecb" | "cbc"              # required for AES
      key: bytes                        # required
      iv: bytes (optional; req when mode=cbc unless factory generates)
      padding: PaddingSpec (optional; default pkcs7)
    # ChaCha20 branch:
      nonce: bytes (required)
      counter: int = 1 (optional)
    """
    kind: Literal["symmetric_crypto"]

    cipher: Literal["aes", "chacha20"]
    key: bytes

    # AES (block-cipher) branch
    mode: Optional[Literal["ecb", "cbc"]] = None
    iv: Optional[bytes] = None
    padding: Optional[PaddingSpec] = None

    # ChaCha20 (stream-cipher) branch
    nonce: Optional[bytes] = None
    counter: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def validate_branch(self) -> Self:
        if self.cipher == "aes":
            # AES requires a mode; must not provide stream-only params
            if self.mode is None:
                raise ValueError("AES requires 'mode' ('ecb' or 'cbc').")
            if self.nonce is not None:
                raise ValueError("'nonce' is invalid for AES.")
            # CBC may need an IV (we allow factory to generate if missing)
            # padding defaulting handled by factory
        elif self.cipher == "chacha20":
            # Stream cipher must NOT have a mode/iv/padding
            if self.mode is not None:
                raise ValueError("'mode' is invalid for ChaCha20.")
            if self.iv is not None:
                raise ValueError("'iv' is invalid for ChaCha20.")
            if self.padding is not None:
                raise ValueError("'padding' is invalid for ChaCha20.")
            if self.nonce is None:
                raise ValueError("ChaCha20 requires 'nonce'.")
        else:
            raise ValueError(f"Unsupported cipher: {self.cipher}")
        return self


# ---------- Reed–Solomon ----------
class ReedSolomonCodecSpec(BaseModel):
    kind: Literal["reed_solomon"]
    code_rate: float = 0.80
    codec_strategy: Literal["poly", "linalg"] = "poly"

    @model_validator(mode="after")
    def check_code_rate(self) -> Self:
        if not (0.0 < self.code_rate < 1.0):
            raise ValueError("code_rate must be in (0,1).")
        return self


# ---------- Union & Pipeline ----------
CodecSpec = Union[SymmetricCryptoSpec, ReedSolomonCodecSpec]


class CodecPipelineSpec(BaseModel):
    codecs: List[CodecSpec] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_not_empty(self) -> Self:
        if not self.codecs:
            raise ValueError("codecs spec list cannot be empty")
        return self
