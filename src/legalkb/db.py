"""Relational store of the legal KB (SQLite file; standard SQL, portable to PostgreSQL).

Tables
  documents         one row per legal document: number, type, issuer, hierarchy rank, dates, domain
  legal_force       document types and their rank of legal force (1 = highest), with the pattern of the document
                    number that identifies the type; documents.rank is read from here when a document is loaded
  priority_principles  how a conflict between two norms is resolved, in the order they are tried (ord), with what
                    each compares and its legal basis
  norm_conflicts    pairs of norms with opposite heads (computed at compile time): the winner and the principle that
                    decided, or no winner (an unresolved conflict)
  doc_relations     document -> document: replaces / amends / guides / consolidates
  units             Chương / Điều / Khoản / Điểm with full text and parent unit; an article quoted in an amending
                    document is a new version of the amended article (target_doc, valid_from; the old one gets valid_to)
  entity_types      ontology of legal subjects / objects, with is-a parent
  predicates        relations, properties, actions and legal statuses (name, arity, kind)
  predicate_args    typed, named arguments of each predicate
  attributes        numeric / date / enum attributes of an entity type, with unit
  norms             one normative rule: modality, subject / bearer / beneficiary variables, action or conclusion,
                    validity, source unit, quote
  norm_variables    typed variables of a norm
  norm_conditions   conditions: atoms (relation over variables), comparisons (attribute op value unit),
                    alternatives (alt_group / alt_option: options of a group are OR-ed, conditions of an option AND-ed)
  norm_formulas     computed attributes (e.g. contribution = 8% x wage)
  norm_deadlines    time limits of the action (N units from an event)
  norm_sanctions    sanctions with amount range
  norm_references   norm -> unit / norm links: has_exception (target is an exception of the norm),
                    exception_of, refers_to, implements, priority_over
  condition_refs    a condition named after a provision ("đối tượng tại khoản 1 Điều 2") -> the norms of that provision
  embeddings        cached text embeddings of names (vocabulary mapping)
  name_links        entity types / attributes mapped onto the vocabulary: same (alias) or subtype
  predicate_links   alignment of predicates across articles: same (alias, renamed at compile time) or implies
                    (bridge rule; src_mode obligation/right/prohibition: having that deontic status implies dst)
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_FILE = ROOT / "data" / "legalkb" / "legal_kb.sqlite"

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
  doc_id TEXT PRIMARY KEY, number TEXT UNIQUE NOT NULL, title TEXT, doc_type TEXT, issuer TEXT,
  rank INTEGER, domain TEXT, issued TEXT, effective_from TEXT, effective_to TEXT, source_file TEXT);
CREATE TABLE IF NOT EXISTS doc_relations (
  src_number TEXT NOT NULL, rel_type TEXT NOT NULL CHECK (rel_type IN ('replaces','amends','guides','consolidates')),
  dst_number TEXT NOT NULL, PRIMARY KEY (src_number, rel_type, dst_number));
CREATE TABLE IF NOT EXISTS units (
  unit_id TEXT PRIMARY KEY, doc_number TEXT NOT NULL REFERENCES documents(number), chapter TEXT, article TEXT,
  clause TEXT, point TEXT, parent_id TEXT, title TEXT, text TEXT,
  target_doc TEXT, valid_from TEXT, valid_to TEXT);  -- versions: <doc>:D<n>@<amending doc> is the new wording
CREATE TABLE IF NOT EXISTS entity_types (
  name TEXT PRIMARY KEY, parent TEXT, description_vi TEXT, domain TEXT, origin TEXT);
CREATE TABLE IF NOT EXISTS predicates (
  name TEXT PRIMARY KEY, arity INTEGER NOT NULL,
  kind TEXT CHECK (kind IN ('relation','property','action','status')), description_vi TEXT, domain TEXT, origin TEXT);
CREATE TABLE IF NOT EXISTS predicate_args (
  pred TEXT NOT NULL REFERENCES predicates(name), position INTEGER NOT NULL, role TEXT, type TEXT,
  PRIMARY KEY (pred, position));
CREATE TABLE IF NOT EXISTS attributes (
  name TEXT PRIMARY KEY, of_type TEXT, value_type TEXT CHECK (value_type IN ('number','date','enum','text','boolean')),
  unit TEXT, description_vi TEXT, domain TEXT, origin TEXT);  -- origin: vocab (fixed vocabulary) / extracted
CREATE TABLE IF NOT EXISTS norms (
  norm_id TEXT PRIMARY KEY, unit_id TEXT NOT NULL REFERENCES units(unit_id),
  modality TEXT CHECK (modality IN ('obligation','right','prohibition','definition','consequence','procedure','sanction')),
  subject_var TEXT, bearer_var TEXT, beneficiary_var TEXT,
  action_pred TEXT, action_args TEXT, conclusion_pred TEXT, conclusion_args TEXT, conclusion_negated INTEGER,
  valid_from TEXT, valid_to TEXT, validity_note TEXT, quote TEXT,
  status TEXT DEFAULT 'draft');
CREATE TABLE IF NOT EXISTS norm_variables (
  norm_id TEXT NOT NULL REFERENCES norms(norm_id), var TEXT NOT NULL, type TEXT, PRIMARY KEY (norm_id, var));
CREATE TABLE IF NOT EXISTS norm_conditions (
  cond_id INTEGER PRIMARY KEY AUTOINCREMENT, norm_id TEXT NOT NULL REFERENCES norms(norm_id),
  alt_group INTEGER DEFAULT 0, alt_option INTEGER DEFAULT 0,
  kind TEXT CHECK (kind IN ('atom','compare')), pred TEXT, args TEXT, negated INTEGER DEFAULT 0,
  attr TEXT, of_var TEXT, op TEXT, value_num REAL, value_text TEXT, unit TEXT,
  value_attr TEXT, value_of TEXT);
CREATE TABLE IF NOT EXISTS norm_formulas (
  norm_id TEXT NOT NULL REFERENCES norms(norm_id), target_attr TEXT, of_var TEXT, expression TEXT, unit TEXT);
CREATE TABLE IF NOT EXISTS norm_deadlines (
  norm_id TEXT NOT NULL REFERENCES norms(norm_id), amount REAL, unit TEXT, from_event TEXT);
CREATE TABLE IF NOT EXISTS norm_sanctions (
  norm_id TEXT NOT NULL REFERENCES norms(norm_id), kind TEXT, min_amount REAL, max_amount REAL, unit TEXT, text TEXT);
CREATE TABLE IF NOT EXISTS norm_references (
  norm_id TEXT NOT NULL REFERENCES norms(norm_id),
  ref_kind TEXT CHECK (ref_kind IN ('has_exception','exception_of','refers_to','implements','priority_over')),
  ref_text TEXT, target_unit_id TEXT, target_norm_id TEXT);
CREATE TABLE IF NOT EXISTS predicate_links (
  src TEXT NOT NULL, src_mode TEXT NOT NULL CHECK (src_mode IN ('holds','obligation','right','prohibition')),
  rel TEXT NOT NULL CHECK (rel IN ('same','implies')), dst TEXT NOT NULL, arg_map TEXT, reason TEXT,
  PRIMARY KEY (src, src_mode, dst));
CREATE TABLE IF NOT EXISTS condition_refs (
  cond_id INTEGER NOT NULL REFERENCES norm_conditions(cond_id), target_norm_id TEXT NOT NULL,
  PRIMARY KEY (cond_id, target_norm_id));
CREATE TABLE IF NOT EXISTS embeddings (text_hash TEXT PRIMARY KEY, vec BLOB);
CREATE TABLE IF NOT EXISTS name_links (
  kind TEXT NOT NULL CHECK (kind IN ('type','attr')), src TEXT NOT NULL,
  rel TEXT NOT NULL CHECK (rel IN ('same','subtype')), dst TEXT NOT NULL, reason TEXT,
  PRIMARY KEY (kind, src, dst));
CREATE TABLE IF NOT EXISTS legal_force (
  doc_type TEXT PRIMARY KEY, number_pattern TEXT NOT NULL, issuer TEXT, rank INTEGER NOT NULL, basis TEXT);
INSERT OR IGNORE INTO legal_force VALUES
  ('Luật', '/QH\\d+$', 'Quốc hội', 2, 'Luật Ban hành VBQPPL 2015, Điều 4'),
  ('Văn bản hợp nhất (Luật)', 'VBHN-VPQH$', 'Văn phòng Quốc hội', 2,
   'Pháp lệnh Hợp nhất VBQPPL 2012: văn bản hợp nhất có hiệu lực như văn bản được hợp nhất'),
  ('Nghị định', '/NĐ-CP$', 'Chính phủ', 3, 'Luật Ban hành VBQPPL 2015, Điều 4'),
  ('Quyết định', '/QĐ-TTg$', 'Thủ tướng Chính phủ', 4, 'Luật Ban hành VBQPPL 2015, Điều 4'),
  ('Thông tư', '/TT-[A-ZĐ]+$', 'Bộ', 5, 'Luật Ban hành VBQPPL 2015, Điều 4');
CREATE TABLE IF NOT EXISTS priority_principles (
  principle TEXT PRIMARY KEY, ord INTEGER NOT NULL UNIQUE, compares TEXT, description_vi TEXT, basis TEXT);
INSERT OR IGNORE INTO priority_principles VALUES
  ('explicit', 1, 'norm_references.priority_over', 'văn bản tự quy định quy phạm nào được ưu tiên áp dụng',
   'nguyên văn quy phạm'),
  ('lex_superior', 2, 'documents.rank (legal_force)', 'áp dụng văn bản có hiệu lực pháp lý cao hơn',
   'Luật Ban hành VBQPPL 2015, Điều 156 khoản 2'),
  ('lex_posterior', 3, 'documents.issuer, documents.issued',
   'cùng một cơ quan ban hành: áp dụng văn bản ban hành sau', 'Luật Ban hành VBQPPL 2015, Điều 156 khoản 3'),
  ('lex_specialis', 4, 'norm_conditions (điều kiện bắt buộc)',
   'trong cùng một văn bản: áp dụng quy phạm cụ thể hơn (điều kiện bắt buộc bao trọn quy phạm kia)',
   'nguyên tắc chung về áp dụng pháp luật; Luật Ban hành VBQPPL không có điều khoản riêng');
CREATE TABLE IF NOT EXISTS norm_conflicts (
  norm_a TEXT NOT NULL, norm_b TEXT NOT NULL, head TEXT, winner TEXT, principle TEXT, detail TEXT,
  PRIMARY KEY (norm_a, norm_b));
CREATE INDEX IF NOT EXISTS ix_units_doc ON units(doc_number, article);
CREATE INDEX IF NOT EXISTS ix_norm_unit ON norms(unit_id);
CREATE INDEX IF NOT EXISTS ix_cond_norm ON norm_conditions(norm_id);
CREATE INDEX IF NOT EXISTS ix_ref_norm ON norm_references(norm_id);
"""


def legal_force(con: sqlite3.Connection | None = None) -> list[tuple[str, str, str, int]]:
    """(number pattern, document type, issuer, rank) from the legal_force table."""
    con = con or connect()
    return con.execute("SELECT number_pattern, doc_type, issuer, rank FROM legal_force ORDER BY rank, doc_type").fetchall()


def connect(path: Path = DB_FILE) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path), timeout=120)  # several writers (one per domain) may wait for each other
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)
    return con
