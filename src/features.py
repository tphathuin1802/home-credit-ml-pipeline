"""Feature engineering cho Home Credit Default Risk.

Module này hoàn toàn pure-Python / pandas — KHÔNG phụ thuộc scikit-learn, để có
thể import an toàn trong app Docker (image inference không cần sklearn nặng).

Tài chính / Math cho từng nhóm feature (giải thích để bảo vệ đồ án):

1. Application ratios
   - ``CREDIT_INCOME_RATIO = AMT_CREDIT / AMT_INCOME_TOTAL`` — đo **DTI** (debt-
     to-income). DTI càng cao, khách càng khó trả. Quy ước ngân hàng: DTI
     < 36% an toàn, 36-43% cảnh báo, > 43% rủi ro cao.
   - ``ANNUITY_INCOME_RATIO = AMT_ANNUITY / AMT_INCOME_TOTAL`` — tỉ lệ trả góp
     hàng tháng / thu nhập. Tương tự DTI nhưng phản ánh dòng tiền ngắn hạn.
   - ``CREDIT_TERM = AMT_CREDIT / AMT_ANNUITY`` — số tháng trả (thường 12-60
     cho vay tiêu dùng). Kỳ hạn dài → gánh nặng lãi lớn nhưng trả hàng tháng
     nhỏ.

2. Time-derived
   - ``AGE_YEARS = -DAYS_BIRTH / 365.25`` — tuổi (năm). Hệ số âm vì Home Credit
     quy ước ngày về quá khứ.
   - ``EMPLOYED_YEARS = -DAYS_EMPLOYED / 365.25`` — thâm niên (năm). Sentinel
     ``365243`` nghĩa là "nghỉ việc / không xác định" → đổi thành NaN + cờ
     ``EMPLOYED_ANOM``.
   - ``DAYS_LAST_PHONE_CHANGE`` giữ nguyên (tín hiệu gian lận nhẹ).

3. EXT_SOURCE
   - ``EXT_SOURCE_MEAN / MIN / MAX / STD`` — điểm tín nhiệm từ 3 nguồn ngoài.
     Cao → an toàn. Solution top-1 Kaggle dùng trung bình 3 nguồn là feature
     quan trọng nhất. Một số nguồn (1) chỉ có ở ~43% khách → pipeline xử lý
     missing.

4. Document / flag / categorical
   - Document flags: cộng ``FLAG_DOCUMENT_*`` thành ``NUM_DOCS_SUBMITTED`` —
     phản ánh khách chuẩn bị hồ sơ kỹ hay không.
   - Categorical: ``CODE_GENDER`` (F/M, XNA hiếm), ``NAME_INCOME_TYPE``,
     ``NAME_EDUCATION_TYPE``, ``NAME_FAMILY_STATUS``, ``OCCUPATION_TYPE``,
     ``ORGANIZATION_TYPE`` (rất nhiều giá trị) — sẽ xử lý bằng OneHotEncoder
     trong pipeline ở GĐ 3.

5. Bureau aggregates (groupby SK_ID_CURR, left join)
   - Số khoản vay, số khoản active, số khoản quá hạn — phản ánh **lịch sử
     tín dụng bên ngoài Home Credit**.
   - Tổng dư nợ, tổng quá hạn — quy mô "đòn bẩy" của khách.
   - Tỉ lệ ``DEBT_CREDIT_RATIO = AMT_CREDIT_SUM_DEBT / AMT_CREDIT_SUM`` —
     khách đã "đốt" bao nhiêu % hạn mức.
   - Khách không có bureau → tổng = 0 (ngoại trừ debt có thể = NaN → điền 0)
     + cờ ``HAS_BUREAU = 0``. Kinh tế: khách "không có lịch sử" thường bị
     đánh giá rủi ro cao hơn vì thiếu thông tin (thin-file borrower).
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from src.config import DAYS_EMPLOYED_SENTINEL

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Application features
# ----------------------------------------------------------------------
APP_NUMERIC_BASE = [
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "AMT_GOODS_PRICE",
    "CNT_FAM_MEMBERS",
    "CNT_CHILDREN",
    "DAYS_REGISTRATION",
    "DAYS_ID_PUBLISH",
    "DAYS_LAST_PHONE_CHANGE",
    "OWN_CAR_AGE",
    "REGION_POPULATION_RELATIVE",
    "HOUR_APPR_PROCESS_START",
    "EXT_SOURCE_1",
    "EXT_SOURCE_2",
    "EXT_SOURCE_3",
]

APP_CAT_BASE = [
    "CODE_GENDER",
    "FLAG_OWN_CAR",
    "FLAG_OWN_REALTY",
    "NAME_TYPE_SUITE",
    "NAME_INCOME_TYPE",
    "NAME_EDUCATION_TYPE",
    "NAME_FAMILY_STATUS",
    "NAME_HOUSING_TYPE",
    "OCCUPATION_TYPE",
    "ORGANIZATION_TYPE",
    "WEEKDAY_APPR_PROCESS_START",
    "FONDKAPREMONT_MODE",
    "HOUSETYPE_MODE",
    "WALLSMATERIAL_MODE",
    "EMERGENCYSTATE_MODE",
]


def clean_application(df: pd.DataFrame) -> pd.DataFrame:
    """Làm sạch application_train/test, trả DataFrame mới.

    Bước xử lý:
    - ``DAYS_EMPLOYED == 365243`` → NaN + thêm cờ ``EMPLOYED_ANOM``.
    - Các ``DAYS_*`` âm → giữ nguyên (chỉ dùng qua hàm ``-DAYS/365.25``).
    - ``CODE_GENDER == 'XNA'`` → NaN để imputer xử lý.
    - ``OWN_CAR_AGE`` ở khách không có ô tô → NaN.
    """
    df = df.copy()

    # 1) DAYS_EMPLOYED sentinel
    df["EMPLOYED_ANOM"] = (df["DAYS_EMPLOYED"] == DAYS_EMPLOYED_SENTINEL).astype("int8")
    df.loc[df["DAYS_EMPLOYED"] == DAYS_EMPLOYED_SENTINEL, "DAYS_EMPLOYED"] = np.nan

    # 2) CODE_GENDER XNA
    if "CODE_GENDER" in df.columns:
        df.loc[df["CODE_GENDER"] == "XNA", "CODE_GENDER"] = np.nan

    # 3) OWN_CAR_AGE: với khách FLAG_OWN_CAR=='N' thì để NaN (semantically no car)
    if {"FLAG_OWN_CAR", "OWN_CAR_AGE"}.issubset(df.columns):
        df.loc[df["FLAG_OWN_CAR"] == "N", "OWN_CAR_AGE"] = np.nan

    return df


def build_application_features(df: pd.DataFrame) -> pd.DataFrame:
    """Sinh feature dẫn xuất từ application (ratios, time, EXT_SOURCE)."""
    df = df.copy()

    # Ratios
    income = df["AMT_INCOME_TOTAL"].replace(0, np.nan)
    annuity = df["AMT_ANNUITY"].replace(0, np.nan)
    df["CREDIT_INCOME_RATIO"] = df["AMT_CREDIT"] / income
    df["ANNUITY_INCOME_RATIO"] = annuity / income
    df["CREDIT_TERM"] = df["AMT_CREDIT"] / annuity
    df["CREDIT_GOODS_RATIO"] = df["AMT_CREDIT"] / df["AMT_GOODS_PRICE"].replace(0, np.nan)
    df["INCOME_PER_FAM"] = income / df["CNT_FAM_MEMBERS"].replace(0, np.nan)
    df["INCOME_PER_CHILD"] = income / (df["CNT_CHILDREN"] + 1)

    # Time features (years)
    df["AGE_YEARS"] = -df["DAYS_BIRTH"] / 365.25
    df["EMPLOYED_YEARS"] = -df["DAYS_EMPLOYED"] / 365.25
    df["REGISTERED_YEARS"] = -df["DAYS_REGISTRATION"] / 365.25
    df["ID_PUBLISH_YEARS"] = -df["DAYS_ID_PUBLISH"] / 365.25
    df["LAST_PHONE_YEARS"] = -df["DAYS_LAST_PHONE_CHANGE"] / 365.25

    # EXT_SOURCE aggregates
    ext = df[["EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"]]
    df["EXT_SOURCE_MEAN"] = ext.mean(axis=1)
    df["EXT_SOURCE_MIN"] = ext.min(axis=1)
    df["EXT_SOURCE_MAX"] = ext.max(axis=1)
    df["EXT_SOURCE_STD"] = ext.std(axis=1)
    # Tích các nguồn: nếu thiếu nhiều hơn 1 nguồn thì để NaN (sẽ được impute)
    df["EXT_SOURCE_PROD"] = ext.prod(axis=1, min_count=2)
    df["EXT_SOURCE_COUNT"] = ext.notna().sum(axis=1).astype("int8")

    # Document flags
    doc_cols = [c for c in df.columns if c.startswith("FLAG_DOCUMENT_")]
    if doc_cols:
        df["NUM_DOCS_SUBMITTED"] = df[doc_cols].sum(axis=1).astype("int8")
    else:
        df["NUM_DOCS_SUBMITTED"] = 0

    # Drop raw DAYS_*: giữ bản derived ở trên
    drop = [c for c in df.columns if c.startswith("DAYS_")]
    df = df.drop(columns=drop)

    return df


# ----------------------------------------------------------------------
# Bureau features
# ----------------------------------------------------------------------
def build_bureau_features(bureau: pd.DataFrame) -> pd.DataFrame:
    """Aggregate bureau.csv theo SK_ID_CURR.

    Trả về DataFrame index = SK_ID_CURR, cột = feature aggregate.
    Khách không có bureau KHÔNG xuất hiện ở output (sẽ được fillna trong
    ``merge_features``).
    """
    import gc
    # Chỉ select cột cần thiết
    keep = [c for c in [
        "SK_ID_CURR", "CREDIT_ACTIVE", "CREDIT_TYPE",
        "DAYS_CREDIT", "DAYS_CREDIT_ENDDATE", "DAYS_ENDDATE_FACT", "DAYS_CREDIT_UPDATE",
        "AMT_CREDIT_SUM", "AMT_CREDIT_SUM_DEBT", "AMT_CREDIT_SUM_LIMIT", "AMT_CREDIT_SUM_OVERDUE",
        "CREDIT_DAY_OVERDUE", "CNT_CREDIT_PROLONG",
    ] if c in bureau.columns]
    b = bureau[keep].copy()
    del bureau
    gc.collect()

    # Days features: chuyển về năm để dễ đọc
    for c in ("DAYS_CREDIT", "DAYS_CREDIT_ENDDATE", "DAYS_ENDDATE_FACT", "DAYS_CREDIT_UPDATE"):
        if c in b.columns:
            b[c] = -b[c] / 365.25  # năm

    # Active flag
    b["IS_ACTIVE"] = (b["CREDIT_ACTIVE"] == "Active").astype("int8")
    b["IS_CLOSED"] = (b["CREDIT_ACTIVE"] == "Closed").astype("int8")
    b["IS_OVERDUE"] = (b["CREDIT_DAY_OVERDUE"] > 0).astype("int8")

    # Categorical one-hot cho CREDIT_TYPE
    type_counts = (
        b.groupby(["SK_ID_CURR", "CREDIT_TYPE"]).size().unstack(fill_value=0)
    )
    type_counts.columns = [f"BUREAU_TYPE_{c.upper().replace(' ', '_')}" for c in type_counts.columns]

    agg_dict = {
        "IS_ACTIVE": ["sum", "mean"],
        "IS_CLOSED": ["sum", "mean"],
        "IS_OVERDUE": ["sum", "mean"],
        "DAYS_CREDIT": ["min", "max", "mean"],
        "AMT_CREDIT_SUM": ["sum", "mean", "max"],
        "AMT_CREDIT_SUM_DEBT": ["sum", "mean", "max"],
        "AMT_CREDIT_SUM_LIMIT": ["sum", "mean"],
        "AMT_CREDIT_SUM_OVERDUE": ["sum", "max"],
        "CREDIT_DAY_OVERDUE": ["max", "mean"],
        "CNT_CREDIT_PROLONG": ["sum", "max"],
    }

    agg = b.groupby("SK_ID_CURR").agg(agg_dict)
    agg.columns = ["BUREAU_" + "_".join(c).upper() for c in agg.columns]

    # Tỉ lệ nợ / tổng hạn mức
    total_debt = agg["BUREAU_AMT_CREDIT_SUM_DEBT_SUM"].replace(0, np.nan)
    total_credit = agg["BUREAU_AMT_CREDIT_SUM_SUM"].replace(0, np.nan)
    agg["BUREAU_DEBT_CREDIT_RATIO"] = (total_debt / total_credit).astype(float)

    # Count of loans
    counts = b.groupby("SK_ID_CURR").size().rename("BUREAU_CNT_LOANS")
    has_bureau = pd.Series(1, index=counts.index, name="HAS_BUREAU", dtype="int8")

    out = agg.join(counts).join(type_counts, how="left").join(has_bureau, how="left")
    out = out.fillna(0)  # categorical type_counts: missing = 0
    return out


# ----------------------------------------------------------------------
# Previous application features
# ----------------------------------------------------------------------
def build_prev_app_features(prev: pd.DataFrame) -> pd.DataFrame:
    """Aggregate previous_application.csv theo SK_ID_CURR.

    Tài chính / Math:
    - Tỉ lệ ``APPROVED / REFUSED`` trong lịch sử vay Home Credit phản ánh
      rủi ro khách: tỉ lệ refused cao → khách đã từng bị đánh giá cao rủi ro.
    - ``AMT_CREDIT`` tổng + max: khách có thói quen vay bao nhiêu.
    - ``DAYS_DECISION`` (ngày quyết định) gần nhất → thời gian cập nhật
      thông tin gần nhất. Quá cũ → có thể thông tin đã outdated.
    - ``CNT_PAYMENT`` (số kỳ thanh toán) trung bình → kỳ hạn trung bình.
    """
    import gc
    # Chỉ select cột cần thiết để giảm RAM
    keep = [c for c in [
        "SK_ID_CURR", "NAME_CONTRACT_STATUS",
        "AMT_ANNUITY", "AMT_APPLICATION", "AMT_CREDIT", "AMT_DOWN_PAYMENT", "AMT_GOODS_PRICE",
        "RATE_DOWN_PAYMENT",
        "DAYS_DECISION", "DAYS_FIRST_DRAWING", "DAYS_FIRST_DUE",
        "DAYS_LAST_DUE_1ST_VERSION", "DAYS_LAST_DUE", "DAYS_TERMINATION",
        "CNT_PAYMENT",
    ] if c in prev.columns]
    p = prev[keep].copy()
    del prev
    gc.collect()

    # Tỉ lệ trạng thái hợp đồng
    status_counts = (
        p.groupby(["SK_ID_CURR", "NAME_CONTRACT_STATUS"]).size().unstack(fill_value=0)
    )
    status_counts.columns = [f"PREV_STATUS_{c.upper()}" for c in status_counts.columns]
    # Tỉ lệ approved
    if "PREV_STATUS_APPROVED" in status_counts.columns and "PREV_STATUS_REFUSED" in status_counts.columns:
        denom = status_counts["PREV_STATUS_APPROVED"] + status_counts["PREV_STATUS_REFUSED"]
        status_counts["PREV_APPROVE_RATE"] = (
            status_counts["PREV_STATUS_APPROVED"] / denom.replace(0, np.nan)
        ).fillna(0)

    # Cột thời gian về năm
    for c in ("DAYS_DECISION", "DAYS_FIRST_DRAWING", "DAYS_FIRST_DUE", "DAYS_LAST_DUE_1ST_VERSION", "DAYS_LAST_DUE", "DAYS_TERMINATION"):
        if c in p.columns:
            p[c] = -p[c] / 365.25

    agg_dict = {
        "AMT_ANNUITY": ["mean", "max", "sum"],
        "AMT_APPLICATION": ["mean", "max", "sum"],
        "AMT_CREDIT": ["mean", "max", "sum"],
        "AMT_DOWN_PAYMENT": ["mean", "max", "sum"],
        "AMT_GOODS_PRICE": ["mean", "max"],
        "RATE_DOWN_PAYMENT": ["mean", "min", "max"],
        "DAYS_DECISION": ["min", "max", "mean"],
        "CNT_PAYMENT": ["mean", "sum", "max"],
        "DAYS_FIRST_DUE": ["mean"],
        "DAYS_LAST_DUE_1ST_VERSION": ["mean"],
        "DAYS_LAST_DUE": ["mean"],
        "DAYS_TERMINATION": ["mean"],
    }
    # Chỉ giữ cột thực sự tồn tại (1 số file có thể khác)
    agg_dict = {k: v for k, v in agg_dict.items() if k in p.columns}
    agg = p.groupby("SK_ID_CURR").agg(agg_dict)
    agg.columns = ["PREV_" + "_".join(c).upper() for c in agg.columns]

    counts = p.groupby("SK_ID_CURR").size().rename("PREV_CNT_APPLICATIONS")

    out = agg.join(counts).join(status_counts, how="left").fillna(0)
    return out


# ----------------------------------------------------------------------
# Installments payments features
# ----------------------------------------------------------------------
def build_installments_features(inst: pd.DataFrame) -> pd.DataFrame:
    """Aggregate installments_payments.csv theo SK_ID_CURR.

    Tài chính / Math:
    - ``late_days = DAYS_INSTALMENT - DAYS_ENTRY_PAYMENT``:
      + > 0 → trễ hạn (tín hiệu rủi ro cốt lõi).
      + < 0 → trả sớm (tín hiệu tốt).
      + = 0 → đúng hạn.
    - Tỉ lệ khách **trễ hơn X ngày** (X=1, 7, 30, 60) trong lịch sử
      là một trong các feature mạnh nhất trên Home Credit.
    - Tổng tiền trả / tổng phải trả = tỉ lệ hoàn thành nghĩa vụ.
    """
    inst = inst[[c for c in [
        "SK_ID_CURR", "DAYS_INSTALMENT", "DAYS_ENTRY_PAYMENT",
        "AMT_INSTALMENT", "AMT_PAYMENT",
    ] if c in inst.columns]].copy()
    import gc
    # late_days > 0 → trễ hạn
    inst["LATE_DAYS"] = inst["DAYS_INSTALMENT"] - inst["DAYS_ENTRY_PAYMENT"]
    inst["LATE_FLAG"] = (inst["LATE_DAYS"] > 0).astype("int8")
    inst["LATE_1D"] = (inst["LATE_DAYS"] > 1).astype("int8")
    inst["LATE_7D"] = (inst["LATE_DAYS"] > 7).astype("int8")
    inst["LATE_30D"] = (inst["LATE_DAYS"] > 30).astype("int8")
    inst["LATE_60D"] = (inst["LATE_DAYS"] > 60).astype("int8")
    inst["LATE_AMT"] = (inst["AMT_INSTALMENT"] - inst["AMT_PAYMENT"]).clip(lower=0)
    inst["UNDERPAID"] = (inst["AMT_PAYMENT"] < inst["AMT_INSTALMENT"]).astype("int8")

    # Chuẩn hoá thời gian về năm
    for c in ("DAYS_INSTALMENT", "DAYS_ENTRY_PAYMENT"):
        inst[c] = -inst[c] / 365.25

    # Tổng theo khách
    grp = inst.groupby("SK_ID_CURR")
    agg_dict = {
        "LATE_DAYS": ["max", "mean", "std", "sum"],
        "LATE_FLAG": ["sum", "mean"],
        "LATE_1D": ["sum", "mean"],
        "LATE_7D": ["sum", "mean"],
        "LATE_30D": ["sum", "mean"],
        "LATE_60D": ["sum", "mean"],
        "LATE_AMT": ["sum", "max"],
        "UNDERPAID": ["sum", "mean"],
        "AMT_INSTALMENT": ["sum", "max", "mean"],
        "AMT_PAYMENT": ["sum", "max", "mean"],
        "DAYS_INSTALMENT": ["min", "max", "mean"],
        "DAYS_ENTRY_PAYMENT": ["min", "max", "mean"],
    }
    agg = grp.agg(agg_dict)
    agg.columns = ["INST_" + "_".join(c).upper() for c in agg.columns]
    # Tỉ lệ hoàn thành: AMT_PAYMENT / AMT_INSTALMENT
    total_pay = agg["INST_AMT_PAYMENT_SUM"]
    total_due = agg["INST_AMT_INSTALMENT_SUM"].replace(0, np.nan)
    agg["INST_PAY_RATIO"] = (total_pay / total_due).fillna(0)
    counts = grp.size().rename("INST_CNT_INSTALMENTS")
    return agg.join(counts).fillna(0)


# ----------------------------------------------------------------------
# POS_CASH_balance features
# ----------------------------------------------------------------------
def build_pos_cc_features(
    pos: pd.DataFrame,
    cc: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate POS_CASH_balance + credit_card_balance theo SK_ID_CURR.

    Tài chính / Math:
    - ``utilization = CNT_INSTALMENT_FUTURE / CNT_INSTALMENT`` — khách đang
      trong bao nhiêu kỳ trả góp tới (còn dư nợ nhiều).
    - Credit card: ``AMT_BALANCE / AMT_CREDIT_LIMIT_ACTUAL`` = utilization
      ratio revolving. Cao → rủi ro.
    """
    import gc
    keep = [c for c in [
        "SK_ID_CURR", "MONTHS_BALANCE", "CNT_INSTALMENT", "CNT_INSTALMENT_FUTURE",
    ] if c in pos.columns]
    pos = pos[keep].copy()
    del keep
    # Util ratio POS
    if "CNT_INSTALMENT_FUTURE" in pos.columns and "CNT_INSTALMENT" in pos.columns:
        pos["POS_UTIL"] = (pos["CNT_INSTALMENT_FUTURE"] / pos["CNT_INSTALMENT"].replace(0, np.nan)).fillna(0)
    pos["MONTHS_BALANCE"] = -pos["MONTHS_BALANCE"] / 12  # năm

    pos_agg = pos.groupby("SK_ID_CURR").agg(
        POS_UTIL_MAX=("POS_UTIL", "max"),
        POS_UTIL_MEAN=("POS_UTIL", "mean"),
        POS_CNT_INSTALMENT_MEAN=("CNT_INSTALMENT", "mean"),
        POS_MONTHS_BALANCE_MIN=("MONTHS_BALANCE", "min"),
    )
    pos_count = pos.groupby("SK_ID_CURR").size().rename("POS_CNT")

    # Credit card (chỉ select cột cần thiết để tiết kiệm RAM)
    cc_cols = [c for c in [
        "SK_ID_CURR", "MONTHS_BALANCE", "AMT_BALANCE", "AMT_CREDIT_LIMIT_ACTUAL",
    ] if c in cc.columns]
    cc_view = cc[cc_cols].copy()
    if {"AMT_BALANCE", "AMT_CREDIT_LIMIT_ACTUAL"}.issubset(cc_view.columns):
        cc_view["CC_UTIL"] = (cc_view["AMT_BALANCE"] / cc_view["AMT_CREDIT_LIMIT_ACTUAL"].replace(0, np.nan)).fillna(0)
    if "MONTHS_BALANCE" in cc_view.columns:
        cc_view["MONTHS_BALANCE"] = -cc_view["MONTHS_BALANCE"] / 12
    del cc
    import gc; gc.collect()
    cc_agg = cc_view.groupby("SK_ID_CURR").agg(
        CC_UTIL_MAX=("CC_UTIL", "max") if "CC_UTIL" in cc_view.columns else ("AMT_BALANCE", "max"),
        CC_UTIL_MEAN=("CC_UTIL", "mean") if "CC_UTIL" in cc_view.columns else ("AMT_BALANCE", "mean"),
        CC_BALANCE_MAX=("AMT_BALANCE", "max") if "AMT_BALANCE" in cc_view.columns else ("MONTHS_BALANCE", "max"),
        CC_BALANCE_SUM=("AMT_BALANCE", "sum") if "AMT_BALANCE" in cc_view.columns else ("MONTHS_BALANCE", "sum"),
        CC_LIMIT_MAX=("AMT_CREDIT_LIMIT_ACTUAL", "max") if "AMT_CREDIT_LIMIT_ACTUAL" in cc_view.columns else ("MONTHS_BALANCE", "max"),
        CC_MONTHS_BALANCE_MIN=("MONTHS_BALANCE", "min"),
    )
    cc_count = cc_view.groupby("SK_ID_CURR").size().rename("CC_CNT")
    del cc_view; gc.collect()

    out = pos_agg.join(pos_count, how="outer").join(cc_agg, how="outer").join(cc_count, how="outer").fillna(0)
    out["HAS_POS"] = (out["POS_CNT"] > 0).astype("int8")
    out["HAS_CC"] = (out["CC_CNT"] > 0).astype("int8")
    return out


