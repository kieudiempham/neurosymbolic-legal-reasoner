"""Bridge inference: emit canonical fact keys consumed by backward/forward (phase 3)."""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from pydantic import BaseModel, Field

from question_side.parse_clarify_apply import known_facts_for_reasoning
from reasoning.internal.codec import canonicalize_atom, deserialize_atom
from rulebase.rulebase_registry import RulebaseRegistry
from schemas.session import SessionState
from schemas.structured_fact import StructuredFact

logger = logging.getLogger(__name__)


class BridgeFactProvenance(BaseModel):
    fact_origin: str = "bridge"
    bridge_rule_id: str = ""
    source_domain: str = "shared"
    triggering_fact_ids: list[str] = Field(default_factory=list)
    bridge_inference_id: str = ""


class BridgeEmittedFact(BaseModel):
    """Structured bridge fact for logic-layer matching (Chặng A)."""

    fact_id: str = ""
    fact_key: str
    predicate: str = ""
    args: list[Any] = Field(default_factory=list)
    fact_domain: str = "shared"
    provenance: BridgeFactProvenance


def _atom_fields_from_key(fact_key: str) -> tuple[str, list[Any]]:
    try:
        a = canonicalize_atom(deserialize_atom(fact_key))
        return a.predicate, list(a.args)
    except Exception:
        return "", []


def _extract_entity_arguments(known_facts: dict[str, Any]) -> list[str]:
    """Extract potential entity arguments from known facts for fact instantiation."""
    entities: list[str] = []
    for k, v in known_facts.items():
        if v is True or v is False or v is None:
            continue
        # Try to extract identifiers from fact keys
        parts = k.replace("(", " ").replace(")", " ").split()
        for part in parts:
            if part and part not in ("bridge_fact", "True", "False"):
                entities.append(part)
    return list(dict.fromkeys(entities))[:8]


# Inference templates keyed like phase-2 routing bridge ids + explicit inference bridges
_INFERENCE: list[dict[str, Any]] = [
    {
        "bridge_id": "builtin_employee_to_labor",
        "when_text_contains": ["lao động", "employer", "employee", "người sử dụng lao động"],
        "emit_fact_template": "nguoi_su_dung_lao_dong({entity})",
        "generic_fallback": "bridge_fact:nguoi_su_dung_lao_dong(generic)",
    },
    {
        "bridge_id": "builtin_tax_keywords",
        "when_text_contains": ["thuế", "vat", "gtgt", "tncn", "tax"],
        "emit_fact_template": "chi_tra_thue({entity})",
        "generic_fallback": "bridge_fact:chi_tra_thue(generic)",
    },
    {
        "bridge_id": "builtin_income_to_labor",
        "when_text_contains": ["thu nhập", "income", "salary", "lương"],
        "emit_fact_template": "co_thu_nhap_lao_dong({entity})",
        "generic_fallback": "bridge_fact:co_thu_nhap_lao_dong(generic)",
    },
]


def _blob(session: SessionState, question: str) -> str:
    kf = known_facts_for_reasoning(session)
    parts = [question or ""] + [str(k) for k in kf.keys()] + [str(v) for v in kf.values() if isinstance(v, str)]
    return " ".join(parts).lower()


