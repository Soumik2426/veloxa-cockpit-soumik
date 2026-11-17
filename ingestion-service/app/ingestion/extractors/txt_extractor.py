from pathlib import Path


class TXTExtractor:

    def extract(self, file_path: Path) -> dict:

        # Try UTF-8 first, then fall back to Windows encoding
        try:
            text = file_path.read_text(encoding="utf-8-sig")

        except UnicodeDecodeError:
            text = file_path.read_text(
                encoding="cp1252",
                errors="replace"
            )

        return {
            "text": text,
            "character_count": len(text),
            "record_status": "DATA" if text.strip() else "EMPTY"
        }
