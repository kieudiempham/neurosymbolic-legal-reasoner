"""First-class evidence retrieval stage: build normalized evidence bundle with provenance linkage."""

from __future__ import annotations

from typing import Any

from schemas.evidence import EvidenceBundle, EvidenceRecord, EvidenceSnippet
from schemas.reasoning import RequirementItem
from schemas.rule import RuleRecord
from utils.ids import new_id
from utils.text import lower_fold


def _extract_subgoals_from_proof(proof: Any | None) -> list[str]:
    out: list[str] = []
    if proof is None:
        return out
    for step in getattr(proof, "proof_steps", None) or []:
        for key in list(getattr(step, "fact_keys", None) or []):
            s = str(key).strip()
            if s:
                out.append(s)
        for p in list(getattr(step, "premises", None) or []):
            s = str(p).strip()
            if s:
                out.append(s)
        for atom in list(getattr(step, "supporting_atoms", None) or []):
            s = str(atom).strip()
            if s:
                out.append(s)
    dedup: list[str] = []
    seen: set[str] = set()
    for x in out:
        if x in seen:
            continue
        seen.add(x)
        dedup.append(x)
    return dedup


def _link_best_subgoal(text_span: str, subgoals: list[str]) -> str | None:
    if not subgoals:
        return None
    t = lower_fold(text_span)
    best: tuple[int, str] | None = None
    for sg in subgoals:
        toks = [tok for tok in lower_fold(str(sg)).split() if len(tok) > 2]
        overlap = sum(1 for tok in toks if tok in t)
        if overlap <= 0:
            continue
        if best is None or overlap > best[0]:
            best = (overlap, sg)
    return best[1] if best else None


def build_evidence_bundle(
    *,
    query: str,
    selected_rule: RuleRecord | None,
    requirement_set: list[RequirementItem] | None,
    proof: Any | None,
    snippets: list[EvidenceSnippet],
) -> EvidenceBundle:
    requirement_keys = [str(r.key) for r in (requirement_set or []) if str(r.key).strip()]
    proof_subgoals = _extract_subgoals_from_proof(proof)
    subgoals = proof_subgoals or requirement_keys

    items: list[EvidenceRecord] = []
    linkage_map: dict[str, list[str]] = {}

    for idx, sn in enumerate(snippets, start=1):
        linked = _link_best_subgoal(sn.text, subgoals)
        eid = f"evi_{idx}_{new_id('k')[-6:]}"
        if linked:
            linkage_map.setdefault(linked, []).append(eid)
        statute_id = None
        src = str(sn.source_doc or "")
        if src:
            statute_id = src.split("-")[0].strip() if "-" in src else src.strip()[:80]

        rec = EvidenceRecord(
            evidence_id=eid,
            source_type="corpus_chunk",
            statute_id=statute_id or None,
            article=sn.article,
            clause=sn.clause,
            text_span=(sn.text or "")[:1200],
            linked_subgoal=linked,
            support_score=float(sn.score) if sn.score is not None else None,
            contradiction_score=None,
            provenance={
                "chunk_id": sn.chunk_id,
                "doc_id": sn.doc_id,
                "source_doc": sn.source_doc,
                "source_ref": sn.source_ref,
                "article_clause": sn.article_clause,
                "page": sn.page,
                "linked_rule_id": sn.linked_rule_id,
                "retrieval_reason": sn.retrieval_reason,
                "score_breakdown": sn.score_breakdown,
            },
        )
        items.append(rec)

    return EvidenceBundle(
        bundle_id=new_id("evidence_bundle"),
        query_text=query,
        selected_rule_id=selected_rule.rule_id if selected_rule else None,
        requirement_set=requirement_keys,
        proof_subgoals=proof_subgoals,
        items=items,
        linkage_map=linkage_map,
        provenance={
            "stage": "evidence_retrieval",
            "selected_rule_id": selected_rule.rule_id if selected_rule else None,
            "inputs": {
                "query_present": bool(query),
                "requirement_count": len(requirement_keys),
                "proof_subgoal_count": len(proof_subgoals),
                "snippet_count": len(snippets),
            },
        },
    )
