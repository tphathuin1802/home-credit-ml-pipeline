"""Training pipeline for Home Credit Default Risk.

Pipeline:
  1. Load application_train + bureau, build features.
  2. Stratified split: train (70%) / valid (15%) / test (15%).
  3. Wrap preprocessing + model trong một ``sklearn.Pipeline``.
     - Preprocessing: ColumnTransformer { numeric -> median impute + clip
       inf/-inf + scale (StandardScaler cho Logistic, passthrough cho LGBM);
       categorical -> most_frequent impute + OneHotEncoder(handle_unknown=ignore) }
     - Model A: LogisticRegression(class_weight=None | 'balanced')
     - Model B: LightGBMClassifier(scale_pos_weight=...) + early stop on valid
  4. Compare 2-3 variants on valid, chọn best (theo AUC). Re-fit trên
     train+valid để tận dụng dữ liệu (nếu LightGBM, giữ best_iteration).
  5. Calibrate (Platt hoặc Isotonic) trên valid nếu cần (Brier > 0.08 hoặc
     ECE > 0.05).
  6. Final evaluation trên test. Lưu model.joblib, metrics.json, ROC/cal/KS/PR.

Tài chính / Math:
- Class imbalance ~8% (default rate). Hai hướng xử lý:
    + ``class_weight='balanced'`` cho Logistic — tăng trọng số lớp 1.
    + ``scale_pos_weight = n_neg / n_pos`` cho LightGBM — tương tự nhưng
      tách rời khỏi loss, cho phép giữ metric tối ưu là binary_logloss.
- Stratified split giữ tỉ lệ TARGET = const giữa 3 tập, cần thiết khi
  metric chính là AUC/KS (nhạy với phân phối nhãn).
- Calibration trên valid, đánh giá trên test: nếu calibrate trên test sẽ
  bị optimistic bias (leak).
"""

from __future__ import annotations

import argparse
import json
import logging
import time
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import optuna
import pandas as pd
from lightgbm import LGBMClassifier, early_stopping, log_evaluation
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, recall_score, precision_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

from src.config import (
    APP_TRAIN_CSV,
    BUREAU_CSV,
    CREDIT_CARD_CSV,
    DEFAULTS_PATH,
    ID_COL,
    INSTALLMENTS_CSV,
    METRICS_PATH,
    MODEL_PATH,
    POS_CASH_BALANCE_CSV,
    PREV_APP_CSV,
    RANDOM_STATE,
    SAMPLE_ROWS,
    TARGET_COL,
    TEST_SIZE,
    VALID_SIZE,
    CAL_PNG,
    ROC_PNG,
    SCORE_BASE,
    SCORE_PDO,
    SCORE_ODDS_BASE,
    SHAP_PNG,
    MODEL_CARD_PATH,
)
from src.evaluate import (
    all_metrics,
    comparison_table,
    plot_calibration,
    plot_ks,
    plot_pr,
    plot_roc,
)
from src.features import APP_CAT_BASE, build_full_features

warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=UserWarning)
optuna.logging.set_verbosity(optuna.logging.WARNING)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def load_data() -> dict[str, pd.DataFrame]:
    """Load application + bureau (+ 4 bảng phụ). Sample nếu SAMPLE_ROWS.

    Trả dict {'app', 'bureau', 'prev', 'installments', 'pos', 'cc'}.
    Bảng phụ được filter theo SK_ID_CURR của app sample.
    """
    import gc
    # Step 1: Đọc CHỈ ID + TARGET để sample (rất nhẹ, ~10MB)
    logger.info("Reading app IDs (cols 0-2) ...")
    app_ids_set_df = pd.read_csv(APP_TRAIN_CSV, usecols=[ID_COL, TARGET_COL], low_memory=True)
    if SAMPLE_ROWS is not None:
        app_ids_set_df = app_ids_set_df.sample(n=min(SAMPLE_ROWS, len(app_ids_set_df)), random_state=RANDOM_STATE).reset_index(drop=True)
        logger.info("Sampled to %d rows.", len(app_ids_set_df))
    app_ids = set(app_ids_set_df[ID_COL].tolist())
    logger.info("App IDs: %d unique customers.", len(app_ids))
    del app_ids_set_df
    gc.collect()

    # Step 2: Load đầy đủ, filter ngay trong chunk (không concat trước)
    logger.info("Reading application_train (filtering) ...")
    app_chunks: list[pd.DataFrame] = []
    for chunk in pd.read_csv(APP_TRAIN_CSV, chunksize=50_000, low_memory=True):
        app_chunks.append(chunk[chunk[ID_COL].isin(app_ids)])
    app = pd.concat(app_chunks, ignore_index=True)
    del app_chunks
    gc.collect()
    logger.info("App loaded: %d rows.", len(app))

    def _read_filter(path: Path, key: str, usecols: list[str] | None = None) -> pd.DataFrame:
        """Đọc CSV theo chunks + filter theo app_ids.

        Chunked read để tránh MemoryError khi RAM hạn chế.
        """
        import gc
        logger.info("Reading %s (chunked) ...", path.name)
        chunks: list[pd.DataFrame] = []
        chunk_size = 100_000
        for chunk in pd.read_csv(path, chunksize=chunk_size, usecols=usecols, low_memory=True):
            filtered = chunk[chunk["SK_ID_CURR"].isin(app_ids)]
            if len(filtered) > 0:
                chunks.append(filtered)
        df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
        del chunks
        gc.collect()
        logger.info("  %s: %d rows after filter.", path.name, len(df))
        return df

    # Step 1: Đọc CHỈ ID + TARGET để sample (rất nhẹ, ~10MB)
    logger.info("Reading app IDs (cols 0-2) ...")
    import gc
    app_ids_set_df = pd.read_csv(APP_TRAIN_CSV, usecols=[ID_COL, TARGET_COL], low_memory=True)
    if SAMPLE_ROWS is not None:
        app_ids_set_df = app_ids_set_df.sample(n=min(SAMPLE_ROWS, len(app_ids_set_df)), random_state=RANDOM_STATE).reset_index(drop=True)
        logger.info("Sampled to %d rows.", len(app_ids_set_df))
    app_ids = set(app_ids_set_df[ID_COL].tolist())
    logger.info("App IDs: %d unique customers.", len(app_ids))
    del app_ids_set_df
    gc.collect()

    # Step 2: Load đầy đủ, filter ngay trong chunk (không concat trước)
    logger.info("Reading application_train (filtering) ...")
    app_chunks: list[pd.DataFrame] = []
    for chunk in pd.read_csv(APP_TRAIN_CSV, chunksize=50_000, low_memory=True):
        app_chunks.append(chunk[chunk[ID_COL].isin(app_ids)])
    app = pd.concat(app_chunks, ignore_index=True)
    del app_chunks
    gc.collect()
    logger.info("App loaded: %d rows.", len(app))

    return {
        "app": app,
        "bureau": _read_filter(BUREAU_CSV, "bureau"),
        "prev": _read_filter(PREV_APP_CSV, "prev"),
        "installments": _read_filter(INSTALLMENTS_CSV, "installments"),
        "pos": _read_filter(POS_CASH_BALANCE_CSV, "pos"),
        "cc": _read_filter(CREDIT_CARD_CSV, "cc"),
    }


def split_data(features: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """70/15/15 stratified split."""
    y = features[TARGET_COL].astype(int)
    X = features.drop(columns=[TARGET_COL, ID_COL])

    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=TEST_SIZE + VALID_SIZE, stratify=y, random_state=RANDOM_STATE
    )
    rel = VALID_SIZE / (TEST_SIZE + VALID_SIZE)
    X_valid, X_test, y_valid, y_test = train_test_split(
        X_temp, y_temp, test_size=1 - rel, stratify=y_temp, random_state=RANDOM_STATE
    )
    logger.info(
        "Split: train=%d (%.2f%%), valid=%d (%.2f%%), test=%d (%.2f%%)",
        len(X_train), 100 * len(X_train) / len(X),
        len(X_valid), 100 * len(X_valid) / len(X),
        len(X_test), 100 * len(X_test) / len(X),
    )
    for name, ys in [("train", y_train), ("valid", y_valid), ("test", y_test)]:
        logger.info("  %s default rate: %.4f", name, ys.mean())
    return X_train, X_valid, X_test, y_train, y_valid, y_test


