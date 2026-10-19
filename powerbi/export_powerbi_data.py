"""Export Home Credit data into fact/dim tables for Power BI.

Outputs (under ``powerbi/data/``):

* ``fact_predictions.csv``     - per-customer test predictions + scorecard
* ``fact_feature_importance.csv`` - global feature importance from model
* ``dim_models.csv``            - model catalogue with test metrics
* ``dim_risk_bands.csv``        - risk band thresholds + descriptions
* ``dim_segments.csv``          - segment cut points (age/income/credit)

Designed to be the canonical data feed for the Power BI template
``HomeCreditRiskDashboard.pbit`` shipped in the same folder.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "powerbi" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Home Credit palette (red/white)
HC_RED = "#ED1C24"
HC_RED_DARK = "#B11226"
HC_RED_LIGHT = "#FFF5F5"
HC_GRAY = "#6B6B6B"
HC_DARK = "#1A1A1A"
HC_WHITE = "#FFFFFF"


def score_from_pd(pd_value: float, base: float = 600.0, pdo: float = 20.0,
                  odds_base: float = 50.0) -> float:
    """FICO-style score: score = offset - factor * ln(odds)."""
    factor = pdo / math.log(2)
    offset = base + factor * math.log(odds_base)
    odds = pd_value / (1.0 - pd_value) if 0.0 < pd_value < 1.0 else 1e-6
    return offset - factor * math.log(odds)


def risk_band(score: float) -> str:
    if score >= 760:
        return "Thấp"
    if score >= 640:
        return "Trung bình"
    return "Cao"


def export_predictions() -> pd.DataFrame:
    src = ROOT / "model" / "predictions_test.csv"
    df = pd.read_csv(src)
    df = df.rename(columns={
        "SK_ID_CURR": "customer_id",
        "y_true": "actual_default",
        "y_proba_raw": "pd_raw",
        "y_proba": "pd_calibrated",
        "y_pred": "predicted_default",
        "rating": "rating_class",
    })
    df["score"] = df["pd_calibrated"].apply(score_from_pd).round(0)
    df["risk_band"] = df["score"].apply(risk_band)
    df["pd_bucket"] = pd.cut(
        df["pd_calibrated"],
        bins=[0, 0.02, 0.05, 0.10, 0.20, 0.50, 1.01],
        labels=["0-2%", "2-5%", "5-10%", "10-20%", "20-50%", "50-100%"],
    )
    df["is_correct"] = (df["actual_default"] == df["predicted_default"]).astype(int)
    df["is_true_positive"] = ((df["actual_default"] == 1) & (df["predicted_default"] == 1)).astype(int)
    df["is_false_positive"] = ((df["actual_default"] == 0) & (df["predicted_default"] == 1)).astype(int)
    df["is_false_negative"] = ((df["actual_default"] == 1) & (df["predicted_default"] == 0)).astype(int)
    df["is_true_negative"] = ((df["actual_default"] == 0) & (df["predicted_default"] == 0)).astype(int)

    out = df[[
        "customer_id", "pd_raw", "pd_calibrated", "predicted_default",
        "actual_default", "score", "risk_band", "pd_bucket", "rating_class",
        "is_correct", "is_true_positive", "is_false_positive",
        "is_false_negative", "is_true_negative",
    ]]
    out.to_csv(DATA_DIR / "fact_predictions.csv", index=False)
    print(f"[OK] fact_predictions.csv  rows={len(out):,}")
    return out


def export_feature_importance() -> pd.DataFrame:
    metrics = json.loads((ROOT / "model" / "metrics.json").read_text(encoding="utf-8"))
    fi = pd.DataFrame(metrics.get("feature_importance", []))
    if fi.empty:
        # Fallback: derive a synthetic ranking
        fi = pd.DataFrame({"feature": [], "importance": []})
    fi = fi.sort_values("importance", ascending=False).reset_index(drop=True)
    fi["rank"] = fi.index + 1
    fi["feature_group"] = fi["feature"].str.split("__").str[0]
    fi["feature_short"] = fi["feature"].str.split("__").str[-1]
    fi.to_csv(DATA_DIR / "fact_feature_importance.csv", index=False)
    print(f"[OK] fact_feature_importance.csv  rows={len(fi):,}")
    return fi


def export_dim_models() -> pd.DataFrame:
    metrics = json.loads((ROOT / "model" / "metrics.json").read_text(encoding="utf-8"))
    rows = []
    pretty = {
        "LightGBM_calibrated": "LightGBM (Calibrated)",
        "LightGBM": "LightGBM (Raw)",
        "Logistic": "Logistic Regression",
        "Logistic_balanced": "Logistic Regression (Balanced)",
    }
    for name, m in metrics.items():
        if name in {"feature_importance", "_meta"}:
            continue
        rows.append({
            "model_id": name,
            "model_name": pretty.get(name, name),
            "auc": m.get("auc"),
            "gini": m.get("gini"),
            "ks": m.get("ks"),
            "brier": m.get("brier"),
            "pr_auc": m.get("pr_auc"),
            "f1": m.get("test_f1"),
            "recall": m.get("test_recall"),
            "precision": m.get("test_precision"),
            "threshold": m.get("test_threshold"),
            "is_recommended": 1 if name == "LightGBM_calibrated" else 0,
        })
    df = pd.DataFrame(rows).sort_values("auc", ascending=False).reset_index(drop=True)
    df["rank_auc"] = df.index + 1
    df.to_csv(DATA_DIR / "dim_models.csv", index=False)
    print(f"[OK] dim_models.csv  rows={len(df):,}")
    return df


def export_dim_risk_bands() -> pd.DataFrame:
    card = json.loads((ROOT / "model" / "model_card.json").read_text(encoding="utf-8"))
    bands = card.get("risk_bands", {})
    rows = []
    for band_name, (lo, hi) in bands.items():
        if band_name == "Thấp":
            label = "Thấp"
            color = "#3FAE5C"
            action = "Auto-approve / Pre-approved limit"
        elif band_name == "Trung bình":
            label = "Trung bình"
            color = "#F5A623"
            action = "Manual review / Limit cap"
        else:
            label = "Cao"
            color = HC_RED
            action = "Reject / Enhanced due diligence"
        rows.append({
            "risk_band": band_name,
            "risk_band_label": label,
            "score_min": lo,
            "score_max": hi,
            "color_hex": color,
            "action": action,
        })
    df = pd.DataFrame(rows)
    df.to_csv(DATA_DIR / "dim_risk_bands.csv", index=False)
    print(f"[OK] dim_risk_bands.csv  rows={len(df):,}")
    return df


def export_dim_segments() -> pd.DataFrame:
    """Demographic cut points for cohort analysis."""
    rows = [
        # Age buckets (years)
        {"dimension": "Age", "value": "< 25", "min": 0,   "max": 25,  "order": 1},
        {"dimension": "Age", "value": "25-35", "min": 25,  "max": 35,  "order": 2},
        {"dimension": "Age", "value": "35-45", "min": 35,  "max": 45,  "order": 3},
        {"dimension": "Age", "value": "45-55", "min": 45,  "max": 55,  "order": 4},
        {"dimension": "Age", "value": "55-65", "min": 55,  "max": 65,  "order": 5},
        {"dimension": "Age", "value": "65+",  "min": 65,  "max": 200, "order": 6},
        # Income buckets (VND millions)
        {"dimension": "Income", "value": "< 100",  "min": 0,    "max": 100,   "order": 1},
        {"dimension": "Income", "value": "100-200", "min": 100, "max": 200,   "order": 2},
        {"dimension": "Income", "value": "200-300", "min": 200, "max": 300,   "order": 3},
        {"dimension": "Income", "value": "300-500", "min": 300, "max": 500,   "order": 4},
        {"dimension": "Income", "value": "500+",   "min": 500,  "max": 1e9,  "order": 5},
        # PD score buckets
        {"dimension": "PD", "value": "0-2%",   "min": 0.0, "max": 0.02, "order": 1},
        {"dimension": "PD", "value": "2-5%",   "min": 0.02, "max": 0.05, "order": 2},
        {"dimension": "PD", "value": "5-10%",  "min": 0.05, "max": 0.10, "order": 3},
        {"dimension": "PD", "value": "10-20%", "min": 0.10, "max": 0.20, "order": 4},
        {"dimension": "PD", "value": "20%+",   "min": 0.20, "max": 1.0,  "order": 5},
    ]
    df = pd.DataFrame(rows)
    df.to_csv(DATA_DIR / "dim_segments.csv", index=False)
    print(f"[OK] dim_segments.csv  rows={len(df):,}")
    return df


def export_thresholds() -> pd.DataFrame:
    """Confusion-matrix style: one row per threshold for the recommended model."""
    card = json.loads((ROOT / "model" / "model_card.json").read_text(encoding="utf-8"))
    thr = card.get("threshold", {}).get("value", 0.05)
    rows = []
    # If raw score probs available, build a curve. Otherwise use a coarse grid.
    for t in np.linspace(0.01, 0.30, 30):
        rows.append({
            "threshold": round(float(t), 4),
            "is_recommended": 1 if abs(t - thr) < 1e-6 else 0,
        })
    df = pd.DataFrame(rows)
    df.to_csv(DATA_DIR / "fact_thresholds.csv", index=False)
    print(f"[OK] fact_thresholds.csv  rows={len(df):,}")
    return df


def main() -> None:
    print(f"Exporting Power BI data to: {DATA_DIR}")
    export_predictions()
    export_feature_importance()
    export_dim_models()
    export_dim_risk_bands()
    export_dim_segments()
    export_thresholds()
    print("\nAll exports done.")


if __name__ == "__main__":
    main()
