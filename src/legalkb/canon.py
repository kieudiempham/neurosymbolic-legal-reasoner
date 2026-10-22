"""Corpus-wide canonicalisation of names, after all documents are extracted (semantic candidates + LLM labels).

Token overlap (align.shortlist) misses synonyms written differently (du_tuoi_nghi_huu / dat_tuoi_huu_tri), so here
candidates come from embeddings of "name — description" (text-embedding-3-small, cached in the embeddings table) and
the pairs are labelled by align.align with a stronger model. Four passes:
  types     extracted entity types -> vocabulary types (same / subtype): connects variables to the type hierarchy
  attrs     extracted attributes -> vocabulary attributes (same)
  chains    condition predicates no norm concludes -> predicates some norm concludes, or vocabulary predicates
            (same / implies): this is what lets a conclusion of one article satisfy a condition of another
  vocab     remaining extracted predicates -> vocabulary predicates (same), only for close candidates
"""

from __future__ import annotations

import hashlib
import os
import time

import numpy as np

from .align import align
from .extract import Extractor

EMBED_MODEL = "text-embedding-3-small"
CANON_MODEL = os.environ.get("LEGALKB_CANON_MODEL", "gpt-4.1")
_TABLE = {"pred": "predicates", "type": "entity_types", "attr": "attributes"}


def embed(con, client, texts: list[str]) -> np.ndarray:
    """Unit-normalised embeddings, cached by text hash."""
    keys = [hashlib.sha1(f"{EMBED_MODEL}|{t}".encode("utf-8")).hexdigest() for t in texts]
    have = {k: np.frombuffer(v, dtype=np.float32) for k, v in con.execute(
        f"SELECT text_hash, vec FROM embeddings WHERE text_hash IN ({','.join('?' * len(keys))})", keys)} if keys else {}
    todo = [(k, t) for k, t in zip(keys, texts) if k not in have]
    for i in range(0, len(todo), 500):
        chunk = todo[i: i + 500]
        for attempt in range(6):
            try:
                r = client.embeddings.create(model=EMBED_MODEL, input=[t[:500] for _, t in chunk])
                break
            except Exception as e:  # noqa: BLE001
                if "insufficient_quota" in str(e):
                    raise
                time.sleep(5 * 2 ** attempt)
        for (k, _), d in zip(chunk, r.data):
            v = np.asarray(d.embedding, dtype=np.float32)
            have[k] = v / np.linalg.norm(v)
            con.execute("INSERT OR REPLACE INTO embeddings VALUES (?,?)", (k, have[k].tobytes()))
    con.commit()
    return np.stack([have[k] for k in keys]) if keys else np.zeros((0, 1536), dtype=np.float32)


def _texts(con, kind: str, names: list[str]) -> list[str]:
    desc = dict(con.execute(f"SELECT name, description_vi FROM {_TABLE[kind]}"))
    return [f"{n.replace('_', ' ')} — {desc.get(n) or ''}" for n in names]


def candidates(con, client, kind: str, sources: list[str], targets: list[str], k: int, min_cos: float) -> dict:
    """source -> its k nearest targets (cosine >= min_cos), the source itself excluded."""
    if not sources or not targets:
        return {}
    s, t = embed(con, client, _texts(con, kind, sources)), embed(con, client, _texts(con, kind, targets))
    sim = s @ t.T
    out = {}
    for i, name in enumerate(sources):
        order = np.argsort(-sim[i])[: k + 1]
        cands = [targets[j] for j in order if sim[i, j] >= min_cos and targets[j] != name][:k]
        if cands:
            out[name] = cands
    return out


PASSES = ("types", "attrs", "chains", "vocab")


def canonicalise(con, workers: int = 16, passes: tuple[str, ...] = PASSES, model: str = CANON_MODEL) -> dict:
    ex = Extractor(model)
    q = lambda sql: [n for (n,) in con.execute(sql)]  # noqa: E731
    vocab = {kind: q(f"SELECT name FROM {t} WHERE origin='vocab'") for kind, t in _TABLE.items()}
    linked_types = set(q("SELECT src FROM name_links WHERE kind='type'"))
    linked_attrs = set(q("SELECT src FROM name_links WHERE kind='attr'"))
    linked_preds = set(q("SELECT src FROM predicate_links"))
    concluded = set(q("SELECT DISTINCT conclusion_pred FROM norms WHERE conclusion_pred IS NOT NULL"))
    report = {}

    def run(name, kind, sources, targets, k, min_cos):
        if name not in passes:
            return
        c = candidates(con, ex.client, kind, sorted(sources), sorted(targets), k, min_cos)
        t0 = time.time()
        n = align(con, ex.client, model, {kind: set(c)}, "", workers, candidates=c)
        con.commit()
        report[name] = {"sources": len(sources), "with_candidates": len(c), "links": n, "seconds": round(time.time() - t0)}
        print(name, report[name], flush=True)

    run("types", "type", set(q("SELECT name FROM entity_types WHERE origin='extracted'")) - linked_types,
        vocab["type"], 6, 0.45)
    run("attrs", "attr", set(q("SELECT name FROM attributes WHERE origin='extracted'")) - linked_attrs,
        vocab["attr"], 6, 0.5)
    cond_preds = set(q("SELECT DISTINCT pred FROM norm_conditions WHERE kind='atom' AND pred IS NOT NULL"))
    run("chains", "pred", cond_preds - concluded - linked_preds, concluded | set(vocab["pred"]), 6, 0.5)
    used = set(q("SELECT action_pred FROM norms WHERE action_pred IS NOT NULL")) | concluded
    extracted = set(q("SELECT name FROM predicates WHERE origin='extracted'"))
    run("vocab", "pred", (used & extracted) - set(q("SELECT src FROM predicate_links")), vocab["pred"], 4, 0.62)
    return report
