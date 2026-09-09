import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ProcessorConfig:
    input_dir: Path = Path("input")
    output_dir: Path = Path("output")
    dpi: int = 200
    quality: int = 85
    lang: str = "spa+eng"
    fmt: str = "webp"
    workers: int = os.cpu_count() or 1
    min_conf: int = 30
    psm: Optional[int] = None
    force: bool = False
    force_ocr: bool = False

    def __post_init__(self):
        self.input_dir = Path(self.input_dir)
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.workers = max(1, self.workers)
