"""Paper figures from saved results (no re-running).

    PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.make_figures   -> experiments/figures/*.pdf|png

Figure 1: QA accuracy vs clarification budget (0, 1, 2, unlimited) — Ours, Heuristic, no-MBD.
Figure 2: ablation — QA accuracy per variant, fault-level F1 printed under each bar.
Colours: validated categorical slots (blue, orange, aqua); identity also carried by marker shape and a
direct end label, so the figures survive grayscale print.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments" / "figures"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def style(ax) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def fig_budget() -> None:
    b = json.loads((ROOT / "experiments" / "budget" / "budget_results.json").read_text(encoding="utf-8"))
    xs, ticks = [0, 1, 2, 3], ["0", "1", "2", "unlimited"]
    series = [("nesy_diag", "Ours (MBD)", BLUE, "o"), ("rule_check", "Heuristic", ORANGE, "s"),
              ("no_mbd", "No MBD", AQUA, "^")]
    fig, ax = plt.subplots(figsize=(4.6, 3.0), dpi=200)
    offsets = {"nesy_diag": -9, "rule_check": 9, "no_mbd": 0}  # Ours and Heuristic end at the same value
    for key, name, color, marker in series:
        ys = [100 * b[f"{key}|{k}"]["qa_acc"] for k in ("0", "1", "2", "inf")]
        ax.plot(xs, ys, color=color, linewidth=2, marker=marker, markersize=6, markeredgecolor="white",
                markeredgewidth=1, label=name, zorder=3)
        ax.annotate(f"{name}  {ys[-1]:.1f}", (xs[-1], ys[-1]), xytext=(8, offsets[key]), textcoords="offset points",
                    va="center", fontsize=8.5, color=INK)
    ax.set_xticks(xs, ticks)
    ax.set_xlim(-0.2, 4.4)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Clarification questions the user answers per query", fontsize=9, color=INK)
    ax.set_ylabel("QA accuracy (%)", fontsize=9, color=INK)
    style(ax)
    ax.legend(frameon=False, fontsize=8.5, loc="lower right", bbox_to_anchor=(0.78, 0.02))
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"fig1_clarification_budget.{ext}", bbox_inches="tight")
    plt.close(fig)


def fig_ablation() -> None:
    b = json.loads((ROOT / "experiments" / "budget" / "budget_results.json").read_text(encoding="utf-8"))
    st = json.loads((ROOT / "experiments" / "strict_eval.json").read_text(encoding="utf-8"))
    rows = [("Ours\n(full)", "nesy_diag", "single|test|nesy_diag"),
            ("− acceptance\ntest", "raw_nli", "single|test|raw_nli"),
            ("− MBD", "no_mbd", "single|test|no_mbd"),
            ("− diagnosis\n& recovery", None, None)]
    qa = [100 * b[f"{k}|inf"]["qa_acc"] if k else 15.3 for _, k, _ in rows]
    f1 = [100 * st[s]["fault_f1"] if s else None for *_, s in rows]
    fig, ax = plt.subplots(figsize=(4.6, 3.0), dpi=200)
    xs = range(len(rows))
    bars = ax.bar(xs, qa, width=0.62, color=BLUE, edgecolor="white", linewidth=2, zorder=3)
    for x, bar, v, f in zip(xs, bars, qa, f1):
        ax.text(x, v + 2, f"{v:.1f}", ha="center", va="bottom", fontsize=9, color=INK, fontweight="bold")
    labels = [r[0] + "\n" + ("Fault F1: –" if f is None else f"Fault F1: {f:.1f}") for r, f in zip(rows, f1)]
    ax.set_xticks(list(xs), labels, fontsize=8)
    ax.set_ylim(0, 100)
    ax.set_ylabel("QA accuracy (%)", fontsize=9, color=INK)
    style(ax)
    ax.tick_params(axis="x", length=0, pad=4)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"fig2_ablation.{ext}", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig_budget()
    fig_ablation()
    print("wrote", sorted(p.name for p in OUT.iterdir()))


if __name__ == "__main__":
    main()
