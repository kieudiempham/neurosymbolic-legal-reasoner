"""Read the 18 legal documents (PDF or legacy .doc) and segment them into articles."""

from __future__ import annotations

import re
import struct
import unicodedata
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CORPUS = ROOT / "data" / "raw" / "legal_corpus"
DOMAINS = ("labor", "enterprise", "tax")


def read_doc(path: Path) -> str:
    """Plain text of a Word 97-2003 .doc via its piece table (no Word/LibreOffice needed)."""
    import olefile

    ole = olefile.OleFileIO(str(path))
    wd = ole.openstream("WordDocument").read()
    flags = struct.unpack_from("<H", wd, 0x000A)[0]
    table = ole.openstream("1Table" if flags & 0x0200 else "0Table").read()
    fc_clx, lcb_clx = struct.unpack_from("<II", wd, 0x01A2)
    clx = table[fc_clx : fc_clx + lcb_clx]
    i = 0
    while clx[i] == 0x01:  # skip Prc (property modifiers)
        cb = struct.unpack_from("<H", clx, i + 1)[0]
        i += 3 + cb
    if clx[i] != 0x02:
        raise ValueError(f"{path.name}: unexpected CLX structure")
    lcb = struct.unpack_from("<I", clx, i + 1)[0]
    plc = clx[i + 5 : i + 5 + lcb]
    n = (lcb - 4) // 12
    cps = struct.unpack_from(f"<{n + 1}I", plc, 0)
    out = []
    for k in range(n):
        pcd = plc[4 * (n + 1) + 8 * k : 4 * (n + 1) + 8 * (k + 1)]
        fc = struct.unpack_from("<I", pcd, 2)[0]
        nchar = cps[k + 1] - cps[k]
        if fc & 0x40000000:
            start = (fc & ~0x40000000) // 2
            out.append(wd[start : start + nchar].decode("cp1252", errors="replace"))
        else:
            out.append(wd[fc : fc + 2 * nchar].decode("utf-16-le", errors="replace"))
    text = "".join(out)
    text = re.sub(r"[\x07\x0b\x0c\r]", "\n", text)
    text = re.sub(r"[\x00-\x06\x08\x0e-\x1f]", "", text)
    return text


def read_pdf(path: Path) -> str:
    import pymupdf

    return "\n".join(p.get_text() for p in pymupdf.open(str(path)))


def document_text(path_noext: Path) -> tuple[str, str]:
    pdf, doc = path_noext.with_suffix(".pdf"), path_noext.with_suffix(".doc")
    if pdf.exists():
        raw, src = read_pdf(pdf), pdf.name
    else:
        raw, src = read_doc(doc), doc.name
    return unicodedata.normalize("NFC", raw), src


@dataclass
class Article:
    doc_id: str
    domain: str
    doc_file: str
    number: str
    title: str
    chapter: str
    text: str

    @property
    def ref(self) -> str:
        return f"{self.doc_id}, Điều {self.number}"


_ART = re.compile(r"(?m)^\s*Điều\s+(\d+[a-zđ]?)\s*[\.:]\s*(.*)$")
_CHAP = re.compile(r"(?m)^\s*Chương\s+([IVXLC]+)\b.*$")


def doc_label(stem: str) -> str:
    """Readable citation label from the file name, e.g. 'Luật BHXH 41/2024/QH15'."""
    s = re.sub(r"^\d+_\s*", "", stem)
    m = re.search(r"(\d+)_(\d{4})_(QH\d+|ND-CP|nd_cp|TT-BTC|VBHN|vbhn_vpqh)", s, flags=re.I)
    if "vbhn_67" in s:
        return "Luật Doanh nghiệp (VBHN 67/VBHN-VPQH)"
    if m:
        kind = m.group(3).upper().replace("ND_CP", "NĐ-CP").replace("ND-CP", "NĐ-CP")
        return f"{s.split('_')[0].replace('luat', 'Luật').replace('nghi', 'Nghị')} {m.group(1)}/{m.group(2)}/{kind}"
    return s


def segment(text: str, doc_id: str, domain: str, doc_file: str) -> list[Article]:
    text = re.sub(r"[ \t ]+", " ", text)
    marks = list(_ART.finditer(text))
    chapters = [(m.start(), m.group(1)) for m in _CHAP.finditer(text)]
    arts: list[Article] = []
    seen: set[str] = set()
    for k, m in enumerate(marks):
        end = marks[k + 1].start() if k + 1 < len(marks) else len(text)
        body = text[m.start() : end].strip()
        num = m.group(1)
        # amendment documents quote articles of other laws; keep the first occurrence of each number
        key = num if num not in seen else f"{num}#{k}"
        seen.add(num)
        chap = ""
        for pos, c in chapters:
            if pos <= m.start():
                chap = c
        body = re.sub(r"\n{2,}", "\n", body)
        arts.append(Article(doc_id, domain, doc_file, key, m.group(2).strip()[:200], chap, body[:12000]))
    return arts


def load_corpus() -> list[Article]:
    out: list[Article] = []
    for dom in DOMAINS:
        stems = sorted({p.with_suffix("") for p in (CORPUS / dom).iterdir() if p.suffix in (".pdf", ".doc")})
        for stem in stems:
            text, src = document_text(stem)
            out += segment(text, stem.name, dom, src)
    return out


if __name__ == "__main__":
    import collections
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    arts = load_corpus()
    by = collections.Counter((a.domain, a.doc_id) for a in arts)
    for (d, doc), n in sorted(by.items()):
        chars = sum(len(a.text) for a in arts if a.doc_id == doc)
        print(f"{d:10s} {doc[:50]:50s} articles={n:4d} chars={chars}")
    print("TOTAL", len(arts), "articles", sum(len(a.text) for a in arts), "chars")
