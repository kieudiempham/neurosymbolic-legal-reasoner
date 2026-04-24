#!/usr/bin/env python3
"""Quick CLI demo for HF NLI (Vietnamese examples). Run from repo root:

  pip install torch transformers
  set PYTHONPATH=src
  python scripts/nli_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    sys.path.insert(0, str(src))

    from runtime.nli.service import init_nli_service, reset_nli_service
    from runtime.nli.types import NLIRuntimeConfig

    reset_nli_service()
    cfg = NLIRuntimeConfig()
    svc = init_nli_service(cfg)

    premise = (
        "Người thành lập doanh nghiệp phải nộp hồ sơ đăng ký doanh nghiệp cho cơ quan đăng ký kinh doanh."
    )
    cases = [
        "Người thành lập doanh nghiệp có nghĩa vụ nộp hồ sơ đăng ký doanh nghiệp.",
        "Người thành lập doanh nghiệp không cần nộp hồ sơ đăng ký doanh nghiệp.",
        "Người thành lập doanh nghiệp phải nộp thuế thu nhập cá nhân trong ngày đăng ký.",
    ]
    for i, hyp in enumerate(cases, 1):
        d = svc.predict(premise, hyp)
        print(f"--- Case {i} ---")
        print("label:", d["label"])
        print("scores:", d["scores"])
    reset_nli_service()


if __name__ == "__main__":
    main()
