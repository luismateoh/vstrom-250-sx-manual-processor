import shutil
from pathlib import Path
from typing import Optional

import pytesseract
from PIL import Image


class OcrEngine:
    def __init__(self, lang: str = "spa+eng"):
        self.lang = lang
        self.available = shutil.which("tesseract") is not None

    def check(self) -> None:
        if not self.available:
            raise RuntimeError(
                "Tesseract no está instalado. "
                "Instálalo: https://github.com/tesseract-ocr/tesseract"
            )

    def extract_text(self, img: Image.Image) -> str:
        self.check()
        return pytesseract.image_to_string(img, lang=self.lang)

    def extract_blocks(self, img: Image.Image) -> list[dict]:
        """Extrae bloques de texto con coordenadas para resaltado en la PWA."""
        self.check()
        data = pytesseract.image_to_data(img, lang=self.lang, output_type=pytesseract.Output.DICT)
        blocks: list[dict] = []
        n_boxes = len(data["text"])

        for i in range(n_boxes):
            text = data["text"][i].strip()
            if not text:
                continue
            blocks.append(
                {
                    "text": text,
                    "bbox": {
                        "x": int(data["left"][i]),
                        "y": int(data["top"][i]),
                        "width": int(data["width"][i]),
                        "height": int(data["height"][i]),
                    },
                    "conf": int(data["conf"][i]),
                }
            )
        return blocks

    def process_image(self, img: Image.Image) -> dict:
        full_text = self.extract_text(img)
        blocks = self.extract_blocks(img)
        return {
            "text": full_text,
            "blocks": blocks,
            "wordCount": len(full_text.split()),
        }