# ----------------------------------------------------------------------
# Merge
# ----------------------------------------------------------------------
def merge_features(
    app_feat: pd.DataFrame,
    bureau_feat: pd.DataFrame,
    *extra_feats: pd.DataFrame,
) -> pd.DataFrame:
    """Left join application với bureau (+ extras) aggregates. Khách không có
    bureau/extras → điền 0 cho numeric + cờ ``HAS_* = 0``.
    """
    id_col = _id_col_name(app_feat)
    all_ids = pd.DataFrame({id_col: app_feat[id_col].unique()})

    def _align(feat: pd.DataFrame, has_col: str) -> pd.DataFrame:
        feat = feat.copy()
        if has_col not in feat.columns:
            feat[has_col] = 1
        feat = all_ids.merge(feat, on=id_col, how="left")
        feat[has_col] = feat[has_col].fillna(0).astype("int8")
        num_cols = feat.select_dtypes(include=[np.number]).columns.drop(has_col, errors="ignore")
        feat[num_cols] = feat[num_cols].fillna(0)
        return feat

    bureau_feat = _align(bureau_feat, "HAS_BUREAU")
    merged = app_feat.merge(bureau_feat, on=id_col, how="left")
    for i, extra in enumerate(extra_feats):
        has_col = f"HAS_EXTRA_{i}"
        extra = _align(extra, has_col)
        merged = merged.merge(extra, on=id_col, how="left")
    # Fill bất kỳ HAS_* còn lại
    for c in [c for c in merged.columns if c.startswith("HAS_") or c.startswith("HAS_EXTRA_")]:
        merged[c] = merged[c].fillna(0).astype("int8")
    return merged


