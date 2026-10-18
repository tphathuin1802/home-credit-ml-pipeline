"""Central configuration for the credit default risk project.

Tài chính/Math:
- ``TARGET = 1`` ứng với khách vỡ nợ; tỉ lệ dương ~8% là bài toán mất cân bằng
  (imbalanced classification). Baseline "luôn đoán 0" đã đúng 92%, nên
  Accuracy là metric vô nghĩa - ta sẽ dùng AUC, Gini, KS.
- ``random_state`` cố định + stratify theo TARGET đảm bảo phân chia
  train/valid/test tái lập được (reproducibility), điều kiện tiên quyết
  để so sánh mô hình có ý nghĩa.
"""

from __future__ import annotations

from pathlib import Path

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
# Thư mục gốc dự án = thư mục cha của ``src/``.
PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]

DATA_RAW: Path = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED: Path = PROJECT_ROOT / "data" / "processed"
MODEL_DIR: Path = PROJECT_ROOT / "model"
NOTEBOOK_DIR: Path = PROJECT_ROOT / "notebooks"

# Tạo thư mục nếu chưa tồn tại (idempotent).
for _p in (DATA_RAW, DATA_PROCESSED, MODEL_DIR, NOTEBOOK_DIR):
    _p.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Dataset files (Kaggle "Home Credit Default Risk")
# ----------------------------------------------------------------------
APP_TRAIN_CSV: Path = DATA_RAW / "application_train.csv"
APP_TEST_CSV: Path = DATA_RAW / "application_test.csv"
BUREAU_CSV: Path = DATA_RAW / "bureau.csv"
BUREAU_BALANCE_CSV: Path = DATA_RAW / "bureau_balance.csv"
PREV_APP_CSV: Path = DATA_RAW / "previous_application.csv"
POS_CASH_BALANCE_CSV: Path = DATA_RAW / "POS_CASH_balance.csv"
INSTALLMENTS_CSV: Path = DATA_RAW / "installments_payments.csv"
CREDIT_CARD_CSV: Path = DATA_RAW / "credit_card_balance.csv"
COLUMNS_DESC_CSV: Path = DATA_RAW / "HomeCredit_columns_description.csv"

# ----------------------------------------------------------------------
# Reproducibility
# ----------------------------------------------------------------------
RANDOM_STATE: int = 42

# ----------------------------------------------------------------------
# Sampling for development
# ----------------------------------------------------------------------
# Khi phát triển có thể lấy mẫu để chạy nhanh. Đặt ``None`` để dùng toàn bộ
# dữ liệu (cần > 8GB RAM khả dụng).
SAMPLE_ROWS: int | None = 50_000

# ----------------------------------------------------------------------
# Train / Valid / Test split (stratified by TARGET)
# ----------------------------------------------------------------------
# 70 / 15 / 15 - đủ valid để early-stop và calibrate, đủ test để báo cáo.
TEST_SIZE: float = 0.15
VALID_SIZE: float = 0.15  # tính trên phần còn lại sau test

# ----------------------------------------------------------------------
# Model artifacts
# ----------------------------------------------------------------------
MODEL_PATH: Path = MODEL_DIR / "model.joblib"
METRICS_PATH: Path = MODEL_DIR / "metrics.json"
DEFAULTS_PATH: Path = MODEL_DIR / "defaults.json"
ROC_PNG: Path = MODEL_DIR / "roc_curve.png"
CAL_PNG: Path = MODEL_DIR / "calibration_curve.png"
SHAP_PNG: Path = MODEL_DIR / "shap_global.png"
MODEL_CARD_PATH: Path = MODEL_DIR / "model_card.json"

# ----------------------------------------------------------------------
# Scorecard (PD -> score)
# ----------------------------------------------------------------------
# Côngng thức: score = offset - factor * log(odds), với odds = PD / (1 - PD).
# Base score 600, PDO (points to double the odds) = 20, odds 50:1.
#   factor = PDO / ln(2)
#   offset = base_score + factor * ln(50)
# Trong thẻ điểm FICO phổ biến 300-850, thang 600-1000+ cho retail.
SCORE_BASE: float = 600.0
SCORE_PDO: float = 20.0
SCORE_ODDS_BASE: float = 50.0  # odds ở base_score

# Ngưỡng phân nhóm rủi ro (cập nhật sau khi nhìn phân phối score trên test).
RISK_BANDS: dict[str, tuple[float, float]] = {
    "Thấp": (760.0, float("inf")),
    "Trung bình": (640.0, 760.0),
    "Cao": (-float("inf"), 640.0),
}

# ----------------------------------------------------------------------
# Feature lists (chỉ chứa tên - định nghĩa chi tiết ở features.py)
# ----------------------------------------------------------------------
# Sẽ populate đầy đủ ở Giai đoạn 2.
TARGET_COL: str = "TARGET"
ID_COL: str = "SK_ID_CURR"

# Application columns đặc biệt cần xử lý (DAYS_EMPLOYED = 365243 là sentinel).
DAYS_EMPLOYED_SENTINEL: int = 365_243

# Bureau aggregation - danh sách cột gốc + hàm aggregate.
BUREAU_NUMERIC_COLS: list[str] = [
    "DAYS_CREDIT",
    "CREDIT_DAY_OVERDUE",
    "DAYS_CREDIT_ENDDATE",
    "DAYS_ENDDATE_FACT",
    "AMT_CREDIT_SUM",
    "AMT_CREDIT_SUM_DEBT",
    "AMT_CREDIT_SUM_LIMIT",
    "AMT_CREDIT_SUM_OVERDUE",
]
BUREAU_CAT_COLS: list[str] = ["CREDIT_ACTIVE", "CREDIT_TYPE"]

__all__ = [
    "PROJECT_ROOT",
    "DATA_RAW",
    "DATA_PROCESSED",
    "MODEL_DIR",
    "NOTEBOOK_DIR",
    "APP_TRAIN_CSV",
    "APP_TEST_CSV",
    "BUREAU_CSV",
    "BUREAU_BALANCE_CSV",
    "PREV_APP_CSV",
    "POS_CASH_BALANCE_CSV",
    "INSTALLMENTS_CSV",
    "CREDIT_CARD_CSV",
    "COLUMNS_DESC_CSV",
    "RANDOM_STATE",
    "SAMPLE_ROWS",
    "TEST_SIZE",
    "VALID_SIZE",
    "MODEL_PATH",
    "METRICS_PATH",
    "DEFAULTS_PATH",
    "ROC_PNG",
    "CAL_PNG",
    "SHAP_PNG",
    "MODEL_CARD_PATH",
    "SCORE_BASE",
    "SCORE_PDO",
    "SCORE_ODDS_BASE",
    "RISK_BANDS",
    "TARGET_COL",
    "ID_COL",
    "DAYS_EMPLOYED_SENTINEL",
    "BUREAU_NUMERIC_COLS",
    "BUREAU_CAT_COLS",
]
