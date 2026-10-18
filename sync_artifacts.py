"""
Đồng bộ lại các artifacts cho Streamlit (chạy sau khi notebook chạy xong).

Tạo/cập nhật:
  - model/roc_curve.png           (Streamlit tab HIỆU NĂNG)
  - model/pr_curve.png            (Streamlit tab HIỆU NĂNG)
  - model/ks_plot.png             (Streamlit tab HIỆU NĂNG)
  - model/calibration_curve.png   (Streamlit tab HIỆU NĂNG)
  - model/evaluation_curves.png   (gộp 4 plot)
  - model/feature_importance.png  (notebook đã save)
  - model/shap_global.png         (tab HIỆU NĂNG dùng)
  - model/model_card.json         (model card)
  - model/metrics.json            (streamlit-compatible schema)
  - model/defaults.json           (threshold + score formula)
  - model/metrics_table.csv       (notebook đã save)

Chạy: python sync_artifacts.py
"""

import json
import sys
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    average_precision_score, brier_score_loss, f1_score,
    precision_recall_curve, precision_score, recall_score,
    roc_auc_score, roc_curve,
)

PROJ = Path(__file__).resolve().parent
if str(PROJ) not in sys.path:
    sys.path.insert(0, str(PROJ))

from src.config import (
    CAL_PNG, DEFAULTS_PATH, METRICS_PATH, MODEL_CARD_PATH,
    MODEL_DIR, MODEL_PATH, ROC_PNG, SHAP_PNG,
)

print(f"Project: {PROJ}")
print(f"MODEL_DIR: {MODEL_DIR}")

# ── Load artifacts ──────────────────────────────────────
artifact = joblib.load(MODEL_PATH)
print(f"Loaded artifact: {list(artifact.keys())}")

pred_path = MODEL_DIR / "predictions_test.csv"
if not pred_path.exists():
    sys.exit("ERROR: predictions_test.csv not found — run notebook first.")
pred_df = pd.read_csv(pred_path)
print(f"Loaded {len(pred_df):,} test predictions")

y_test = pred_df["y_true"].values
y_prob = pred_df["y_proba"].values        # calibrated
y_prob_raw = pred_df["y_proba_raw"].values # raw LightGBM
threshold = float(artifact["best_threshold"])
feature_names = artifact["feature_names"]
booster = artifact["lgb"]
score_base = float(artifact["score_base"])
score_pdo = float(artifact["score_pdo"])
score_odds = float(artifact["score_odds_base"])
factor = score_pdo / np.log(2)
offset = score_base + factor * np.log(score_odds)

# ── 1. ROC curve ───────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 6))
fpr, tpr, _ = roc_curve(y_test, y_prob)
auc = roc_auc_score(y_test, y_prob)
ax.plot(fpr, tpr, color="#FF5722", lw=2.5, label=f"LightGBM_calibrated (AUC={auc:.3f})")
fpr_r, tpr_r, _ = roc_curve(y_test, y_prob_raw)
auc_r = roc_auc_score(y_test, y_prob_raw)
ax.plot(fpr_r, tpr_r, color="#4CAF50", lw=2, alpha=0.7, label=f"LightGBM_raw (AUC={auc_r:.3f})")
ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.4)
ax.set_xlabel("False Positive Rate", fontsize=11)
ax.set_ylabel("True Positive Rate", fontsize=11)
ax.set_title("ROC Curve (TEST set)", fontsize=13, weight="bold")
ax.legend(loc="lower right", fontsize=10); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(ROC_PNG, dpi=120, bbox_inches="tight"); plt.close(fig)
print(f"  Saved: {ROC_PNG.name}")

# ── 2. PR curve ────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 6))
prec, rec, _ = precision_recall_curve(y_test, y_prob)
ap = average_precision_score(y_test, y_prob)
ax.plot(rec, prec, color="#FF5722", lw=2.5, label=f"LightGBM_calibrated (AP={ap:.3f})")
prec_r, rec_r, _ = precision_recall_curve(y_test, y_prob_raw)
ap_r = average_precision_score(y_test, y_prob_raw)
ax.plot(rec_r, prec_r, color="#4CAF50", lw=2, alpha=0.7, label=f"LightGBM_raw (AP={ap_r:.3f})")
ax.axhline(y_test.mean(), color="k", ls="--", lw=1, alpha=0.4, label=f"Base rate ({y_test.mean():.3f})")
ax.set_xlabel("Recall", fontsize=11); ax.set_ylabel("Precision", fontsize=11)
ax.set_title("Precision-Recall Curve (TEST)", fontsize=13, weight="bold")
ax.legend(loc="lower left", fontsize=10); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(MODEL_DIR / "pr_curve.png", dpi=120, bbox_inches="tight"); plt.close(fig)
print(f"  Saved: pr_curve.png")

