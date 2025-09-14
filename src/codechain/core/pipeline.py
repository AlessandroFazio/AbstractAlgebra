import struct
from typing import Dict, Iterator, Optional, Sequence, Tuple

from codechain.core.base import Codec
from codechain.core.checksum.crc import CRC


class Framer:
    """Encodes/decodes frames as TLV sequences with MAGIC header."""

    _MAGIC = b"CFP1"

    _TAG_CODEC_BEGIN = 0x01
    _TAG_CKSUM    = 0x02
    _TAG_PARAM       = 0x03
    _TAG_CODEC_END   = 0x04
    _TAG_DATA        = 0x05

    def _encode_tlv(self, tag: int, value: bytes) -> bytes:
        return struct.pack("<BI", tag, len(value)) + value

    def _decode_tlv(self, buf: bytes) -> Iterator[Tuple[int, bytes]]:
        pos = 0
        while pos < len(buf):
            tag = buf[pos]
            length = struct.unpack_from("<I", buf, pos + 1)[0]
            pos += 5
            yield tag, buf[pos:pos + length]
            pos += length
        
    def pack_frame(self, cksum: int, meta: Dict[str, bytes], payload: bytes) -> bytes:
        parts = [self._MAGIC]
        parts.append(self._encode_tlv(self._TAG_CODEC_BEGIN, b""))
        parts.append(self._encode_tlv(self._TAG_CKSUM, struct.pack("<I", cksum)))
        for k, v in meta.items():
            raw = k.encode("utf-8") + b"\0" + v
            parts.append(self._encode_tlv(self._TAG_PARAM, raw))
        parts.append(self._encode_tlv(self._TAG_CODEC_END, b""))
        parts.append(self._encode_tlv(self._TAG_DATA, payload))
        return b"".join(parts)

    def unpack_frame(self, buf: bytes) -> Tuple[int, Dict[str, bytes], bytes]:
        if not buf.startswith(self._MAGIC):
            raise ValueError("bad magic")
        pos = len(self._MAGIC)
        cksum: Optional[int] = None
        meta: Dict[str, bytes] = {}
        payload: Optional[bytes] = None
        for tag, value in self._decode_tlv(buf[pos:]):
            if tag == self._TAG_CKSUM:
                cksum = struct.unpack("<I", value)[0]
            elif tag == self._TAG_PARAM:
                k, v = value.split(b"\0", 1)
                meta[k.decode()] = v
            elif tag == self._TAG_DATA:
                payload = value
        if cksum is None or payload is None:
            raise ValueError("incomplete frame")
        return cksum, meta, payload


class CodecPipeline:
    def __init__(self, codecs: Sequence[Codec], framer: Optional[Framer] = None):
        self._codecs = list(codecs)
        self._framer = framer or Framer()

    def encode(self, data: bytes) -> bytes:
        buf = data
        for codec in reversed(self._codecs):
            meta, payload = codec.encode(buf)
            cksum = self._compute_cksum(codec, meta, payload)
            buf = self._framer.pack_frame(cksum, meta, payload)
        return buf

    def decode(self, framed: bytes) -> bytes:
        buf = framed
        for codec in self._codecs:
            cksum, meta, payload = self._framer.unpack_frame(buf)
            if cksum != self._compute_cksum(codec, meta, payload):
                raise ValueError(f"Frame checksum mismatch")
            buf = codec.decode(meta, payload)
        return buf
    
    def _compute_cksum(self, codec: Codec, meta: dict[str, bytes], payload: bytes) -> int:
        data = bytearray()
        data.extend((codec.hash() & 0xFFFFFFFF).to_bytes(4, 'little'))
        for k,v in meta.items():
            data.extend(k.encode("utf8"))
            data.extend(v)
        data.extend(payload)
        return CRC.checksum(bytes(data))