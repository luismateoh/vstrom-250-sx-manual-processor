import io
from pathlib import Path
from typing import Iterator

import fitz  # PyMuPDF
from PIL import Image


class PdfExtractor:
    def __init__(self, pdf_path: Path, dpi: int = 200, quality: int = 85, fmt: str = "webp"):
        self.pdf_path = pdf_path
        self.dpi = dpi
        self.quality = quality
        self.fmt = fmt.lower()
        self.doc = fitz.open(str(pdf_path))

    def __len__(self) -> int:
        return len(self.doc)

    def __iter__(self) -> Iterator[tuple[int, Image.Image]]:
        zoom = self.dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        for page_number in range(len(self.doc)):
            page = self.doc.load_page(page_number)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            yield page_number + 1, img

    def save_page(self, img: Image.Image, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if self.fmt == "webp":
            img.save(dest, "WEBP", quality=self.quality, method=6)
        elif self.fmt in ("jpg", "jpeg"):
            rgb_img = img.convert("RGB")
            rgb_img.save(dest, "JPEG", quality=self.quality, optimize=True)
        else:
            img.save(dest, self.fmt.upper())
        return dest

    def close(self):
        self.doc.close()
