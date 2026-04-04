"""Canonical atom representation + stable serialization for session/API boundaries."""

from __future__ import annotations

import re
from typing import Any

from reasoning.internal.models import Atom


def canonicalize_atom(atom: Atom) -> Atom:
    """Chuẩn hóa nhẹ: predicate strip, args giữ nguyên kiểu (slug VN không dấu)."""
    pred = (atom.predicate or "").strip()
    args: list[Any] = []
    for a in atom.args:
        if isinstance(a, str):
            args.append(a.strip())
        else:
            args.append(a)
    return Atom(predicate=pred, args=tuple(args))


def serialize_atom(atom: Atom) -> str:
    """Chuỗi ổn định cho `known_facts` / session (boundary)."""
    c = canonicalize_atom(atom)
    inner = ",".join(_serialize_arg(x) for x in c.args)
    return f"{c.predicate}({inner})"


def _serialize_arg(x: Any) -> str:
    if isinstance(x, (list, tuple)):
        return "[" + ",".join(_serialize_arg(i) for i in x) + "]"
    return str(x)


_ATOM_RE = re.compile(r"^([^(]+)\((.*)\)\s*$", re.DOTALL)


def deserialize_atom(s: str) -> Atom:
    """
    Parse `predicate(a,b)` — không hỗ trợ dấu phẩy trong chuỗi arg (đúng với rulebase hiện tại).
    """
    m = _ATOM_RE.match(s.strip())
    if not m:
        return Atom(predicate=s.strip(), args=())
    pred, inner = m.group(1).strip(), m.group(2).strip()
    if not inner:
        return Atom(predicate=pred, args=())
    parts = _split_args(inner)
    return Atom(predicate=pred, args=tuple(_parse_arg(p) for p in parts))


def _split_args(inner: str) -> list[str]:
    out: list[str] = []
    depth = 0
    cur: list[str] = []
    for ch in inner:
        if ch == "," and depth == 0:
            out.append("".join(cur).strip())
            cur = []
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth = max(0, depth - 1)
        cur.append(ch)
    if cur:
        out.append("".join(cur).strip())
    return out


def _parse_arg(p: str) -> Any:
    p = p.strip()
    if p.startswith("[") and p.endswith("]"):
        inner = p[1:-1].strip()
        if not inner:
            return []
        return [_parse_arg(x) for x in _split_args(inner)]
    try:
        if "." in p:
            return float(p)
        return int(p)
    except ValueError:
        pass
    if p.lower() in ("true", "false"):
        return p.lower() == "true"
    return p


def atoms_equal(a: Atom, b: Atom) -> bool:
    ca, cb = canonicalize_atom(a), canonicalize_atom(b)
    return ca.predicate == cb.predicate and ca.args == cb.args


def atom_from_dict(predicate: str, args: list[Any] | None) -> Atom:
    return Atom(predicate=predicate, args=tuple(args or []))


def goal_dict_to_tuple(goal: dict[str, Any]) -> tuple[Any, ...]:
    """Goal runtime `Layer2Parse.goal` -> tuple (predicate, *args) để so khớp `goal_atom`."""
    p = goal.get("predicate")
    args = goal.get("args") or []
    return (p, *list(args))


def tuple_to_goal_dict(t: tuple[Any, ...]) -> dict[str, Any]:
    if not t:
        return {"predicate": "unknown", "args": []}
    return {"predicate": t[0], "args": list(t[1:])}
