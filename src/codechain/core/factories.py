from typing import Union, Optional
import os

# Your framework imports
from codechain.core.base import Codec
from codechain.core.pipeline import CodecPipeline

# Crypto primitives & modes
from codechain.core.crypto.ciphers.aes import AES
from codechain.core.crypto.ciphers.modes.ecb import ECBMode
from codechain.core.crypto.ciphers.modes.cbc import CBCMode
from codechain.core.crypto.sym import SymmetricCryptoCodec

# Padding schemes
from codechain.core.padding import PKCS7  # extend later (ansi-x923, iso7816)

# FEC
from codechain.core.fec.reed_solomon import ReedSolomonCodec

# Typed specs
from codechain.core.models import (
    CodecSpec,
    CodecPipelineSpec,
    SymmetricCryptoSpec,
    ReedSolomonCodecSpec,
    PaddingSpec,
)


# ---------- Padding Factory ----------
class PaddingFactory:
    @staticmethod
    def build(spec: Optional[PaddingSpec]):
        if spec is None:
            return PKCS7()  # sensible default for ECB/CBC
        if spec.kind == "pkcs7":
            return PKCS7()
        # TODO: add ANSI X.923, ISO/IEC 7816-4
        raise ValueError(f"Unsupported padding scheme {spec.kind}")


# ---------- BlockCipher+Mode Factory ----------
class BlockModeFactory:
    @staticmethod
    def build_aes_mode(key: bytes, mode: str, padding: Optional[PaddingSpec], iv: Optional[bytes]):
        aes = AES.from_key_bytes(key)
        pad = PaddingFactory.build(padding)
        if mode == "ecb":
            return ECBMode(aes, pad)
        if mode == "cbc":
            iv_final = iv or os.urandom(aes.block_size)
            return CBCMode(aes, pad, iv=iv_final)
        raise ValueError(f"Unsupported AES mode {mode}")


# ---------- StreamCipher Factory ----------
class StreamCipherFactory:
    @staticmethod
    def build(cipher: str, key: bytes, nonce: bytes, counter: int):
        raise NotImplementedError
        #if cipher == "chacha20":
        #    return ChaCha20(key=key, nonce=nonce, counter=counter)
        #raise ValueError(f"Unsupported stream cipher {cipher}")


# ---------- SymmetricCrypto Factory ----------
class SymmetricCryptoFactory:
    @staticmethod
    def build(spec: SymmetricCryptoSpec) -> SymmetricCryptoCodec:
        if spec.cipher == "aes":
            # AES requires mode; handled in model validation
            mode_cipher = BlockModeFactory.build_aes_mode(
                key=spec.key,
                mode=spec.mode,               # type: ignore[arg-type]
                padding=spec.padding,
                iv=spec.iv,
            )
            return SymmetricCryptoCodec(mode_cipher)

        if spec.cipher == "chacha20":
            sc = StreamCipherFactory.build(
                cipher="chacha20",
                key=spec.key,
                nonce=spec.nonce,             # type: ignore[arg-type]
                counter=spec.counter,
            )
            return SymmetricCryptoCodec(sc)

        raise ValueError(f"Unsupported symmetric cipher {spec.cipher}")


# ---------- Top-level Codec Factory ----------
class CodecFactory:
    @staticmethod
    def build(spec: CodecSpec) -> Codec:
        if isinstance(spec, SymmetricCryptoSpec):
            return SymmetricCryptoFactory.build(spec)
        if isinstance(spec, ReedSolomonCodecSpec):
            return ReedSolomonCodec(spec.code_rate, spec.codec_strategy)
        raise ValueError(f"Unsupported codec spec {type(spec).__name__}")


class CodecPipelineFactory:
    @staticmethod
    def build(spec: CodecPipelineSpec) -> CodecPipeline:
        return CodecPipeline([CodecFactory.build(s) for s in spec.codecs])
