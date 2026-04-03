"""Convert `.doc`/`.docx` legal documents to plain text for NLP pipelines.

Primary strategy on Windows: Word COM automation (no OCR, no web).
Fallback: read same-path `.txt` if present.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from utils.logger import get_logger
from utils.text import normalize_whitespace
from utils.ids import stable_hash


class DocToTextConverter:
    """Convert Word documents to raw and cleaned plain text."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = config or {}
        self._log = get_logger(self.__class__.__name__)

    def convert(self, doc_path: Path) -> tuple[str, str]:
        """Return (raw_text, cleaned_text)."""
        if not doc_path.exists():
            raise FileNotFoundError(f"Missing input document: {doc_path}")

        suffix = doc_path.suffix.lower()
        raw_text: str

        if suffix in {".doc", ".docx"}:
            txt_path = doc_path.with_suffix(".txt")
            try:
                raw_text = self._load_via_word_com(doc_path)

                # If Word COM succeeds but yields extremely short text (common
                # when `.doc` is not a real Word binary), prefer the sibling
                # `.txt` artifact if available.
                min_com_chars = int(self._config.get("min_com_text_chars", 200))
                if txt_path.exists() and len(raw_text.strip()) < min_com_chars:
                    raw_text = txt_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                # Research-friendly fallback: try a sibling .txt file.
                if txt_path.exists():
                    self._log.warning(
                        "Word COM load failed for %s; falling back to %s (%s)",
                        doc_path,
                        txt_path,
                        e,
                    )
                    raw_text = txt_path.read_text(encoding="utf-8", errors="ignore")
                else:
                    raise
        else:
            raise ValueError(f"Unsupported document suffix: {suffix}")

        cleaned_text = self._clean_text(raw_text)
        return raw_text, cleaned_text

    def _load_via_word_com(self, doc_path: Path) -> str:
        """Load text using Word automation (Windows)."""
        try:
            import win32com.client  # pywin32
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "win32com is not available; cannot read .doc with Word COM."
            ) from e

        word = None
        doc = None
        tmp_doc_path: Path | None = None
        try:
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            word.DisplayAlerts = 0
            # Some Word installations fail to open files with non-ASCII names.
            # Workaround: copy to a temp directory with an ASCII-safe name.
            import re
            import shutil
            import tempfile

            ascii_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", doc_path.stem).strip("_")
            if not ascii_stem:
                ascii_stem = "doc"
            tmp_dir = Path(tempfile.mkdtemp(prefix="legalqa_doc_"))
            tmp_doc_path = tmp_dir / f"{ascii_stem}_{stable_hash(str(doc_path), n=8)}{doc_path.suffix}"
            shutil.copy2(doc_path, tmp_doc_path)

            doc = word.Documents.Open(str(tmp_doc_path), ReadOnly=True)
            # Word.Range.Text keeps formatting as plain text with line breaks.
            text = doc.Range().Text
            # Word often returns a trailing \x07 for doc end.
            return text.replace("\x07", "").strip()
        finally:
            try:
                if doc is not None:
                    doc.Close(False)
            finally:
                if word is not None:
                    word.Quit()
                if tmp_doc_path is not None and tmp_doc_path.exists():
                    try:
                        tmp_doc_path.unlink()
                    except Exception:
                        pass

    def _clean_text(self, text: str) -> str:
        """Normalize whitespace but keep paragraph structure via line breaks."""
        # Normalize newline first.
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Collapse repeated whitespace per line, but keep line breaks.
        lines = []
        for line in text.split("\n"):
            line = line.replace("\xa0", " ")
            line = normalize_whitespace(line)
            if line == "":
                lines.append("")
            else:
                lines.append(line)
        return "\n".join(lines).strip()