def run_bridge_inference(
    session: SessionState,
    question: str,
    triggered_bridge_ids: list[str],
    registry: RulebaseRegistry | None,
) -> tuple[list[BridgeEmittedFact], list[dict[str, Any]]]:
    """
    Emit facts for triggered bridges when text/fact evidence matches.
    Facts use canonical schema (not just generic) when possible.
    """
    out: list[BridgeEmittedFact] = []
    diag: list[dict[str, Any]] = []
    blob = _blob(session, question)
    seen_emit: set[str] = set()
    
    kf = known_facts_for_reasoning(session)
    entities = _extract_entity_arguments(kf)
    inf_id_base = f"bi_{uuid.uuid4().hex[:12]}"

    for rule in _INFERENCE:
        bid = str(rule.get("bridge_id") or "")
        if bid and triggered_bridge_ids and bid not in triggered_bridge_ids:
            continue
        hits = False
        for frag in rule.get("when_text_contains") or []:
            if frag.lower() in blob:
                hits = True
                break
        if not hits:
            continue
        
        # Try to instantiate fact with real entities first
        template = rule.get("emit_fact_template")
        emitted_any = False
        
        if template and "{entity}" in template and entities:
            for entity in entities[:3]:  # Limit to first 3 entities
                fact_key = template.format(entity=entity)
                if fact_key not in seen_emit:
                    seen_emit.add(fact_key)
                    inf_id = f"{inf_id_base}_{len(out)}"
                    prov = BridgeFactProvenance(
                        bridge_rule_id=bid or "inference_builtin",
                        source_domain="shared",
                        triggering_fact_ids=list(kf.keys())[:12],
                        bridge_inference_id=inf_id,
                    )
                    pred, aargs = _atom_fields_from_key(fact_key)
                    out.append(
                        BridgeEmittedFact(
                            fact_id=f"{inf_id}:{fact_key}",
                            fact_key=fact_key,
                            predicate=pred,
                            args=aargs,
                            fact_domain="shared",
                            provenance=prov,
                        )
                    )
                    diag.append({"bridge_id": bid, "fact_key": fact_key, "entity_from": entity})
                    logger.info("[bridge_inference] emitted %s via %s (entity=%s)", fact_key, bid, entity)
                    emitted_any = True
        
        # Fallback to generic if no entities matched or template unavailable
        if not emitted_any:
            fallback = rule.get("generic_fallback")
            if fallback and fallback not in seen_emit:
                seen_emit.add(fallback)
                inf_id = f"{inf_id_base}_{len(out)}"
                prov = BridgeFactProvenance(
                    bridge_rule_id=bid or "inference_builtin",
                    source_domain="shared",
                    triggering_fact_ids=list(kf.keys())[:12],
                    bridge_inference_id=inf_id,
                )
                pred, aargs = _atom_fields_from_key(fallback)
                out.append(
                    BridgeEmittedFact(
                        fact_id=f"{inf_id}:{fallback}",
                        fact_key=fallback,
                        predicate=pred,
                        args=aargs,
                        fact_domain="shared",
                        provenance=prov,
                    )
                )
                diag.append({"bridge_id": bid, "fact_key": fallback, "reason": "generic_fallback"})
                logger.info("[bridge_inference] emitted %s via %s (fallback)", fallback, bid)

    # Optional: metadata bridges on shared index declaring emit_fact_keys
    if registry and registry.get_shared():
        for r in registry.get_shared().rules or []:
            md = r.metadata or {}
            br = md.get("bridge")
            if not isinstance(br, dict):
                continue
            if not br.get("emit_fact_keys"):
                continue
            bid = str(br.get("bridge_id") or r.rule_id)
            if triggered_bridge_ids and bid not in triggered_bridge_ids:
                continue
            for fk in br.get("emit_fact_keys") or []:
                if fk in seen_emit:
                    continue
                seen_emit.add(fk)
                inf_id = f"bi_{uuid.uuid4().hex[:12]}"
                prov = BridgeFactProvenance(
                    bridge_rule_id=bid,
                    source_domain="shared",
                    triggering_fact_ids=[r.rule_id],
                    bridge_inference_id=inf_id,
                )
                pred, aargs = _atom_fields_from_key(fk)
                out.append(
                    BridgeEmittedFact(
                        fact_id=f"{inf_id}:{fk}",
                        fact_key=fk,
                        predicate=pred,
                        args=aargs,
                        fact_domain="shared",
                        provenance=prov,
                    )
                )
                diag.append({"bridge_id": bid, "fact_key": fk, "source_rule_id": r.rule_id})

    return out, diag


def apply_bridge_facts_to_session(session: SessionState, facts: list[BridgeEmittedFact]) -> None:
    for bf in facts:
        session.known_facts[bf.fact_key] = True
        sf = StructuredFact(
            fact_id=bf.fact_id or bf.fact_key,
            predicate=bf.predicate,
            args=list(bf.args),
            fact_origin="bridge",
            fact_domain=bf.fact_domain,
            serialized_key=bf.fact_key,
            bridge_rule_id=bf.provenance.bridge_rule_id,
            triggering_fact_ids=list(bf.provenance.triggering_fact_ids),
            provenance={
                "bridge_inference_id": bf.provenance.bridge_inference_id,
                "source_domain": bf.provenance.source_domain,
            },
        )
        session.structured_facts[bf.fact_key] = sf.model_dump(mode="json")
        logger.debug("[bridge_apply] set known_facts[%r] = True via bridge", bf.fact_key)
