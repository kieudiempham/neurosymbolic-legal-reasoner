"""Layer 1-2: document metadata and the legal structure (Chương / Điều / Khoản / Điểm). Rule-based, no LLM.

Vietnamese legal documents follow the Law on Promulgation of Legal Documents, so the structure and most metadata
(number, type, issuing body, issue date, effective date) can be read with patterns; this is more reliable than an
LLM for these fields.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from diagnosis.kbx.corpus import CORPUS, DOMAINS, document_text

# hierarchy of legal force (lower number = higher force)
DOC_TYPES = [  # (pattern on the document number, type, issuing body, rank)
    (r"/QH\d+$", "Luật", "Quốc hội", 2),
    (r"VBHN-VPQH$", "Văn bản hợp nhất (Luật)", "Văn phòng Quốc hội", 2),
    (r"/NĐ-CP$", "Nghị định", "Chính phủ", 3),
    (r"/QĐ-TTg$", "Quyết định", "Thủ tướng Chính phủ", 4),
    (r"/TT-[A-ZĐ]+$", "Thông tư", "Bộ", 5),
]
_NUMBER = re.compile(r"(?:Luật|Bộ luật|Nghị định|Thông tư|Văn bản hợp nhất|Quyết định)?\s*số[:\s]+([0-9]+/[0-9]{4}/[A-ZĐ0-9\-]+|[0-9]+/VBHN-[A-ZĐ]+)", re.I)
_ISSUED = re.compile(r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})")
_EFFECTIVE = re.compile(r"có hiệu lực(?: thi hành)?(?: kể)? từ ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})")
_REPLACES = re.compile(r"(?:Luật|Nghị định|Thông tư)[^.;\n]{0,60}?số\s+([0-9]+/[0-9]{4}/[A-ZĐ0-9\-]+)[^.;\n]{0,40}?hết hiệu lực")
_CHAP = re.compile(r"(?m)^\s*Chương\s+([IVXLC]+)\b")
_ART = re.compile(r"(?m)^\s*Điều\s+(\d+[a-zđ]?)\s*[\.:]\s*(.*)$")
_CLAUSE = re.compile(r"(?m)^\s*(\d+)\.\s+")
_POINT = re.compile(r"(?m)^\s*([a-zđ])\)\s+")


@dataclass
class Unit:
    unit_id: str          # e.g. 41/2024/QH15:D2.K1.a
    doc_number: str
    chapter: str
    article: str
    clause: str | None
    point: str | None
    title: str
    text: str


@dataclass
class Document:
    doc_id: str           # file stem
    number: str
    title: str
    doc_type: str
    issuer: str
    rank: int
    domain: str
    issued: str | None
    effective_from: str | None
    replaces: list[str] = field(default_factory=list)
    source_file: str = ""


def _date(m) -> str:
    return f"{int(m.group(3)):04d}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"


def read_document(stem: Path, domain: str) -> tuple[Document, str]:
    text, src = document_text(stem)
    head = text[:1500]
    m = _NUMBER.search(head)
    number = m.group(1).replace("ND-CP", "NĐ-CP") if m else stem.name
    dtype, issuer, rank = "Khác", "", 9
    for pat, t, iss, r in DOC_TYPES:
        if re.search(pat, number):
            dtype, issuer, rank = t, iss, r
            break
    title_m = re.search(r"\n\s*(LUẬT|BỘ LUẬT|NGHỊ ĐỊNH|THÔNG TƯ|VĂN BẢN HỢP NHẤT|QUYẾT ĐỊNH)\s*\n\s*([^\n]+)", head)
    title = f"{title_m.group(1).title()} {title_m.group(2).strip().title()}" if title_m else stem.name
    issued = _ISSUED.search(head)
    eff = list(_EFFECTIVE.finditer(text))
    return Document(stem.name, number, title, dtype, issuer, rank, domain, _date(issued) if issued else None,
                    _date(eff[-1]) if eff else None, sorted(set(_REPLACES.findall(text))), src), text


def segment_units(doc: Document, text: str) -> list[Unit]:
    """Split into Điều, then Khoản ("1. ..."), then Điểm ("a) ..."). An Điều without clauses is one unit."""
    text = re.sub(r"[ \t ]+", " ", text)
    chapters = [(m.start(), m.group(1)) for m in _CHAP.finditer(text)]
    arts = list(_ART.finditer(text))
    units: list[Unit] = []
    seen: set[str] = set()
    for k, m in enumerate(arts):
        num = m.group(1)
        if num in seen:  # amending documents quote articles of other laws: keep the first occurrence
            continue
        seen.add(num)
        body = text[m.end(): arts[k + 1].start() if k + 1 < len(arts) else len(text)]
        chap = next((c for pos, c in reversed(chapters) if pos <= m.start()), "")
        title = m.group(2).strip()
        base = f"{doc.number}:D{num}"
        clauses = list(_CLAUSE.finditer(body))
        if not clauses:
            units.append(Unit(base, doc.number, chap, num, None, None, title, body.strip()))
            continue
        lead = body[: clauses[0].start()].strip()
        if lead:
            units.append(Unit(base, doc.number, chap, num, None, None, title, lead))
        for j, c in enumerate(clauses):
            ctext = body[c.end(): clauses[j + 1].start() if j + 1 < len(clauses) else len(body)]
            points = list(_POINT.finditer(ctext))
            cid = f"{base}.K{c.group(1)}"
            if not points:
                units.append(Unit(cid, doc.number, chap, num, c.group(1), None, title, ctext.strip()))
                continue
            clead = ctext[: points[0].start()].strip()
            units.append(Unit(cid, doc.number, chap, num, c.group(1), None, title, clead))
            for i, pt in enumerate(points):
                ptext = ctext[pt.end(): points[i + 1].start() if i + 1 < len(points) else len(ctext)]
                units.append(Unit(f"{cid}.{pt.group(1)}", doc.number, chap, num, c.group(1), pt.group(1), title,
                                  ptext.strip()))
    return units


def load_documents(only: list[str] | None = None) -> list[tuple[Document, list[Unit]]]:
    out = []
    for dom in DOMAINS:
        for stem in sorted({p.with_suffix("") for p in (CORPUS / dom).iterdir() if p.suffix in (".pdf", ".doc")}):
            if only and stem.name not in only:
                continue
            doc, text = read_document(stem, dom)
            out.append((doc, segment_units(doc, text)))
    return out


def as_dict(x) -> dict:
    return asdict(x)
