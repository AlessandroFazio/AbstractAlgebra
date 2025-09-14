from os import PathLike
from pathlib import Path
import sys
from typing import Iterator, TextIO

class StreamIO: 
    def __init__(self) -> None:
        self._read = 0
        self._written = 0
        
    def read_bytes(self, chunk_size: int=8192) -> Iterator[int]:
        while True:
            chunk = sys.stdin.buffer.read(chunk_size)
            if not chunk:
                break
            for b in chunk:
                yield b
            self._read += len(chunk)
                
    def write_bytes(self, byte_iter: Iterator[int], chunk_size: int=8192) -> None:
        buf = []
        for b in byte_iter:
            buf.append(b)
            if len(buf) >= chunk_size:
                sys.stdout.buffer.write(bytes(buf))
                buf.clear()
                self._written += len(buf)
        if buf:
            sys.stdout.buffer.write(bytes(buf))
            self._written += len(buf)
        sys.stdout.buffer.flush()
        
    def read_count(self) -> int:
        return self._read
    
    def written_count(self) -> int:
        return self._written