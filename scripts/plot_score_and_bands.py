"""Generate Figure 13 (score distribution) and Figure 14 (default rate by band).

Reads `model/predictions_test.csv` (output of notebook cell 21) and
`model/model_card.json` (for risk bands + scorecard params), recomputes
the FICO-like score, and writes two PNGs to `model/`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Force UTF-8 stdout so Vietnamese band labels print on Windows cp1252 consoles
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import matplotlib

matplotlib.use("Agg")  # headless: no display needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "model"
PRED_CSV = MODEL_DIR / "predictions_test.csv"
CARD_JSON = MODEL_DIR / "model_card.json"
OUT_13 = MODEL_DIR / "fig13_score_distribution.png"
OUT_14 = MODEL_DIR / "fig14_default_by_band.png"

# Default risk bands (3-tier). Overridden from model_card.json if available.
DEFAULT_BANDS: dict[str, tuple[float, float]] = {
    "Thấp":        (760, 1000),
    "Trung bình":  (640, 760),
    "Cao":         (300, 640),
}

BAND_COLORS = {
    "Thấp":        "#2ca02c",
    "Trung bình":  "#ffc107",
    "Cao":         "#d62728",
    # fallbacks for 5-tier English labels
    "Excellent":   "#2ca02c",
    "Good":        "#7fcb3a",
    "Fair":        "#ffc107",
    "Poor":        "#ff7f0e",
    "Very Poor":   "#d62728",
}


def load_card() -> tuple[float, float, dict[str, tuple[float, float]]]:
    """Read scorecard offset/factor and risk bands from model_card.json."""
    if not CARD_JSON.exists():
        return 712.88, 28.85, DEFAULT_BANDS
    with open(CARD_JSON, "r", encoding="utf-8") as f:
        card = json.load(f)
    sc = card.get("scorecard", {})
    offset = float(sc.get("offset", 712.88))
    factor = float(sc.get("factor", 28.85))
    bands = card.get("risk_bands", DEFAULT_BANDS)
    parsed: dict[str, tuple[float, float]] = {}
    for label, rng in bands.items():
        lo, hi = float(rng[0]), float(rng[1])
        parsed[label] = (min(lo, hi), max(lo, hi))
    return offset, factor, parsed


def pd_to_score(p: np.ndarray | float, offset: float, factor: float) -> np.ndarray | float:
    odds = np.clip(p / (1 - p), 1e-6, 1 - 1e-6)
    return offset - factor * np.log(odds)


def score_to_band(s: float, bands: dict[str, tuple[float, float]]) -> str:
    # Iterate in descending order of lower bound so high scores match first
    for label, (lo, hi) in sorted(
        bands.items(), key=lambda kv: -kv[1][0]
    ):
        if lo <= s < hi:
            return label
    # Fallback: assign to nearest band
    nearest = min(bands.items(), key=lambda kv: min(abs(s - kv[1][0]), abs(s - kv[1][1])))
    return nearest[0]


def main() -> None:
    if not PRED_CSV.exists():
        raise FileNotFoundError(
            f"Missing {PRED_CSV}. Re-run notebook cell 21 first."
        )

    offset, factor, RISK_BANDS = load_card()
    print(f"Scorecard offset={offset:.2f} factor={factor:.4f}")
    safe_bands = {k: (int(v[0]), int(v[1])) for k, v in RISK_BANDS.items()}
    print(f"Risk bands: {safe_bands}")

    df = pd.read_csv(PRED_CSV)
    print(f"\nLoaded {len(df):,} test predictions from {PRED_CSV.name}")
    print(f"  Columns: {list(df.columns)}")
    print(f"  y_proba range: [{df['y_proba'].min():.4f}, {df['y_proba'].max():.4f}]")
    print(f"  default rate:  {df['y_true'].mean():.2%}")

    # ── Recompute score from calibrated PD ──
    df["score"] = pd_to_score(df["y_proba"].values, offset, factor)
    print(f"  score range:   [{df['score'].min():.1f}, {df['score'].max():.1f}]")

    # ── Figure 13 ──────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(11, 5.5))
    counts, bins, _ = ax.hist(
        df["score"], bins=50, color="#1f77b4", alpha=0.75, edgecolor="white"
    )
    ymax = counts.max() * 1.05
    for label, (lo, hi) in RISK_BANDS.items():
        color = BAND_COLORS.get(label, "#666")
        ax.axvspan(lo, hi, alpha=0.10, color=color, zorder=0)
        ax.axvline(lo, color=color, linestyle="--", linewidth=1.0, alpha=0.7)
        ax.text(
            lo + (hi - lo) * 0.02, ymax * 0.93, f"{label}\n[{lo:.0f}, {hi:.0f})",
            color=color, fontsize=8.5, fontweight="bold", va="top",
        )
    ax.set_xlabel("FICO-like score")
    ax.set_ylabel("Number of applicants")
    ax.set_title(
        f"Figure 13. Score distribution and risk-band boundaries "
        f"(n={len(df):,})"
    )
    ax.set_xlim(300, 1010)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_13, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {OUT_13.name}")

    # ── Figure 14 ──────────────────────────────────────────────────────────
    df["RiskBand"] = df["score"].apply(lambda s: score_to_band(s, RISK_BANDS))
    band_order = list(RISK_BANDS.keys())
    grouped = (
        df.groupby("RiskBand")
        .agg(n=("y_true", "size"), default_rate=("y_true", "mean"))
        .reindex(band_order)
    )
    grouped["default_rate_pct"] = grouped["default_rate"] * 100

    fig, ax = plt.subplots(figsize=(9, 5.5))
    colors = [BAND_COLORS.get(b, "#666") for b in grouped.index]
    bars = ax.bar(
        grouped.index,
        grouped["default_rate_pct"].fillna(0),
        color=colors,
        edgecolor="white",
        linewidth=1.2,
    )
    for bar, v, n in zip(bars, grouped["default_rate_pct"], grouped["n"]):
        if pd.isna(v):
            continue
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            v + 0.5,
            f"{v:.2f}%\n(n={n:,})",
            ha="center",
            fontsize=10,
            fontweight="bold",
        )
    ax.set_ylabel("Empirical default rate (%)")
    ax.set_xlabel("Risk band")
    ax.set_title(
        f"Figure 14. Empirical default rate by risk band "
        f"(n={len(df):,})"
    )
    ymax_14 = max(
        grouped["default_rate_pct"].fillna(0).max() * 1.3,
        10.0,
    )
    ax.set_ylim(0, ymax_14)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_14, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {OUT_14.name}")

    # ── Print table for verification ──
    print("\nRisk band summary (test set):")
    print(
        grouped[["n", "default_rate_pct"]]
        .rename(columns={"default_rate_pct": "default_rate_%"})
        .to_string()
    )


if __name__ == "__main__":
    main()
