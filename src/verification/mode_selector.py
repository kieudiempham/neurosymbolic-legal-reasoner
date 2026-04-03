"""Select verification strictness (research demo — simple toggles)."""


def use_nli_for(mode: str, *, nesy_nli_mock: bool = True) -> bool:
    if mode == "parse_verification":
        return False
    return not nesy_nli_mock or mode in ("answer_verification",)


def symbolic_strict(mode: str) -> bool:
    return mode in ("backward_verification", "forward_verification")
