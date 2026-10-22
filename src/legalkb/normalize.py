"""Normalisation (rule-based): names, units, cross-references between norms, document relations."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict

_UNITS = {  # surface unit -> (canonical unit, factor to the canonical unit)
    "ngày": ("ngay", 1), "ngày làm việc": ("ngay_lam_viec", 1), "tháng": ("thang", 1), "năm": ("thang", 12),
    "giờ": ("gio", 1), "tuần": ("ngay", 7), "%": ("phan_tram", 1), "phần trăm": ("phan_tram", 1),
    "đồng": ("dong", 1), "vnd": ("dong", 1), "nghìn đồng": ("dong", 1e3), "triệu đồng": ("dong", 1e6),
    "triệu": ("dong", 1e6), "tỷ đồng": ("dong", 1e9), "tỷ": ("dong", 1e9), "người": ("nguoi", 1),
    "lần": ("lan", 1), "tuổi": ("tuoi", 1),
}


def canon_name(name: str | None) -> str | None:
    """Vietnamese or mixed text -> ascii snake_case identifier (đ -> d, accents removed)."""
    if name is None:
        return None
    s = unicodedata.normalize("NFD", name.replace("đ", "d").replace("Đ", "D"))
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn").lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or None


def canon_unit(unit: str | None) -> tuple[str | None, float]:
    if not unit:
        return None, 1.0
    u = unit.strip().lower()
    if u in _UNITS:
        return _UNITS[u]
    return canon_name(u), 1.0


_REF = re.compile(r"(?:[dđ]iem\s+(?P<point>[a-zđ])\s*,?\s*)?(?:khoan\s+(?P<clause>\d+)\s*,?\s*)?(?:[dđ]ieu\s+(?P<article>\d+[a-zđ]?|nay))?"
                  r"(?:\s+(?P<doc>luat nay|nghi dinh nay|thong tu nay|cua\s+[^,;]+))?", re.I)


def _plain(text: str) -> str:
    """Lower case without accents (đ kept), so references match whether or not they carry diacritics."""
    s = unicodedata.normalize("NFD", text.replace("Đ", "đ").lower())
    return unicodedata.normalize("NFC", "".join(ch for ch in s if unicodedata.category(ch) != "Mn"))


def resolve_ref(ref: str, unit_id: str) -> str | None:
    """'khoản 7 Điều này' in unit 41/2024/QH15:D2.K1.a -> 41/2024/QH15:D2.K7 (same document only)."""
    if re.fullmatch(r"[^:\s]+:D\d+[a-zđ]?(\.K\d+(\.[a-zđ])?)?", ref.strip()):
        return ref.strip()  # already a unit id
    m = _REF.search(_plain(ref))
    if not m or not any(m.group(g) for g in ("point", "clause", "article")):
        return None
    if m.group("doc") and m.group("doc").startswith("cua"):
        return None  # reference to another document: kept as text
    doc, rest = unit_id.split(":", 1)
    cur_article = re.match(r"D(\d+[a-zđ]?)", rest).group(1)
    art = m.group("article")
    art = cur_article if (art is None or art == "nay") else art
    target = f"{doc}:D{art}"
    if m.group("clause"):
        target += f".K{m.group('clause')}"
        if m.group("point"):
            target += f".{m.group('point')}"
    return target


def link_references(con) -> int:
    """Resolve textual references to units and, where the target unit has norms, add one row per target norm."""
    n = 0
    rows = con.execute("SELECT rowid, norm_id, ref_kind, ref_text FROM norm_references "
                       "WHERE target_unit_id IS NULL AND target_norm_id IS NULL").fetchall()
    unit_of = dict(con.execute("SELECT norm_id, unit_id FROM norms"))
    targets = {rowid: resolve_ref(text, unit_of[nid]) for rowid, nid, _, text in rows}
    exceptions_to = defaultdict(set)  # target unit -> norms declared as its exceptions (siblings of each other)
    for rowid, nid, kind, _ in rows:
        if kind == "exception_of" and targets[rowid]:
            exceptions_to[targets[rowid]].add(nid)
    for rowid, nid, kind, text in rows:
        target = targets[rowid]
        if not target:
            continue
        # norms of the target unit itself; only if it has none, the norms of its sub-units, except the other
        # exceptions of the same unit (an exception of a lead-in is not an exception of its sibling exceptions)
        excluded = {nid}
        if kind in ("exception_of", "has_exception"):
            excluded |= {e for u, es in exceptions_to.items() if u == target or u.startswith(target + ".") for e in es}
        norms = [t for (t,) in con.execute("SELECT norm_id FROM norms WHERE unit_id = ?", (target,))
                 if t not in excluded] or \
            [t for (t,) in con.execute("SELECT norm_id FROM norms WHERE unit_id LIKE ?", (target + ".%",))
             if t not in excluded]
        if not norms:  # target unit known but not (yet) encoded
            con.execute("UPDATE norm_references SET target_unit_id=? WHERE rowid=?", (target, rowid))
            continue
        con.execute("DELETE FROM norm_references WHERE rowid=?", (rowid,))
        for t in norms:
            con.execute("INSERT INTO norm_references (norm_id, ref_kind, ref_text, target_unit_id, target_norm_id) "
                        "VALUES (?,?,?,?,?)", (nid, kind, text, target, t))
            n += 1
    return n


_GUIDES = re.compile(r"quy định chi tiết[^.]{0,200}?(?:Luật|Bộ luật)[^.;]{0,80}?số\s+(\d+/\d{4}/QH\d+)", re.I)


def document_relations(con, doc_number: str, text: str, replaces: list[str]) -> None:
    for r in replaces:
        con.execute("INSERT OR IGNORE INTO doc_relations VALUES (?,?,?)", (doc_number, "replaces", r))
    for law in set(_GUIDES.findall(text[:6000])):
        con.execute("INSERT OR IGNORE INTO doc_relations VALUES (?,?,?)", (doc_number, "guides", law))
