import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SPECIAL_WORDS = {
    "vstrom": "V-Strom",
    "suzuki": "Suzuki",
    "sx": "SX",
    "en": "EN",
    "es": "ES",
    "ds250rlm3": "DS250RLM3",
}


def format_title(raw: str) -> str:
    words = re.split(r"[-_\s]+", raw.strip())
    formatted: list[str] = []
    for word in words:
        lower = word.lower()
        if lower in _SPECIAL_WORDS:
            formatted.append(_SPECIAL_WORDS[lower])
        elif word.isupper() and len(word) <= 10:
            formatted.append(word)
        elif word.isdigit():
            formatted.append(word)
        else:
            formatted.append(word.capitalize())
    return " ".join(formatted)


class ManifestBuilder:
    def __init__(self, manual_id: str, title: str, source: Path, language: str):
        self.manual_id = manual_id
        self.title = format_title(title)
        self.source = str(source)
        self.language = language
        self.pages: list[dict[str, Any]] = []

    def add_page(self, page_number: int, image: str, text: str, blocks: list[dict], word_count: int):
        self.pages.append(
            {
                "pageNumber": page_number,
                "image": image,
                "text": text,
                "blocks": blocks,
                "wordCount": word_count,
            }
        )

    def build(self) -> dict[str, Any]:
        return {
            "id": self.manual_id,
            "title": self.title,
            "source": self.source,
            "processedAt": datetime.now(timezone.utc).isoformat(),
            "pageCount": len(self.pages),
            "language": self.language,
            "pages": self.pages,
        }

    def save(self, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(self.build(), f, ensure_ascii=False, indent=2)
        return dest
