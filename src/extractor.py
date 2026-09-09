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

    def render(self, page_number: int) -> Image.Image:
        """Renderiza una página (1-based) a PIL sin pasar por un PNG intermedio."""
        zoom = self.dpi / 72.0
        pix = self.doc.load_page(page_number - 1).get_pixmap(
            matrix=fitz.Matrix(zoom, zoom), alpha=False
        )
        return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

    def text_layer(self, page_number: int) -> dict | None:
        """Texto de la capa embebida del PDF, si la página trae una.

        Es exacto y ~1000x más rápido que el OCR, así que se prefiere siempre
        que exista. Devuelve None cuando la página no tiene texto (escaneo puro),
        para que el llamador recurra al OCR.
        """
        words = self.doc.load_page(page_number - 1).get_text("words")
        if not words:
            return None

        scale = self.dpi / 72.0  # las coordenadas del PDF están en puntos
        blocks: list[dict] = []
        lines: dict[tuple[int, int], list[tuple[int, str]]] = {}

        for x0, y0, x1, y1, word, block_no, line_no, word_no in words:
            text = word.strip()
            if not text:
                continue
            blocks.append(
                {
                    "text": text,
                    "bbox": {
                        "x": int(x0 * scale),
                        "y": int(y0 * scale),
                        "width": int((x1 - x0) * scale),
                        "height": int((y1 - y0) * scale),
                    },
                    "conf": 100,  # texto exacto, no una conjetura del OCR
                }
            )
            lines.setdefault((block_no, line_no), []).append((word_no, text))

        full_text = "\n".join(
            " ".join(w for _, w in sorted(ws)) for _, ws in sorted(lines.items())
        )
        return {
            "text": full_text,
            "blocks": blocks,
            "wordCount": len(blocks),
            "droppedWords": 0,
        }

    def __iter__(self) -> Iterator[tuple[int, Image.Image]]:
        for page_number in range(1, len(self) + 1):
            yield page_number, self.render(page_number)

    def save_page(self, img: Image.Image, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if self.fmt == "webp":
            img.save(dest, "WEBP", quality=self.quality, method=6)
        elif self.fmt in ("jpg", "jpeg"):
            img.convert("RGB").save(dest, "JPEG", quality=self.quality, optimize=True)
        else:
            img.save(dest, self.fmt.upper())
        return dest

    def close(self):
        self.doc.close()
