"""Inference cho ứng dụng web / batch.

Model artifact (`model/model.joblib`) chứa 3 schemas tương thích ngược:

  v4 (notebook mới): ct + lgb + iso_reg + feature_names + best_threshold
  v3: pipeline + iso_reg + feature_columns + best_threshold
  v2: preprocessor + lgb_booster + iso_reg + feature_names

Scorecard fields: score_base, score_pdo, score_odds_base
Risk bands: risk_bands (dict)

Cách dùng:
    import joblib
    model = joblib.load("model/model.joblib")
    result = predict_from_record(some_record_dict, model)
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from src import config

logger = logging.getLogger(__name__)

# ── Cache ──────────────────────────────────────────────────────────────────────
_MODEL_CACHE: dict[str, Any] = {}


# ── Scorecard helpers ──────────────────────────────────────────────────────────
def pd_to_score(pd_val: float, offset: float, factor: float) -> float:
    """Convert PD → FICO-like score: score = offset − factor × ln(odds)."""
    pd_val = max(min(pd_val, 0.9999), 1e-9)
    odds = pd_val / (1 - pd_val)
    return float(offset - factor * math.log(odds))


def score_to_band(score: float, risk_bands: dict[str, list[float]]) -> str:
    """Phân nhóm rủi ro theo score."""
    for label, (lo, hi) in risk_bands.items():
        if lo <= score <= hi:
            return label
    return "Very High"


# ── Core prediction ────────────────────────────────────────────────────────────
def predict_from_record(record: dict, model_dict: dict) -> dict:
    """
    Dự đoán từ 1 dict thông tin khách hàng.

    Hỗ trợ 3 artifact schemas:
      - Mới (v4, notebook mới): ``ct`` + ``lgb`` + ``iso_reg`` + ``feature_names``
      - Cũ (v3): ``pipeline`` + ``iso_reg`` + ``feature_columns``
      - Rất cũ: ``preprocessor`` + ``lgb_booster`` + ``iso_reg`` + ``feature_names``
    """
    offset: float = float(model_dict.get("score_formula", {}).get("offset",
        model_dict.get("score_base", 600) + 28.85 * np.log(
            model_dict.get("score_odds_base", 50))))
    factor: float = float(model_dict.get("score_formula", {}).get("factor",
        28.85 if model_dict.get("score_pdo", 20) == 20 else
        model_dict["score_pdo"] / np.log(2)))
    # NOTE: bands MUST be ordered from HIGHEST score to LOWEST so the first
    # matching range is the best (lowest-risk) band. (Low score = high risk.)
    risk_bands: dict = model_dict.get("risk_bands") or {
        "Excellent":  [760, 1000],
        "Good":       [700, 760],
        "Fair":       [640, 700],
        "Poor":       [580, 640],
        "Very Poor":  [300, 580],
    }
    thresh: float = float(model_dict.get("best_threshold", 0.5))
    model_name: str = str(model_dict.get("model_name", "LightGBM_calibrated"))

    # ── Schema v4 (notebook mới): ct + lgb + iso_reg ─────────────────────────
    if "ct" in model_dict and "lgb" in model_dict:
        ct   = model_dict["ct"]
        lgb_b = model_dict["lgb"]
        iso_r = model_dict.get("iso_reg")

        # ALWAYS use the ColumnTransformer's own feature_names_in_ (raw columns)
        # NEVER use feature_names from artifact — those are TRANSFORMED names
        # (e.g. "num__AGE_YEARS", "cat__NAME_CONTRACT_TYPE_Cash loans") and
        # would cause "columns are missing" ValueError.
        if not hasattr(ct, "feature_names_in_"):
            raise RuntimeError(
                "ColumnTransformer has no feature_names_in_ — model artifact "
                "is corrupted or built with a different sklearn version."
            )
        expected_cols = list(ct.feature_names_in_)
        logger.debug("predict_from_record: %d expected raw columns", len(expected_cols))

        X_raw = pd.DataFrame([record])

        # Build a single-row DataFrame with all expected columns; fill missing with NaN
        missing = [c for c in expected_cols if c not in X_raw.columns]
        if missing:
            logger.debug("predict_from_record: filling %d missing cols with NaN", len(missing))
            X_raw = pd.concat(
                [X_raw, pd.DataFrame({c: [np.nan] for c in missing}, index=X_raw.index)],
                axis=1,
            )

        # Reorder to match ct.feature_names_in_ exactly
        X_raw = X_raw[expected_cols]

        X_proc = ct.transform(X_raw)
        raw_prob = float(lgb_b.predict_proba(X_proc)[:, 1][0])
        pd_val = float(iso_r.predict([raw_prob])[0]) if iso_r is not None else raw_prob

    # ── Schema v3: pipeline + calibration ─────────────────────────────────────
    elif "pipeline" in model_dict:
        feature_columns = model_dict.get("feature_columns", model_dict.get("feature_names", []))
        X_raw = pd.DataFrame([record])
        for c in feature_columns:
            if c not in X_raw.columns:
                X_raw[c] = np.nan
        X_raw = X_raw[feature_columns] if feature_columns else X_raw

        raw_prob = float(model_dict["pipeline"].predict_proba(X_raw)[0, 1])

        cal = model_dict.get("calibration")
        if cal is not None and hasattr(cal, "predict"):
            pd_val = float(np.clip(cal.predict([raw_prob])[0], 1e-6, 1 - 1e-6))
        else:
            pd_val = raw_prob

    # ── Schema rất cũ: preprocessor + lgb_booster + iso_reg ─────────────────
    else:
        ct   = model_dict["preprocessor"]
        lgb_b = model_dict["lgb_booster"]
        iso_r = model_dict.get("iso_reg")

        X_raw = pd.DataFrame([record])
        if hasattr(ct, "feature_names_in_"):
            for c in ct.feature_names_in_:
                if c not in X_raw.columns:
                    X_raw[c] = np.nan
        X_proc = ct.transform(X_raw)
        raw_prob = float(lgb_b.predict(X_proc, num_iteration=lgb_b.best_iteration)[0])
        pd_val = float(iso_r.predict([raw_prob])[0]) if iso_r is not None else raw_prob
        if model_name == "LightGBM":
            model_name = "LightGBM_calibrated"

    score = pd_to_score(pd_val, offset, factor)
    band = score_to_band(score, risk_bands)
    decision = "APPROVE" if pd_val < thresh else "REJECT"

    return {
        "pd":         pd_val,
        "score":      round(score, 0),
        "risk_band":  band,
        "threshold":  thresh,
        "decision":   decision,
        "raw_prob":   raw_prob,
        "model_name": model_name,
    }


# ── Cached load ────────────────────────────────────────────────────────────────
def _load_model() -> dict[str, Any]:
    """Load model artifact (cache 1 lần cho Streamlit). Hỗ trợ .joblib và .pkl."""
    if "artifact" in _MODEL_CACHE:
        return _MODEL_CACHE["artifact"]

    # Thử .joblib trước, nếu không có thì .pkl
    candidates = [config.MODEL_PATH, config.MODEL_PATH.with_suffix(".pkl")]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        raise FileNotFoundError(
            f"Không tìm thấy model ở {candidates}. "
            "Chạy notebook `notebooks/home_credit_pipeline.ipynb` trước."
        )
    try:
        artifact = joblib.load(path)
    except Exception as e:
        raise RuntimeError(
            f"Không load được model từ {path} ({path.stat().st_size} bytes). "
            f"Có thể file bị corrupt hoặc version pickle không tương thích. "
            f"Python hiện tại: {__import__('sys').version}. Lỗi: {e}"
        ) from e

    # ── Normalize schema: ensure 'pipeline' key exists for predict_from_record ──
    # Schema mới (v4): ct + lgb + iso_reg
    # Schema cũ: pipeline  OR  preprocessor + lgb_booster
    if "pipeline" not in artifact and "ct" in artifact and "lgb" in artifact:
        from sklearn.pipeline import Pipeline as _Pipeline
        artifact["pipeline"] = _Pipeline([
            ("prep", artifact["ct"]),
            ("clf",  artifact["lgb"]),
        ])
        # Fallback feature_columns
        if "feature_columns" not in artifact:
            artifact["feature_columns"] = artifact.get("feature_names", [])

    _MODEL_CACHE["artifact"] = artifact
    logger.info("Model loaded: %s", path)
    return artifact


# ── Public API ─────────────────────────────────────────────────────────────────
def predict_one(record: dict) -> dict:
    """Dự đoán 1 khách hàng. Wrapper quanh predict_from_record."""
    model_dict = _load_model()
    return predict_from_record(record, model_dict)


def predict_batch(df: pd.DataFrame) -> pd.DataFrame:
    """Dự đoán hàng loạt từ DataFrame.

    Hỗ trợ cả 2 schema của model artifact:
      - Schema mới (v4): ``ct`` + ``lgb`` + ``iso_reg`` (sklearn API)
      - Schema cũ: ``preprocessor`` + ``lgb_booster`` (lightgbm Booster API)
    """
    model_dict = _load_model()

    # ── Resolve model components (handle both schemas) ────────────────────
    if "ct" in model_dict and "lgb" in model_dict:
        # Schema mới: ColumnTransformer (sklearn) + lgb sklearn classifier
        ct      = model_dict["ct"]
        lgb_b   = model_dict["lgb"]
        is_sklearn_lgb = True
    elif "preprocessor" in model_dict and "lgb_booster" in model_dict:
        # Schema cũ: preprocessor (ColumnTransformer) + lgb_booster (Booster)
        ct      = model_dict["preprocessor"]
        lgb_b   = model_dict["lgb_booster"]
        is_sklearn_lgb = False
    elif "pipeline" in model_dict:
        # Schema v3: pipeline
        pipeline = model_dict["pipeline"]
        cal = model_dict.get("calibration")
        thresh  = float(model_dict.get("best_threshold", 0.5))
        sf      = model_dict.get("score_formula", {})
        risk_bands = model_dict.get("risk_bands", {})
        offset  = float(sf.get("offset", 620))
        factor  = float(sf.get("factor", 28.85))

        ids = df[config.ID_COL].values if config.ID_COL in df.columns else range(len(df))
        raw_probs = pipeline.predict_proba(df)[:, 1]
        if cal is not None and hasattr(cal, "predict"):
            pd_vals = np.clip(cal.predict(raw_probs), 1e-6, 1 - 1e-6)
        else:
            pd_vals = raw_probs
        scores  = np.array([pd_to_score(p, offset, factor) for p in pd_vals])
        bands   = [score_to_band(s, risk_bands) for s in scores]
        decisns = np.where(pd_vals < thresh, "APPROVE", "REJECT")
        return pd.DataFrame({
            config.ID_COL: ids, "PD": pd_vals.round(4), "Score": scores.round(1),
            "RiskBand": bands, "Decision": decisns,
        })
    else:
        raise RuntimeError("Model artifact has unknown schema: no ct/preprocessor/pipeline")

    iso_r   = model_dict.get("iso_reg")
    thresh  = float(model_dict.get("best_threshold", 0.5))
    sf      = model_dict.get("score_formula", {})
    # NOTE: risk bands MUST be in descending score order so that the first
    # matching range is the highest-quality band. (Low score = high risk.)
    risk_bands = model_dict.get("risk_bands") or {
        "Excellent":  [760, 1000],
        "Good":       [700, 760],
        "Fair":       [640, 700],
        "Poor":       [580, 640],
        "Very Poor":  [300, 580],
    }
    offset  = float(sf.get("offset", 620))
    factor  = float(sf.get("factor", 28.85))

    ids = df[config.ID_COL].values if config.ID_COL in df.columns else range(len(df))

    # Make sure all expected columns exist; fill missing with NaN
    if hasattr(ct, "feature_names_in_"):
        missing = [c for c in ct.feature_names_in_ if c not in df.columns]
        if missing:
            df = df.copy()
            for c in missing:
                df[c] = np.nan
        # Reorder to match ColumnTransformer's expected order
        df = df[list(ct.feature_names_in_)]

    X_proc = ct.transform(df)
    if is_sklearn_lgb:
        raw_probs = lgb_b.predict_proba(X_proc)[:, 1]
    else:
        raw_probs = lgb_b.predict(X_proc, num_iteration=lgb_b.best_iteration)
    if iso_r is not None:
        pd_vals = iso_r.predict(raw_probs)
    else:
        pd_vals = raw_probs

    scores  = np.array([pd_to_score(p, offset, factor) for p in pd_vals])
    bands   = [score_to_band(s, risk_bands) for s in scores]
    decisns = np.where(pd_vals < thresh, "APPROVE", "REJECT")

    out = pd.DataFrame({
        config.ID_COL: ids,
        "PD":       pd_vals.round(4),
        "Score":    scores.round(1),
        "RiskBand": bands,
        "Decision": decisns,
    })
    return out


def get_model_info() -> dict[str, Any]:
    """Trả thông tin model (dùng cho tab Hiệu năng trong UI)."""
    model_dict = _load_model()
    sb = float(model_dict.get("score_base", 600))
    pdo = float(model_dict.get("score_pdo", 20))
    odds_b = float(model_dict.get("score_odds_base", 50))
    factor = pdo / np.log(2)
    offset = sb + factor * np.log(odds_b)

    risk_bands = model_dict.get("risk_bands") or {
        "Excellent":  [760, 1000],
        "Good":       [700, 760],
        "Fair":       [640, 700],
        "Poor":       [580, 640],
        "Very Poor":  [300, 580],
    }

    info = {
        "model_name":   str(model_dict.get("model_name", "LightGBM_calibrated")),
        "threshold":    float(model_dict.get("best_threshold", 0.5)),
        "n_features":   len(model_dict.get("feature_names",
                                       model_dict.get("feature_columns", []))),
        "score_formula": {
            "offset":       float(model_dict.get("score_formula", {}).get("offset", offset)),
            "factor":       float(model_dict.get("score_formula", {}).get("factor", factor)),
            "base":         sb,
            "pdo":          pdo,
            "odds_at_base": odds_b,
        },
        "risk_bands": {k: list(v) for k, v in risk_bands.items()},
    }

    metrics_path = config.MODEL_DIR / "metrics.json"
    if metrics_path.exists():
        info["metrics"] = json.loads(metrics_path.read_text(encoding="utf-8"))

    return info


def get_default_customer() -> dict:
    """Trả dict khách hàng mẫu với RAW columns (chưa qua FE).

    Lấy từ application_train.csv (5000 dòng đầu, chọn TARGET=0 + loại anomaly).
    Dùng để fill form mặc định trong Streamlit. Sau khi user submit, FE sẽ
    được chạy trên dict này để có engineered features cho model.

    Trả về dict rỗng nếu không tìm thấy CSV.
    """
    csv_path = config.APP_TRAIN_CSV
    if not Path(csv_path).exists():
        sample_p = config.PROJECT_ROOT / "data" / "sample" / "application_train_sample.csv"
        if sample_p.exists():
            csv_path = sample_p
        else:
            return {}

    df = pd.read_csv(csv_path, nrows=5000)
    # Prefer a clean row: TARGET=0 + no DAYS_EMPLOYED anomaly
    clean = df[(df["TARGET"] == 0) & (df["DAYS_EMPLOYED"] != 365243)]
    if len(clean) == 0:
        clean = df[df["DAYS_EMPLOYED"] != 365243]
    if len(clean) == 0:
        clean = df

    row = clean.iloc[0]
    sample: dict[str, Any] = {}
    for c, v in row.items():
        if c == "TARGET":
            continue
        if hasattr(v, "item"):
            sample[c] = v.item()
        elif pd.isna(v):
            sample[c] = None
        else:
            sample[c] = v
    return sample


__all__ = [
    "predict_one",
    "predict_batch",
    "predict_from_record",
    "get_model_info",
    "get_default_customer",
    "pd_to_score",
    "score_to_band",
]