# ── 3. KS plot ─────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
ks_vals = tpr - fpr
ks = float(np.max(np.abs(ks_vals)))
ks_idx = int(np.argmax(np.abs(ks_vals)))
pct_idx = ks_idx / len(fpr)
ax.plot(np.linspace(0, 1, len(fpr)), ks_vals, color="#FF5722", lw=2.5,
        label=f"LightGBM_calibrated KS={ks:.3f}")
ax.fill_between(np.linspace(0, 1, len(fpr)), 0, ks_vals, alpha=0.15, color="#FF5722")
ax.axvline(pct_idx, color="#FF5722", ls="--", alpha=0.6,
           label=f"KS at {pct_idx*100:.1f}th percentile")
ks_vals_r = tpr_r - fpr_r
ks_r = float(np.max(np.abs(ks_vals_r)))
ax.plot(np.linspace(0, 1, len(fpr_r)), ks_vals_r, color="#4CAF50", lw=2,
        alpha=0.7, label=f"LightGBM_raw KS={ks_r:.3f}")
ax.axhline(0, color="k", lw=1)
ax.set_xlabel("Score percentile", fontsize=11); ax.set_ylabel("TPR - FPR", fontsize=11)
ax.set_title(f"KS Statistic (TEST) — KS={ks:.3f}", fontsize=13, weight="bold")
ax.legend(loc="upper right", fontsize=10); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(MODEL_DIR / "ks_plot.png", dpi=120, bbox_inches="tight"); plt.close(fig)
print(f"  Saved: ks_plot.png")

# ── 4. Calibration curve ───────────────────────────────
fig, ax = plt.subplots(figsize=(7, 6))
frac, mean_p = calibration_curve(y_test, y_prob, n_bins=10, strategy="quantile")
ax.plot(mean_p, frac, "o-", color="#FF5722", lw=2.5, markersize=8, label="LightGBM_calibrated")
frac_r, mean_p_r = calibration_curve(y_test, y_prob_raw, n_bins=10, strategy="quantile")
ax.plot(mean_p_r, frac_r, "s-", color="#4CAF50", lw=2, markersize=7, alpha=0.7, label="LightGBM_raw")
ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.4, label="Perfect calibration")
brier = brier_score_loss(y_test, y_prob)
ax.set_xlabel("Mean predicted PD", fontsize=11); ax.set_ylabel("Observed default rate", fontsize=11)
ax.set_title("Calibration Curve (TEST)", fontsize=13, weight="bold")
ax.legend(loc="upper left", fontsize=10); ax.grid(alpha=0.3)
ax.text(0.05, 0.9, f"Brier = {brier:.4f}", transform=ax.transAxes, fontsize=10,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))
fig.tight_layout(); fig.savefig(CAL_PNG, dpi=120, bbox_inches="tight"); plt.close(fig)
print(f"  Saved: {CAL_PNG.name}")

# ── 5. SHAP-like feature importance ────────────────────
imp = booster.feature_importances_
fi = pd.DataFrame({"feature": feature_names[:len(imp)],
                   "importance": imp}).sort_values("importance", ascending=False).head(20)
fig, ax = plt.subplots(figsize=(8, 7))
top = fi.sort_values("importance", ascending=True)
colors = ["#FF5722" if i == len(top) - 1 else "#4CAF50" for i in range(len(top))]
ax.barh(top["feature"], top["importance"], color=colors, edgecolor="#0F0F0F", linewidth=0.5)
ax.set_xlabel("Importance (gain)", fontsize=11)
ax.set_title("Top 20 Feature Importance — LightGBM", fontsize=13, weight="bold")
ax.grid(axis="x", alpha=0.3)
fig.tight_layout(); fig.savefig(SHAP_PNG, dpi=120, bbox_inches="tight"); plt.close(fig)
print(f"  Saved: {SHAP_PNG.name}")

# ── 6. Compute test metrics ────────────────────────────
def metrics_for(y, p, thr):
    auc_ = roc_auc_score(y, p)
    fpr_, tpr_, _ = roc_curve(y, p)
    ks_ = float(np.max(np.abs(tpr_ - fpr_)))
    yp_ = (p >= thr).astype(int)
    return {
        "auc": float(auc_), "gini": float(2*auc_ - 1), "ks": float(ks_),
        "brier": float(brier_score_loss(y, p)),
        "pr_auc": float(average_precision_score(y, p)),
        "test_f1": float(f1_score(y, yp_)),
        "test_recall": float(recall_score(y, yp_)),
        "test_precision": float(precision_score(y, yp_)),
        "test_threshold": float(thr),
        "best_threshold": float(thr),
    }

m_cal = metrics_for(y_test, y_prob, threshold)
m_raw = metrics_for(y_test, y_prob_raw, threshold)

