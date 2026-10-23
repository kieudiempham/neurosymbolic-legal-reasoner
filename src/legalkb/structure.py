"""Layer 1-2: document metadata and the legal structure (Chương / Điều / Khoản / Điểm). Rule-based, no LLM.

Vietnamese legal documents follow the Law on Promulgation of Legal Documents, so the structure and most metadata
(number, type, issuing body, issue date, effective date) can be read with patterns; this is more reliable than an
LLM for these fields.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .db import legal_force

from diagnosis.kbx.corpus import CORPUS, DOMAINS, document_text

_NUMBER = re.compile(r"(?:Luật|Bộ luật|Nghị định|Thông tư|Văn bản hợp nhất|Quyết định)?\s*số[:\s]+([0-9]+/[0-9]{4}/[A-ZĐ0-9\-]+|[0-9]+/VBHN-[A-ZĐ]+)", re.I)
_ISSUED = re.compile(r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})")
_EFFECTIVE = re.compile(r"có hiệu lực(?: thi hành)?(?: kể)? từ ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})")
_REPLACES = re.compile(r"(?:Luật|Nghị định|Thông tư)[^.;\n]{0,60}?số\s+([0-9]+/[0-9]{4}/[A-ZĐ0-9\-]+)[^.;\n]{0,40}?hết hiệu lực")
_CHAP = re.compile(r"(?m)^\s*Chương\s+([IVXLC]+)\b")
_ART = re.compile(r"(?m)^\s*Điều\s+(\d+[a-zđ]?)\s*(?:[\.:]\s*(.*))?$")  # title may be on the next line
# an article quoted inside an amending document: “Điều 11. ... ” (the new wording of an article of another document)
_QUOTED_ART = re.compile(r"(?m)^\s*[“\"]Điều\s+(\d+[a-zđ]?)\s*[\.:]\s*(.*)$")
_QUOTE_END = re.compile(r"[”\"]\s*(?:\.|;)?\s*$", re.M)
_AMENDED = re.compile(r"(?:sửa đổi|bổ sung)[^\n]{0,300}?số\s+([0-9]+/[0-9]{4}/[A-ZĐ0-9\-]+)", re.I)
_TARGET = re.compile(r"số\s+([0-9]+/[0-9]{4}/[A-ZĐ0-9\-]+)")
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
    target_doc: str | None = None   # amended document, for an article quoted in an amending document
    valid_from: str | None = None   # effective date of that new wording


@dataclass
class Document:
    doc_id: str           # file stem
    number: str
    title: str
    doc_type: str
    issuer: str
    rank: int | None
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
    dtype, issuer, rank = "Khác", "", None  # a type not in the legal_force table has no rank
    for pat, t, iss, r in legal_force():  # document types and their rank of legal force: table legal_force
        if re.search(pat, number):
            dtype, issuer, rank = t, iss, r
            break
    title_m = re.search(r"\n\s*(LUẬT|BỘ LUẬT|NGHỊ ĐỊNH|THÔNG TƯ|VĂN BẢN HỢP NHẤT|QUYẾT ĐỊNH)\s*\n\s*([^\n]+)", head)
    title = f"{title_m.group(1).title()} {title_m.group(2).strip().title()}" if title_m else stem.name
    issued = _ISSUED.search(head)
    eff = list(_EFFECTIVE.finditer(text))
    return Document(stem.name, number, title, dtype, issuer, rank, domain, _date(issued) if issued else None,
                    _date(eff[-1]) if eff else None, sorted(set(_REPLACES.findall(text))), src), text


def _split(base: str, doc_number: str, chap: str, num: str, title: str, body: str, **extra) -> list[Unit]:
    """One Điều into units: lead-in, Khoản ("1. ..."), Điểm ("a) ...")."""
    units: list[Unit] = []
    clauses = list(_CLAUSE.finditer(body))
    if not clauses:
        return [Unit(base, doc_number, chap, num, None, None, title, body.strip(), **extra)]
    lead = body[: clauses[0].start()].strip()
    if lead:
        units.append(Unit(base, doc_number, chap, num, None, None, title, lead, **extra))
    for j, c in enumerate(clauses):
        ctext = body[c.end(): clauses[j + 1].start() if j + 1 < len(clauses) else len(body)]
        points = list(_POINT.finditer(ctext))
        cid = f"{base}.K{c.group(1)}"
        if not points:
            units.append(Unit(cid, doc_number, chap, num, c.group(1), None, title, ctext.strip(), **extra))
            continue
        units.append(Unit(cid, doc_number, chap, num, c.group(1), None, title, ctext[: points[0].start()].strip(),
                          **extra))
        for i, pt in enumerate(points):
            ptext = ctext[pt.end(): points[i + 1].start() if i + 1 < len(points) else len(ctext)]
            units.append(Unit(f"{cid}.{pt.group(1)}", doc_number, chap, num, c.group(1), pt.group(1), title,
                              ptext.strip(), **extra))
    return units


def _amendments(doc: Document, body: str, head: str, default_target: list[str]) -> tuple[list[Unit], str]:
    """Articles quoted in an amending article become new versions of the amended document's articles
    (unit id <target>:D<n>@<amending document>). Returns those units and the body with the quotes replaced by a
    pointer, so the amending article itself is not extracted twice."""
    units, out, pos = [], [], 0
    for m in _QUOTED_ART.finditer(body):
        if m.start() < pos:
            continue
        title = m.group(2).strip()
        if title.rstrip(";.,").endswith(("”", '"')):  # only the title is replaced; later instructions amend clauses
            end_m, end, title = None, m.end(), title.rstrip(";.,").rstrip('”"')
        else:
            end_m = _QUOTE_END.search(body, m.end())
            end = end_m.start() if end_m else len(body)
        targets = _TARGET.findall(head + body[max(0, m.start() - 400): m.start()]) or default_target
        if not targets:
            continue
        target = targets[-1].replace("ND-CP", "NĐ-CP")
        num = m.group(1)
        units += _split(f"{target}:D{num}@{doc.number}", doc.number, "", f"{num}@{target}", title,
                        body[m.end(): end] or title, target_doc=target, valid_from=doc.effective_from)
        out.append(body[pos: m.start()] + f"[Điều {num} của văn bản số {target} được thay bằng nội dung mới]")
        pos = end_m.end() if end_m else end
    return units, "".join(out) + body[pos:]


def segment_units(doc: Document, text: str) -> list[Unit]:
    """Split into Điều, then Khoản ("1. ..."), then Điểm ("a) ..."). An Điều without clauses is one unit.
    In amending documents, quoted articles are split off as new versions of the amended articles."""
    text = re.sub(r"[ \t\u00a0]+", " ", text)
    chapters = [(m.start(), m.group(1)) for m in _CHAP.finditer(text)]
    arts = list(_ART.finditer(text))
    # the document an amending law amends, named in its title / first article ("sửa đổi, bổ sung ... Luật ... số X")
    # searched from the first Điều on: the preamble ("Căn cứ Hiến pháp ... sửa đổi ... Nghị quyết số ...") names others
    first = arts[0].start() if arts else 0
    default_target = [t for t in _AMENDED.findall(text[first: first + 3000]) if t != doc.number][:1]
    units: list[Unit] = []
    seen: set[str] = set()
    for k, m in enumerate(arts):
        num = m.group(1)
        if num in seen:
            continue
        seen.add(num)
        body = text[m.end(): arts[k + 1].start() if k + 1 < len(arts) else len(text)]
        title = (m.group(2) or "").strip()
        if not title:  # "Điều 1" with the title on the next line
            first, _, body = body.lstrip("\n").partition("\n")
            title = first.strip()
        chap = next((c for pos, c in reversed(chapters) if pos <= m.start()), "")
        amended, body = _amendments(doc, body, title + " " + body[:400], default_target)
        units += amended
        units += _split(f"{doc.number}:D{num}", doc.number, chap, num, title, body)
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
