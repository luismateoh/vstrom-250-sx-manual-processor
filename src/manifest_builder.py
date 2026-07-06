import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ManifestBuilder:
    def __init__(self, manual_id: str, title: str, source: Path, language: str):
        self.manual_id = manual_id
        self.title = title
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
