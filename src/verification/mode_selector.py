"""Select verification strictness (research demo — simple toggles)."""


def use_nli_for(mode: str, *, nesy_nli_mock: bool = True) -> bool:
    """
    When `nesy_nli_mock` is True, only `answer_verification` runs NLI (cheap heuristic mock).

    When `nesy_nli_mock` is False, NLI runs for all five NeSy modes (parse / rule / backward / forward / answer),
    typically backed by a real model (HF or API).
    """
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
