import json
from os import PathLike
from pathlib import Path
from typing import IO, Any, List, Literal

import yaml

SerFormat = Literal["json", "yaml"]

class SerUtils:
    _FORMATS = {"json", "yaml"}
    
    _FMT_TO_UNMARSHALLER = {
        "json": lambda r: json.load(r),
        "yaml": lambda r: yaml.safe_load(r)
    }
    
    _FMT_TO_EXTS = {
        "json": {".json"},
        "yaml": {".yaml", ".yml"}
    }

    @classmethod
    def unmarshall(cls, read_stream: IO, formats: List[SerFormat]) -> Any:
        for fmt in formats:
            try:
                return cls._FMT_TO_UNMARSHALLER[fmt](read_stream)
            except Exception: 
                pass
        raise RuntimeError(f"could not unmarshall readable stream into any of following formats: {formats}")

    @classmethod
    def from_file(cls, path: Path, formats: List[SerFormat]) -> Any:
        i = 0
        for fmt in formats:
            exts = cls._FMT_TO_EXTS[fmt]
            if path.suffix in exts:    
                break
            i += 1
        
        if i != len(formats):
            formats = [formats[i]] + formats[:i] + formats[i+1:]
            
        with open(path) as f:
            return cls.unmarshall(f, formats)