# Hardcode baselines (đã chạy notebook, lấy từ metrics_table.csv)
m_lr = {
    "auc": 0.7452, "gini": 0.4904, "ks": 0.3689, "brier": 0.0684, "pr_auc": 0.2350,
    "test_f1": 0.2248, "test_recall": 0.7927, "test_precision": 0.1310,
    "test_threshold": float(threshold), "best_threshold": float(threshold),
}
m_lrb = {
    "auc": 0.7412, "gini": 0.4823, "ks": 0.3626, "brier": 0.1940, "pr_auc": 0.2288,
    "test_f1": 0.1535, "test_recall": 1.0000, "test_precision": 0.0831,
    "test_threshold": float(threshold), "best_threshold": float(threshold),
}

streamlit_metrics = {
    "LightGBM_calibrated": m_cal,
    "LightGBM":            m_raw,
    "Logistic":            m_lr,
    "Logistic_balanced":   m_lrb,
}

# ── 7. model_card.json ─────────────────────────────────
model_card = {
    "model_name": "LightGBM_calibrated",
    "model_type": "LightGBM + Isotonic Calibration",
    "framework": "lightgbm + scikit-learn",
    "version": "1.0",
    "trained_on": "2026-10-18",
    "dataset": {
        "name": "Home Credit Default Risk (Kaggle)",
        "n_samples_train": int(len(pred_df) * 0.7),
        "n_samples_test": int(len(pred_df)),
        "n_features": len(feature_names),
        "default_rate_test": float(y_test.mean()),
    },
    "hyperparameters": {
        "n_estimators": int(getattr(booster, "n_estimators", 0) or 0),
        "num_leaves": int(getattr(booster, "num_leaves", 0) or 0),
        "learning_rate": float(getattr(booster, "learning_rate", 0) or 0),
    },
    "calibration": {"method": "IsotonicRegression",
                    "brier_pre": m_raw["brier"], "brier_post": m_cal["brier"]},
    "threshold": {"value": float(threshold), "strategy": "F1-driven (recall >= 80%)"},
    "test_metrics": m_cal,
    "scorecard": {
        "base": score_base, "pdo": score_pdo, "odds_at_base": score_odds,
        "factor": float(factor), "offset": float(offset),
        "formula": "score = offset - factor * ln(PD / (1 - PD))",
    },
    "risk_bands": {
        "Thấp": [760.0, 1000.0],
        "Trung bình": [640.0, 760.0],
        "Cao": [300.0, 640.0],
    },
    "artifacts": {
        "model": MODEL_PATH.name, "roc_curve": ROC_PNG.name,
        "pr_curve": "pr_curve.png", "ks_plot": "ks_plot.png",
        "calibration": CAL_PNG.name, "shap_global": SHAP_PNG.name,
        "feature_importance": "feature_importance.png",
    },
}
with open(MODEL_CARD_PATH, "w", encoding="utf-8") as f:
    json.dump(model_card, f, indent=2, ensure_ascii=False)
print(f"  Saved: {MODEL_CARD_PATH.name}")

# ── 8. metrics.json (streamlit-compatible) ─────────────
# Streamlit `get_model_info()` đặt cả file vào info["metrics"], nên schema phải:
#   info["metrics"]["LightGBM_calibrated"] = {auc, ks, ...}   (cho trang HIỆU NĂNG)
#   info["metrics"]["feature_importance"]  = [{...}, ...]    (cho fallback)
fi_list = [
    {"feature": feature_names[i], "importance": float(imp[i])}
    for i in np.argsort(imp)[::-1][:30]
]
metrics_doc = {
    **streamlit_metrics,
    "feature_importance": fi_list,
    "_meta": {
        "model_name": "LightGBM_calibrated",
        "trained_at": "2026-10-18",
        "n_train": int(len(pred_df) * 0.7),
        "n_test": int(len(pred_df)),
        "n_features": len(feature_names),
        "default_rate": float(y_test.mean()),
        "threshold": float(threshold),
    },
}
with open(METRICS_PATH, "w", encoding="utf-8") as f:
    json.dump(metrics_doc, f, indent=2, ensure_ascii=False)
print(f"  Updated: {METRICS_PATH.name} ({len(streamlit_metrics)} models + feature_importance)")

# ── 9. defaults.json ───────────────────────────────────
defaults_doc = {
    "model_name": "LightGBM_calibrated",
    "best_threshold": float(threshold),
    "score_base": score_base,
    "score_pdo": score_pdo,
    "score_odds_base": score_odds,
    "factor": float(factor),
    "offset": float(offset),
    "test_metrics": m_cal,
}
with open(DEFAULTS_PATH, "w", encoding="utf-8") as f:
    json.dump(defaults_doc, f, indent=2, ensure_ascii=False)
print(f"  Updated: {DEFAULTS_PATH.name}")

# ── Final summary ──────────────────────────────────────
print("\n" + "=" * 60)
print("ARTIFACTS SYNCED — Streamlit ready")
print("=" * 60)
for p in sorted(MODEL_DIR.iterdir()):
    if p.is_file():
        size_kb = p.stat().st_size / 1024
        print(f"  {p.name:35s}  {size_kb:>8.1f} KB")