def _id_col_name(df: pd.DataFrame) -> str:
    for c in ("SK_ID_CURR", "sk_id_curr"):
        if c in df.columns:
            return c
    raise KeyError("SK_ID_CURR not found")


# ----------------------------------------------------------------------
# Pipeline entry point
# ----------------------------------------------------------------------
def build_full_features(
    app: pd.DataFrame,
    bureau: pd.DataFrame,
    prev: pd.DataFrame | None = None,
    installments: pd.DataFrame | None = None,
    pos: pd.DataFrame | None = None,
    cc: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Pipeline đầy đủ: clean → app features → bureau (+ extras) → merge.

    Các bảng ``prev / installments / pos / cc`` là optional; nếu truyền
    ``None`` thì bỏ qua. Trả về DataFrame đã sẵn sàng cho ColumnTransformer
    (numeric + categorical sẽ được tách trong train.py).
    """
    logger.info("Cleaning application (%d rows)...", len(app))
    app_clean = clean_application(app)
    logger.info("Building application features...")
    app_feat = build_application_features(app_clean)

    logger.info("Building bureau features (%d bureau rows)...", len(bureau))
    bureau_feat = build_bureau_features(bureau)

    extras: list[pd.DataFrame] = []
    if prev is not None and len(prev) > 0:
        logger.info("Building previous_application features (%d rows)...", len(prev))
        extras.append(build_prev_app_features(prev))
    if installments is not None and len(installments) > 0:
        logger.info("Building installments features (%d rows)...", len(installments))
        extras.append(build_installments_features(installments))
    if pos is not None and len(pos) > 0:
        logger.info("Building POS/CC features (pos=%d, cc=%d)...", len(pos), len(cc) if cc is not None else 0)
        extras.append(build_pos_cc_features(pos, cc if cc is not None else pos.iloc[:0]))

    logger.info("Merging application + bureau + %d extras...", len(extras))
    merged = merge_features(app_feat, bureau_feat, *extras)
    logger.info("Final feature matrix: %s", merged.shape)
    return merged


# ----------------------------------------------------------------------
# Sklearn-compatible helper (dùng trong train.py, cần module-level để pickle ổn định)
# ----------------------------------------------------------------------
class _ClipTransformer:
    """Clip inf -> NaN, rồi tới imputer. Định nghĩa ở module-level (features.py)
    để joblib pickle/unpickle an toàn (nếu đặt ở train.py sẽ resolve về __main__
    và lỗi khi load từ app khác)."""

    def fit(self, X, y=None):  # noqa
        return self

    def transform(self, X):
        return np.where(np.isinf(X), np.nan, X)


# ----------------------------------------------------------------------
# Single-row feature builder (for predict / streamlit)
# ----------------------------------------------------------------------
def build_features_for_one_row(app_row: pd.DataFrame) -> pd.DataFrame:
    """Build engineered features for a SINGLE application row.

    Returns a 1-row DataFrame with all expected feature columns (app + bureau +
    prev + installments + pos + cc) so that ``predict_from_record`` works
    without raising "columns are missing" ValueError.

    Since we don't have bureau/prev/etc. for an arbitrary user input, the
    corresponding aggregate columns are filled with 0 and the HAS_* flags
    are set to 0. The model has been trained on the same convention (users
    without bureau → HAS_BUREAU=0, aggregated columns=0).
    """
    # 1) Clean + app features
    app_clean = clean_application(app_row)
    app_feat  = build_application_features(app_clean)

    # 2) Get expected aggregate column names from a full pipeline run
    #    (we can't run on a single row alone, so we read from artifact at predict time)
    # For now, build empty dataframes with HAS_* flags; the ColumnTransformer's
    # imputer will handle the rest.
    sk_id = app_feat["SK_ID_CURR"].iloc[0] if "SK_ID_CURR" in app_feat.columns else 0
    base_idx = app_feat.index

    # Empty bureau features: 0s for everything + HAS_BUREAU=0
    bureau_empty = pd.DataFrame({"SK_ID_CURR": [sk_id], "HAS_BUREAU": [0]})

    # Empty extras: 0s for everything + HAS_*=0
    extras_empty = [
        pd.DataFrame({"SK_ID_CURR": [sk_id], "HAS_EXTRA_0": [0]}),  # prev
        pd.DataFrame({"SK_ID_CURR": [sk_id], "HAS_EXTRA_1": [0]}),  # inst
        pd.DataFrame({"SK_ID_CURR": [sk_id], "HAS_EXTRA_2": [0]}),  # pos/cc
    ]

    merged = merge_features(app_feat, bureau_empty, *extras_empty)
    return merged
