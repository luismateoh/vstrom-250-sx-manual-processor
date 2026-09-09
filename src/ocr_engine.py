import shutil
from typing import Optional

import pytesseract
from PIL import Image


class OcrEngine:
    """OCR sobre una imagen de página, en una sola pasada de Tesseract.

    `image_to_data` ya devuelve el texto palabra por palabra, así que el texto
    completo se reconstruye a partir de él en vez de invocar a Tesseract una
    segunda vez con `image_to_string`.
    """

    def __init__(self, lang: str = "spa+eng", min_conf: int = 30, psm: Optional[int] = None):
        self.lang = lang
        self.min_conf = min_conf
        self.psm = psm
        self.available = shutil.which("tesseract") is not None

    def check(self) -> None:
        if not self.available:
            raise RuntimeError(
                "Tesseract no está instalado. "
                "Instálalo: https://github.com/tesseract-ocr/tesseract"
            )

    def _config(self) -> str:
        return f"--psm {self.psm}" if self.psm is not None else ""

    @staticmethod
    def _prepare(img: Image.Image) -> Image.Image:
        """Escala de grises: Tesseract binariza igual, pero con un canal en vez
        de tres gasta menos memoria y ancho de banda."""
        return img if img.mode == "L" else img.convert("L")

    def process_image(self, img: Image.Image) -> dict:
        self.check()
        data = pytesseract.image_to_data(
            self._prepare(img),
            lang=self.lang,
            config=self._config(),
            output_type=pytesseract.Output.DICT,
        )

        blocks: list[dict] = []
        lines: dict[tuple[int, int, int], list[str]] = {}
        dropped = 0

        for i in range(len(data["text"])):
            text = data["text"][i].strip()
            if not text:
                continue

            try:
                conf = float(data["conf"][i])
            except (TypeError, ValueError):
                conf = -1.0

            # Tesseract marca con -1 las filas que no son palabras; el resto de
            # baja confianza suele ser ruido del escaneo que ensucia la búsqueda.
            if conf < self.min_conf:
                dropped += 1
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
                    "conf": int(conf),
                }
            )

            key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            lines.setdefault(key, []).append(text)

        full_text = "\n".join(" ".join(words) for _, words in sorted(lines.items()))

        return {
            "text": full_text,
            "blocks": blocks,
            "wordCount": len(blocks),
            "droppedWords": dropped,
        }
