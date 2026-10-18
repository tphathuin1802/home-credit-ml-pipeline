"""Evaluation utilities for binary credit risk models.

Tất cả hàm thuần, không phụ thuộc Streamlit. Được dùng trong ``train.py`` và
khi load lại model trong app (Tab "Về mô hình").

Tài chính / Math:
- ``auc`` = xác suất mô hình xếp 1 khách vỡ nợ cao hơn 1 khách không vỡ nợ.
  AUC = 0.5 là random, 1.0 là hoàn hảo.
- ``gini = 2 * auc - 1`` — ngân hàng thường báo Gini vì dễ đọc.
- ``ks`` = max |F_0(PD) - F_1(PD)| — khoảng cách lớn nhất giữa CDF
  của hai lớp. KS > 0.3 thường được coi là "có sức phân tách" trong credit.
- ``brier`` = MSE giữa PD dự đoán và nhãn thật. Baseline (luôn đoán tỉ lệ
  trung bình) Brier ≈ p(1-p). Với default rate ~8%, baseline ≈ 0.0742.
- ``expected_calibration_error`` = trung bình |tỉ lệ thật - PD dự đoán| theo
  bin. < 0.02 là rất tốt, 0.02-0.05 chấp nhận được, > 0.05 cần calibrate.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Container
# ----------------------------------------------------------------------
@dataclass
class MetricSet:
    """Tập metric cho 1 mô hình trên 1 tập (valid/test)."""

    auc: float
    gini: float
    ks: float
    brier: float
    pr_auc: float
    ece: float
    base_rate: float

    def to_dict(self) -> dict[str, float]:
        return {
            "auc": float(self.auc),
            "gini": float(self.gini),
            "ks": float(self.ks),
            "brier": float(self.brier),
            "pr_auc": float(self.pr_auc),
            "ece": float(self.ece),
            "base_rate": float(self.base_rate),
        }


# ----------------------------------------------------------------------
# Core metrics
# ----------------------------------------------------------------------
def compute_gini(y_true: np.ndarray, y_score: np.ndarray) -> float:
    return float(2 * roc_auc_score(y_true, y_score) - 1)


def compute_ks(y_true: np.ndarray, y_score: np.ndarray) -> float:
    fpr, tpr, _ = roc_curve(y_true, y_score)
    return float(np.max(np.abs(tpr - fpr)))


def expected_calibration_error(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
) -> float:
    """ECE trung bình trọng số theo số mẫu mỗi bin."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.digitize(y_prob, bins) - 1
    idx = np.clip(idx, 0, n_bins - 1)
    ece = 0.0
    for b in range(n_bins):
        mask = idx == b
        if not mask.any():
            continue
        acc = y_true[mask].mean()
        conf = y_prob[mask].mean()
        ece += (mask.sum() / len(y_true)) * abs(acc - conf)
    return float(ece)


def all_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> MetricSet:
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob).astype(float)
    return MetricSet(
        auc=float(roc_auc_score(y_true, y_prob)),
        gini=compute_gini(y_true, y_prob),
        ks=compute_ks(y_true, y_prob),
        brier=float(brier_score_loss(y_true, y_prob)),
        pr_auc=float(average_precision_score(y_true, y_prob)),
        ece=expected_calibration_error(y_true, y_prob),
        base_rate=float(y_true.mean()),
    )


# ----------------------------------------------------------------------
# Plots
# ----------------------------------------------------------------------
def plot_roc(
    y_true: np.ndarray,
    y_scores: dict[str, np.ndarray],
    out_path: Path,
) -> None:
    """Vẽ ROC cho nhiều model trên cùng một tập ``y_true``.

    Parameters
    ----------
    y_true : array
        Nhãn thật (chung cho tất cả model).
    y_scores : dict[model_name -> y_score]
        Điểm/prob từ từng model.
    """
    plt.figure(figsize=(7, 6))
    for name, y_score in y_scores.items():
        fpr, tpr, _ = roc_curve(y_true, y_score)
        auc = roc_auc_score(y_true, y_score)
        plt.plot(fpr, tpr, label=f"{name} (AUC={auc:.3f})", linewidth=2)
    plt.plot([0, 1], [0, 1], "k--", alpha=0.4, label="Random")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve — Credit Default Risk")
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=120)
    plt.close()
    logger.info("Saved ROC -> %s", out_path)


def plot_calibration(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    out_path: Path,
    n_bins: int = 10,
    name: str = "model",
) -> None:
    plt.figure(figsize=(7, 6))
    frac_pos, mean_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="quantile")
    plt.plot([0, 1], [0, 1], "k--", alpha=0.4, label="Perfect calibration")
    plt.plot(mean_pred, frac_pos, "o-", linewidth=2, label=name)
    plt.xlabel("Predicted PD (mean per bin)")
    plt.ylabel("Observed default rate")
    plt.title(f"Calibration — {name}")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=120)
    plt.close()
    logger.info("Saved calibration -> %s", out_path)


def plot_pr(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    out_path: Path,
    name: str = "model",
) -> None:
    prec, rec, _ = precision_recall_curve(y_true, y_prob)
    ap = average_precision_score(y_true, y_prob)
    plt.figure(figsize=(7, 6))
    plt.plot(rec, prec, linewidth=2, label=f"{name} (AP={ap:.3f})")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title(f"Precision-Recall — {name}")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=120)
    plt.close()
    logger.info("Saved PR -> %s", out_path)


def plot_ks(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    out_path: Path,
    name: str = "model",
) -> None:
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    ks = float(np.max(np.abs(tpr - fpr)))
    plt.figure(figsize=(7, 6))
    plt.plot(np.sort(fpr), np.linspace(0, 1, len(fpr)), label="Cumulative FPR", alpha=0.6)
    plt.plot(np.sort(tpr), np.linspace(0, 1, len(tpr)), label="Cumulative TPR", alpha=0.6)
    ks_idx = int(np.argmax(np.abs(tpr - fpr)))
    plt.scatter([fpr[ks_idx]], [tpr[ks_idx]], s=80, c="red", label=f"KS={ks:.3f}")
    plt.xlabel("Score percentile")
    plt.ylabel("Cumulative")
    plt.title(f"KS plot — {name}")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=120)
    plt.close()
    logger.info("Saved KS -> %s", out_path)


# ----------------------------------------------------------------------
# Comparison table
# ----------------------------------------------------------------------
def comparison_table(
    metrics_by_model: dict[str, dict[str, float]],
) -> pd.DataFrame:
    """Trả DataFrame so sánh nhiều model trên nhiều metric.

    Parameters
    ----------
    metrics_by_model : dict[model_name -> dict[metric_name -> value]]
    """
    rows = []
    for model_name, m in metrics_by_model.items():
        rows.append({"model": model_name, **m})
    return pd.DataFrame(rows).set_index("model")


__all__ = [
    "MetricSet",
    "compute_gini",
    "compute_ks",
    "expected_calibration_error",
    "all_metrics",
    "plot_roc",
    "plot_calibration",
    "plot_pr",
    "plot_ks",
    "comparison_table",
]
