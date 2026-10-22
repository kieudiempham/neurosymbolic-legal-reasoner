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
    u = re.sub(r"\s*(/|\b(mỗi|một|hằng|hàng)\b).*$", "", u) or u  # "triệu đồng/tháng" -> "triệu đồng"
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


_DEONTIC = ("obligation", "right", "prohibition", "procedure")


def repair_norms(con) -> dict:
    """Rule-based repairs of extraction slips:
    - a deontic norm whose behaviour was written as a conclusion: the conclusion becomes the action;
    - a negated action name in a deontic norm (prohibition of khong_cuong_buc_lao_dong = double negation): the
      prefix is dropped, and an obligation not to do X becomes a prohibition of X."""
    n = {"conclusion_to_action": 0, "negated_action": 0}
    for nid, modality, cpred, cargs in con.execute(
            "SELECT norm_id, modality, conclusion_pred, conclusion_args FROM norms WHERE action_pred IS NULL "
            f"AND conclusion_pred IS NOT NULL AND modality IN ({','.join('?' * len(_DEONTIC))})", _DEONTIC).fetchall():
        con.execute("UPDATE norms SET action_pred=?, action_args=?, conclusion_pred=NULL, conclusion_args=NULL, "
                    "conclusion_negated=NULL WHERE norm_id=?", (cpred, cargs, nid))
        n["conclusion_to_action"] += 1
    for nid, modality, apred in con.execute(
            "SELECT norm_id, modality, action_pred FROM norms WHERE action_pred LIKE 'khong\\_%' ESCAPE '\\' "
            "AND modality IN ('obligation', 'prohibition')").fetchall():
        positive = apred[len("khong_"):]
        row = con.execute("SELECT arity, description_vi, domain FROM predicates WHERE name=?", (apred,)).fetchone()
        if row and not con.execute("SELECT 1 FROM predicates WHERE name=?", (positive,)).fetchone():
            con.execute("INSERT INTO predicates VALUES (?,?,?,?,?,?)",
                        (positive, row[0], "action", f"(hành vi khẳng định của {apred})", row[2], "extracted"))
            for pos, role, typ in con.execute("SELECT position, role, type FROM predicate_args WHERE pred=?",
                                              (apred,)).fetchall():
                con.execute("INSERT OR IGNORE INTO predicate_args VALUES (?,?,?,?)", (positive, pos, role, typ))
        con.execute("UPDATE norms SET action_pred=?, modality='prohibition' WHERE norm_id=?", (positive, nid))
        n["negated_action"] += 1
    return n


# a condition predicate named after a cross-reference: co_dieu_kien_theo_khoan_1_dieu_27, thuoc_dien_diem_d_e_k_khoan_1_dieu_2
_REF_NAME = re.compile(r"(?:diem_(?P<points>[a-zđ](?:_[a-zđ])*)_)?(?:khoan_(?P<clauses>\d+(?:_\d+)*))?_?"
                       r"(?:dieu_(?P<articles>\d+(?:_\d+)*))?")


def reference_predicates(con) -> int:
    """Conditions whose predicate names a provision ("đối tượng quy định tại khoản 1 Điều 2") are linked to the norms
    of that provision (table condition_refs); the compiler turns them into applies/2 of those norms, so the
    condition holds exactly when the referenced provision applies."""
    con.execute("DELETE FROM condition_refs")
    n = 0
    for cond_id, pred, nid, unit in con.execute(
            "SELECT k.cond_id, k.pred, k.norm_id, n.unit_id FROM norm_conditions k JOIN norms n ON n.norm_id=k.norm_id "
            "WHERE k.kind='atom' AND (k.pred LIKE '%khoan\\_%' ESCAPE '\\' OR k.pred LIKE '%dieu\\_%' ESCAPE '\\' "
            "OR k.pred LIKE '%diem\\_%' ESCAPE '\\')").fetchall():
        m = next((m for m in _REF_NAME.finditer(pred) if m.group("clauses") or m.group("articles")), None)
        if not m:
            continue
        doc, rest = unit.split(":", 1)
        tail = pred[m.end():]
        other = re.match(r"_?(\d+)_(20\d\d)", tail)  # khoan_1_dieu_2_158_2025: another document
        if other:
            found = con.execute("SELECT number FROM documents WHERE number LIKE ?",
                                (f"{other.group(1)}/{other.group(2)}/%",)).fetchone()
            if not found:
                continue
            doc = found[0]
        elif re.search(r"luat|nghi_dinh|thong_tu", tail):
            continue  # names another document without its number
        articles = (m.group("articles") or re.match(r"D(\d+[a-zđ]?)", rest).group(1)).split("_")
        units = []
        for a in articles:
            base = f"{doc}:D{a}"
            if not m.group("clauses"):
                units.append(base)
                continue
            for k in m.group("clauses").split("_"):
                points = m.group("points").split("_") if m.group("points") else [None]
                units += [f"{base}.K{k}" + (f".{p}" if p else "") for p in points]
        targets = {t for u in units for (t,) in con.execute(
            "SELECT norm_id FROM norms WHERE (unit_id=? OR unit_id LIKE ?) AND modality IN ('definition','consequence')",
            (u, u + ".%"))} - {nid}
        for t in sorted(targets):
            con.execute("INSERT OR IGNORE INTO condition_refs VALUES (?,?)", (cond_id, t))
            n += 1
    return n


def typed_holders(con) -> int:
    """A holder written as a type name instead of a variable (subject_var = 'doanh_nghiep'): it becomes a variable
    of that type, and the same token in the norm's arguments refers to that variable."""
    n = 0
    for nid, subj, bearer in con.execute("SELECT norm_id, subject_var, bearer_var FROM norms").fetchall():
        declared = {v for (v,) in con.execute("SELECT var FROM norm_variables WHERE norm_id=?", (nid,))}
        for col, name in (("subject_var", subj), ("bearer_var", bearer)):
            if not name or name in declared or not re.fullmatch(r"[a-z][a-z0-9_]*", name):
                continue
            var = next(v for v in ("S", "S1", "S2", "S3") if v not in declared)
            declared.add(var)
            con.execute("INSERT INTO norm_variables VALUES (?,?,?)", (nid, var, name))
            con.execute(f"UPDATE norms SET subject_var = CASE WHEN subject_var=? THEN ? ELSE subject_var END, "
                        f"bearer_var = CASE WHEN bearer_var=? THEN ? ELSE bearer_var END WHERE norm_id=?",
                        (name, var, name, var, nid))
            swap = lambda s: ",".join(var if x.strip() == name else x for x in s.split(",")) if s else s  # noqa: E731
            a, c = con.execute("SELECT action_args, conclusion_args FROM norms WHERE norm_id=?", (nid,)).fetchone()
            con.execute("UPDATE norms SET action_args=?, conclusion_args=? WHERE norm_id=?", (swap(a), swap(c), nid))
            for cid, args in con.execute("SELECT cond_id, args FROM norm_conditions WHERE norm_id=?", (nid,)).fetchall():
                con.execute("UPDATE norm_conditions SET args=? WHERE cond_id=?", (swap(args), cid))
            n += 1
    return n