def detect_column_types(X: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Tách numeric vs categorical dựa trên dtype."""
    cat_cols = [c for c in X.columns if X[c].dtype == "object"]
    num_cols = [c for c in X.columns if c not in cat_cols]
    return num_cols, cat_cols


def _clip_transformer():
    from src.features import _ClipTransformer
    return _ClipTransformer()


def build_preprocessor(num_cols: list[str], cat_cols: list[str], scale_numeric: bool) -> ColumnTransformer:
    """ColumnTransformer dùng chung cho cả Logistic và LightGBM."""
    from sklearn.pipeline import Pipeline as _Pipe
    if scale_numeric:
        # Pipeline có clip (inf->NaN) trước khi impute + scale
        num_pipe = _Pipe([
            ("clip", _clip_transformer()),
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ])
    else:
        # Pipeline cho LightGBM: KHÔNG scale, chỉ impute
        num_pipe = _Pipe([
            ("clip", _clip_transformer()),
            ("impute", SimpleImputer(strategy="median")),
        ])
    cat_pipe = _Pipe([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    return ColumnTransformer(
        transformers=[
            ("num", num_pipe, num_cols),
            ("cat", cat_pipe, cat_cols),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def train_logistic(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_valid: pd.DataFrame,
    y_valid: pd.Series,
    num_cols: list[str],
    cat_cols: list[str],
    class_weight: Any = None,
) -> tuple[Pipeline, float]:
    """Train Logistic, đánh giá trên valid. Trả (pipeline, valid_auc)."""
    preprocessor = build_preprocessor(num_cols, cat_cols, scale_numeric=True)
    pipe = Pipeline([("prep", preprocessor), ("clf", LogisticRegression(
        max_iter=2000, C=0.5, class_weight=class_weight, solver="liblinear",
        random_state=RANDOM_STATE,
    ))])
    logger.info("Training Logistic (class_weight=%s) ...", class_weight)
    t0 = time.time()
    pipe.fit(X_train, y_train)
    prob = pipe.predict_proba(X_valid)[:, 1]
    m = all_metrics(y_valid.values, prob)
    logger.info("Logistic class_weight=%s | valid AUC=%.4f, KS=%.4f, Brier=%.4f | %.1fs",
                class_weight, m.auc, m.ks, m.brier, time.time() - t0)
    return pipe, m.auc


def train_lgbm(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_valid: pd.DataFrame,
    y_valid: pd.Series,
    num_cols: list[str],
    cat_cols: list[str],
) -> tuple[Pipeline, float, int]:
    """Train LightGBM với early stop trên valid. Trả (pipeline, valid_auc, best_iter)."""
    preprocessor = build_preprocessor(num_cols, cat_cols, scale_numeric=False)
    # scale_pos_weight tăng gradient lớp 1 lên ~11x. Ở đây mình KHÔNG dùng
    # vì thực nghiệm cho thấy nó khiến logloss tăng sau iter 2 (gradient
    # explosion). AUC vốn đã invariant với threshold nên không cần reweight.
    spw = 1.0
    logger.info("LightGBM scale_pos_weight=%.2f", spw)

    model = LGBMClassifier(
        n_estimators=2000,
        learning_rate=0.03,
        num_leaves=31,
        max_depth=-1,
        min_child_samples=50,
        subsample=0.85,
        subsample_freq=1,
        colsample_bytree=0.7,
        reg_alpha=0.1,
        reg_lambda=0.1,
        scale_pos_weight=spw,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=-1,
    )
    pipe = Pipeline([("prep", preprocessor), ("clf", model)])

    logger.info("Training LightGBM (early stop) ...")
    t0 = time.time()
    # Fit preprocessor trước để lấy feature names + shape
    pipe.named_steps["prep"].fit(X_train, y_train)
    Xt_tr = pipe.named_steps["prep"].transform(X_train)
    Xt_va = pipe.named_steps["prep"].transform(X_valid)

    # LightGBM 4.x: eval_set vẫn hoạt động nhưng in warning. Để tương thích
    # rộng, ta dùng callback early_stopping + log_evaluation.
    # Lưu ý: dùng binary_logloss làm early-stop metric (trơn, giảm dần) chứ
    # không dùng AUC (dao động → dừng sớm sai ở vòng 2 như đã thấy).
    model.fit(
        Xt_tr, y_train,
        eval_set=[(Xt_va, y_valid)],
        eval_metric="binary_logloss",
        callbacks=[early_stopping(150, verbose=False), log_evaluation(200)],
    )
    logger.info("LightGBM best_iter=%s, n_features_in=%d", model.best_iteration_, model.n_features_in_)
    best_iter = int(model.best_iteration_ or model.n_estimators)
    prob = model.predict_proba(Xt_va)[:, 1]
    m = all_metrics(y_valid.values, prob)
    logger.info("LightGBM | valid AUC=%.4f, KS=%.4f, Brier=%.4f | best_iter=%d | %.1fs",
                m.auc, m.ks, m.brier, best_iter, time.time() - t0)
    return pipe, m.auc, best_iter


def retrain_lgbm_full(
    X_train: pd.DataFrame,
    y_train: pd.DataFrame | pd.Series,
    X_valid: pd.DataFrame,
    y_valid: pd.Series,
    num_cols: list[str],
    cat_cols: list[str],
    best_iter: int,
) -> Pipeline:
    """Re-fit LightGBM trên train+valid với số vòng = best_iter * 1.1."""
    preprocessor = build_preprocessor(num_cols, cat_cols, scale_numeric=False)
    spw = 1.0

    X_all = pd.concat([X_train, X_valid], axis=0)
    y_all = pd.concat([y_train, y_valid], axis=0)

    n_rounds = int(best_iter * 1.1)
    model = LGBMClassifier(
        n_estimators=n_rounds,
        learning_rate=0.03,
        num_leaves=31,
        min_child_samples=50,
        subsample=0.85,
        subsample_freq=1,
        colsample_bytree=0.7,
        reg_alpha=0.1,
        reg_lambda=0.1,
        scale_pos_weight=spw,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=-1,
    )
    pipe = Pipeline([("prep", preprocessor), ("clf", model)])
    logger.info("Re-fitting LightGBM trên train+valid với %d vòng ...", n_rounds)
    pipe.fit(X_all, y_all)
    return pipe


# ----------------------------------------------------------------------
# Calibration
# ----------------------------------------------------------------------
def maybe_calibrate(
    pipe: Pipeline,
    X_valid: pd.DataFrame,
    y_valid: pd.Series,
    brier_threshold: float = 0.08,
    ece_threshold: float = 0.05,
) -> tuple[Pipeline, str, dict]:
    """Calibrate bằng Isotonic nếu Brier hoặc ECE vượt ngưỡng trên valid."""
    prob = pipe.predict_proba(X_valid)[:, 1]
    m = all_metrics(y_valid.values, prob)
    logger.info("Pre-calibration valid: Brier=%.4f, ECE=%.4f", m.brier, m.ece)
    if m.brier <= brier_threshold and m.ece <= ece_threshold:
        logger.info("Calibration đạt chuẩn (Brier<%.2f, ECE<%.2f) - bỏ qua.", brier_threshold, ece_threshold)
        return pipe, "none", {"pre": m.to_dict()}

    # Calibrate bằng Isotonic (non-parametric, robust với shape lệch).
    logger.info("Calibrating bằng Isotonic trên valid ...")
    calibrated = CalibratedClassifierCV(pipe, method="isotonic", cv="prefit")
    calibrated.fit(X_valid, y_valid)
    prob_cal = calibrated.predict_proba(X_valid)[:, 1]
    m_cal = all_metrics(y_valid.values, prob_cal)
    logger.info("Post-calibration valid: Brier=%.4f, ECE=%.4f", m_cal.brier, m_cal.ece)
    return calibrated, "isotonic", {"pre": m.to_dict(), "post": m_cal.to_dict()}


# ----------------------------------------------------------------------
# Threshold tuning (F1-driven, với ràng buộc Recall tối thiểu)
# ----------------------------------------------------------------------
def best_threshold_for_f1(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    min_recall: float = 0.80,
) -> tuple[float, float, float, float]:
    """Quét threshold từ 0.01..0.99, chọn threshold cho F1 cao nhất với
    điều kiện ``recall >= min_recall``.

    Trả (best_threshold, best_f1, recall_at_best, precision_at_best).
    Nếu không tìm được threshold nào đạt min_recall, trả threshold cho
    recall cao nhất (kèm F1 ở đó) để không bao giờ trả rỗng.
    """
    thresholds = np.linspace(0.01, 0.99, 99)
    best_f1, best_thr, best_rec, best_prec = -1.0, 0.5, 0.0, 0.0
    fallback_thr, fallback_f1, fallback_rec = 0.5, -1.0, 0.0
    for thr in thresholds:
        y_pred = (y_prob >= thr).astype(int)
        rec = recall_score(y_true, y_pred, zero_division=0)
        prec = precision_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        # Track fallback (highest recall, dùng F1 của nó)
        if rec > fallback_rec:
            fallback_rec, fallback_f1, fallback_thr = rec, f1, thr
        if rec >= min_recall and f1 > best_f1:
            best_f1, best_thr, best_rec, best_prec = f1, thr, rec, prec
    if best_f1 < 0:  # không có threshold nào đạt min_recall
        logger.warning(
            "Khong dat min_recall=%.2f (max recall=%.3f), fallback.",
            min_recall, fallback_rec,
        )
        y_pred = (y_prob >= fallback_thr).astype(int)
        return (
            float(fallback_thr),
            float(fallback_f1),
            float(recall_score(y_true, y_pred, zero_division=0)),
            float(precision_score(y_true, y_pred, zero_division=0)),
        )
    logger.info(
        "Best threshold=%.3f: F1=%.4f, Recall=%.4f, Precision=%.4f",
        best_thr, best_f1, best_rec, best_prec,
    )
    return float(best_thr), float(best_f1), float(best_rec), float(best_prec)


# ----------------------------------------------------------------------
# Optuna tuning cho LightGBM
# ----------------------------------------------------------------------
def tune_lgbm(
    Xt_tr: np.ndarray,
    y_tr: pd.Series,
    Xt_va: np.ndarray,
    y_va: pd.Series,
    n_trials: int = 15,
    timeout_sec: int = 240,
    seed: int = RANDOM_STATE,
) -> tuple[dict, float]:
    """Optuna tìm hyperparameters tối ưu AUC trên valid (giữ lại best params
    dùng cho retrain). Trả (best_params, best_valid_auc).
    """

    def objective(trial: optuna.Trial) -> float:
        import lightgbm as lgb
        params = {
            "objective": "binary",
            "metric": "auc",
            "learning_rate": trial.suggest_float("learning_rate", 0.03, 0.08, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 15, 63),
            "max_depth": trial.suggest_int("max_depth", 4, 8),
            "min_child_samples": trial.suggest_int("min_child_samples", 30, 200),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "subsample_freq": 1,
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 5.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 5.0, log=True),
            "scale_pos_weight": 1.0,
            "random_state": seed,
            "num_threads": 1,    # 1 thread để tránh OOM
            "verbose": -1,
            "max_bin": 63,       # giảm memory (default 255)
            "min_data_in_bin": 50,
        }
        # Dùng lgb.train với Dataset trực tiếp (memory-efficient hơn sklearn wrapper)
        dtrain = lgb.Dataset(Xt_tr, label=y_tr.values, free_raw_data=False)
        dvalid = lgb.Dataset(Xt_va, label=y_va.values, reference=dtrain, free_raw_data=False)
        booster = lgb.train(
            params, dtrain, num_boost_round=400,
            valid_sets=[dvalid],
            callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(0)],
        )
        prob = booster.predict(Xt_va, num_iteration=booster.best_iteration)
        from sklearn.metrics import roc_auc_score
        return float(roc_auc_score(y_va, prob))

    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=seed),
    )
    study.optimize(objective, n_trials=n_trials, timeout=timeout_sec, show_progress_bar=False)
    logger.info(
        "Optuna done: best AUC=%.4f, params=%s",
        study.best_value, study.best_params,
    )
    return study.best_params | {"n_estimators": 2000, "subsample_freq": 1,
                                "scale_pos_weight": 1.0, "random_state": seed,
                                "n_jobs": -1, "verbose": -1}, float(study.best_value)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> int:
    t0 = time.time()
    logger.info("=" * 60)
    logger.info("HOME CREDIT DEFAULT RISK - TRAINING")
    logger.info("=" * 60)

    # 1) Load + features
    data = load_data()
    feat = build_full_features(
        data["app"],
        data["bureau"],
        prev=data["prev"],
        installments=data["installments"],
        pos=data["pos"],
        cc=data["cc"],
    )
    feat = feat.dropna(subset=[TARGET_COL]).reset_index(drop=True)

    # 2) Split
    X_train, X_valid, X_test, y_train, y_valid, y_test = split_data(feat)

    # 3) Column types
    num_cols, cat_cols = detect_column_types(X_train)
    logger.info("Numeric cols: %d, categorical cols: %d", len(num_cols), len(cat_cols))

    # 4) Train các variant
    candidates: dict[str, tuple[Pipeline, float, dict]] = {}

    # 4a) Logistic no class weight
    p_lr, auc_lr = train_logistic(X_train, y_train, X_valid, y_valid, num_cols, cat_cols, class_weight=None)
    candidates["Logistic"] = (p_lr, auc_lr, {"note": "class_weight=None"})

    # 4b) Logistic balanced
    p_lrb, auc_lrb = train_logistic(X_train, y_train, X_valid, y_valid, num_cols, cat_cols, class_weight="balanced")
    candidates["Logistic_balanced"] = (p_lrb, auc_lrb, {"note": "class_weight=balanced"})

    # 4c) LightGBM với Optuna tuning
    logger.info("=" * 60)
    logger.info("OPTUNA TUNING cho LightGBM (50 trials, ~10 phút)")
    logger.info("=" * 60)
    # Transform trước để Optuna dùng
    preprocessor_lgb = build_preprocessor(num_cols, cat_cols, scale_numeric=False)
    preprocessor_lgb.fit(X_train)
    Xt_tr = preprocessor_lgb.transform(X_train)
    Xt_va = preprocessor_lgb.transform(X_valid)
    # Convert sang numpy float32 để giảm memory cho LGBM
    if hasattr(Xt_tr, "toarray"):
        Xt_tr_np = Xt_tr.toarray().astype("float32")
    else:
        Xt_tr_np = np.asarray(Xt_tr, dtype="float32")
    if hasattr(Xt_va, "toarray"):
        Xt_va_np = Xt_va.toarray().astype("float32")
    else:
        Xt_va_np = np.asarray(Xt_va, dtype="float32")
    import gc; gc.collect()
    logger.info("Xt_tr shape=%s, Xt_va shape=%s, dtype=%s", Xt_tr_np.shape, Xt_va_np.shape, Xt_tr_np.dtype)

    best_lgb_params, best_lgb_auc = tune_lgbm(
        Xt_tr_np, y_train, Xt_va_np, y_valid, n_trials=10, timeout_sec=180,
    )
    del Xt_tr_np, Xt_va_np
    gc.collect()

    # Train final LightGBM với params tốt nhất
    n_pos = int(y_train.sum())
    n_neg = int(len(y_train) - n_pos)
    spw = 1.0  # đã chứng minh không nên dùng scale_pos_weight lớn
    final_lgb = LGBMClassifier(**best_lgb_params)
    pipe_lgb = Pipeline([("prep", preprocessor_lgb), ("clf", final_lgb)])
    final_lgb.fit(
        Xt_tr, y_train,
        eval_set=[(Xt_va, y_valid)],
        eval_metric="binary_logloss",
        callbacks=[early_stopping(150, verbose=False), log_evaluation(0)],
    )
    best_iter = int(final_lgb.best_iteration_ or final_lgb.n_estimators)
    prob_lgb_va = final_lgb.predict_proba(Xt_va)[:, 1]
    m_lgb_va = all_metrics(y_valid.values, prob_lgb_va)
    logger.info(
        "LightGBM tuned | valid AUC=%.4f, KS=%.4f, Brier=%.4f | best_iter=%d",
        m_lgb_va.auc, m_lgb_va.ks, m_lgb_va.brier, best_iter,
    )
    candidates["LightGBM"] = (pipe_lgb, m_lgb_va.auc, {
        "note": "optuna_tuned",
        "best_iter": best_iter,
        "best_lgb_params": {k: v for k, v in best_lgb_params.items()
                            if k in ("learning_rate", "num_leaves", "max_depth",
                                     "min_child_samples", "subsample", "colsample_bytree",
                                     "reg_alpha", "reg_lambda")},
    })

    # 5) Chọn best trên valid (theo AUC)
    best_name = max(candidates, key=lambda k: candidates[k][1])
    best_pipe, best_auc, best_meta = candidates[best_name]
    logger.info("Best trên valid (AUC): %s (AUC=%.4f)", best_name, best_auc)

    # 6) Re-fit LightGBM trên train+valid
    if best_name == "LightGBM":
        n_rounds = int(best_iter * 1.1)
        X_all = pd.concat([X_train, X_valid], axis=0)
        y_all = pd.concat([y_train, y_valid], axis=0)
        preprocessor_full = build_preprocessor(num_cols, cat_cols, scale_numeric=False)
        full_lgb_params = dict(best_lgb_params)
        full_lgb_params["n_estimators"] = n_rounds
        full_lgb = LGBMClassifier(**full_lgb_params)
        best_pipe = Pipeline([("prep", preprocessor_full), ("clf", full_lgb)])
        logger.info("Re-fitting LightGBM trên train+valid với %d vòng ...", n_rounds)
        best_pipe.fit(X_all, y_all)
    else:
        best_iter = 0

    # 7) Threshold tuning trên valid (F1-driven, recall >= 0.80)
    logger.info("=" * 60)
    logger.info("THRESHOLD TUNING (F1-driven, min_recall=0.80)")
    logger.info("=" * 60)
    # Lấy xác suất trên valid từ best_pipe (sau re-fit nếu là LightGBM)
    if best_name == "LightGBM":
        # Re-fit trên train+valid → valid prob không thật, dùng Xt_va + pipe cũ
        # (vẫn dùng pipe_lgb từ candidates để threshold tuning)
        prob_valid = pipe_lgb.predict_proba(X_valid)[:, 1]
    else:
        prob_valid = best_pipe.predict_proba(X_valid)[:, 1]
    best_thr, best_f1_va, best_rec_va, best_prec_va = best_threshold_for_f1(
        y_valid.values, prob_valid, min_recall=0.80,
    )
    logger.info(
        "Best threshold trên valid: thr=%.3f | F1=%.4f, Recall=%.4f, Precision=%.4f",
        best_thr, best_f1_va, best_rec_va, best_prec_va,
    )

    # 8) Calibrate nếu cần
    final_pipe, cal_method, cal_info = maybe_calibrate(best_pipe, X_valid, y_valid)
    logger.info("Final pipeline: %s, calibration: %s", best_name, cal_method)

    # 9) Đánh giá trên test
    metrics_all: dict[str, dict] = {}
    for name, (pipe, _, meta) in candidates.items():
        prob = pipe.predict_proba(X_test)[:, 1]
        m = all_metrics(y_test.values, prob)
        m_dict = m.to_dict()
        m_dict.update(meta)
        # Test metrics ở threshold tuned
        y_pred_test = (prob >= best_thr).astype(int)
        m_dict["test_threshold"] = best_thr
        m_dict["test_f1"] = float(f1_score(y_test.values, y_pred_test, zero_division=0))
        m_dict["test_recall"] = float(recall_score(y_test.values, y_pred_test, zero_division=0))
        m_dict["test_precision"] = float(precision_score(y_test.values, y_pred_test, zero_division=0))
        metrics_all[name] = m_dict

    # Final pipeline trên test (sau calibrate)
    final_prob = final_pipe.predict_proba(X_test)[:, 1]
    final_metrics = all_metrics(y_test.values, final_prob)
    y_pred_final = (final_prob >= best_thr).astype(int)
    metrics_all[f"{best_name}_calibrated"] = {
        **final_metrics.to_dict(),
        "calibration": cal_method,
        "valid_pre_calibration": cal_info.get("pre"),
        "valid_post_calibration": cal_info.get("post") if cal_method != "none" else None,
        "test_threshold": best_thr,
        "test_f1": float(f1_score(y_test.values, y_pred_final, zero_division=0)),
        "test_recall": float(recall_score(y_test.values, y_pred_final, zero_division=0)),
        "test_precision": float(precision_score(y_test.values, y_pred_final, zero_division=0)),
    }

    # 10) Lưu model + threshold + score formula
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "pipeline": final_pipe,
        "model_name": best_name,
        "calibration": cal_method,
        "num_cols": num_cols,
        "cat_cols": cat_cols,
        "feature_columns": list(X_train.columns),
        "best_threshold": best_thr,
        "best_lgb_params": best_meta.get("best_lgb_params"),
        "score_base": SCORE_BASE,
        "score_pdo": SCORE_PDO,
        "score_odds_base": SCORE_ODDS_BASE,
    }, MODEL_PATH)
    logger.info("Saved model -> %s (threshold=%.3f)", MODEL_PATH, best_thr)

    # Defaults cho app: ngưỡng + score formula
    DEFAULTS_PATH.write_text(json.dumps({
        "model_name": best_name,
        "calibration": cal_method,
        "best_threshold": best_thr,
        "score_base": SCORE_BASE,
        "score_pdo": SCORE_PDO,
        "score_odds_base": SCORE_ODDS_BASE,
        "test_metrics": metrics_all[f"{best_name}_calibrated"],
        "feature_columns": list(X_train.columns),
    }, indent=2, ensure_ascii=False))
    logger.info("Saved defaults -> %s", DEFAULTS_PATH)

    METRICS_PATH.write_text(json.dumps(metrics_all, indent=2, ensure_ascii=False))
    logger.info("Saved metrics -> %s", METRICS_PATH)

    # 10) Plots
    model_dir = ROC_PNG.parent
    plot_roc(
        y_test.values,
        {"Logistic": candidates["Logistic"][0].predict_proba(X_test)[:, 1],
         "Logistic_balanced": candidates["Logistic_balanced"][0].predict_proba(X_test)[:, 1],
         "LightGBM": candidates["LightGBM"][0].predict_proba(X_test)[:, 1],
         f"{best_name}_calibrated": final_prob},
        ROC_PNG,
    )
    plot_calibration(y_test.values, final_prob, CAL_PNG, name=f"{best_name}_calibrated")
    plot_ks(y_test.values, final_prob, model_dir / "ks_plot.png", name=f"{best_name}_calibrated")
    plot_pr(y_test.values, final_prob, model_dir / "pr_curve.png", name=f"{best_name}_calibrated")

    # 11) Bảng so sánh
    tbl = comparison_table(metrics_all)
    print("\n" + "=" * 60)
    print("METRICS TRÊN TEST")
    print("=" * 60)
    print(tbl.round(4).to_string())
    (ROC_PNG.parent / "metrics_table.csv").write_text(tbl.round(4).to_csv())

    logger.info("Tổng thời gian: %.1fs", time.time() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
