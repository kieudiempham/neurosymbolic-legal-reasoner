"""Compatibility shim for code paths that still mention ``load_rulebase`` / file-only index.

Phase 2 main runtime uses :class:`RulebaseRegistry` via :mod:`runtime.qa_runtime`.
Prefer :func:`retrieval.rulebase_loader.get_rulebase_index` — it delegates to the global registry when set.
"""

from __future__ import annotations

__all__: list[str] = []
