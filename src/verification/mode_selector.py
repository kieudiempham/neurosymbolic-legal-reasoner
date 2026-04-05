"""Select verification strictness (research demo — simple toggles)."""


def use_nli_for(mode: str, *, nesy_nli_mock: bool = False, nli_degraded: bool = False) -> bool:
    """
    When ``nli_degraded`` is True, NLI is skipped for every mode (symbolic-only; must be traced explicitly).

    When ``nesy_nli_mock`` is True, only ``answer_verification`` runs NLI (dev/test shortcut).

    Otherwise NLI runs for all five NeSy modes (parse / rule / backward / forward / answer).
    """
    if nli_degraded:
        return False
    if nesy_nli_mock:
        return mode == "answer_verification"
    return mode in (
        "parse_verification",
        "rule_verification",
        "backward_verification",
        "forward_verification",
        "answer_verification",
    )


def symbolic_strict(mode: str) -> bool:
    return mode in ("backward_verification", "forward_verification")
