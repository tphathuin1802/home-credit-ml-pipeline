"""Quick EDA script - phuc vu notebooks/01_eda.ipynb.

Chay:  python -m notebooks.eda_quick
Hoac:  jupyter nbconvert --to notebook --execute notebooks/eda_quick.py
       de tao notebooks/01_eda.ipynb.

Toan/TC: Muc tieu la xac dinh
- Ty le TARGET (default rate) ~ 8% (mat can bang).
- Phan phoi DAYS_EMPLOYED co sentinel 365243.
- Missing rate cua EXT_SOURCE_1/2/3, ORGANIZATION_TYPE...
- Ty le khach co bureau (gan 100%).
- Danh sach bien categorical nhieu gia tri (can bucket hoac target-encode sau).
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import (
    APP_TRAIN_CSV,
    BUREAU_CSV,
    DAYS_EMPLOYED_SENTINEL,
    SAMPLE_ROWS,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)


def load_sample() -> tuple[pd.DataFrame, pd.DataFrame]:
    app = pd.read_csv(APP_TRAIN_CSV, nrows=SAMPLE_ROWS)
    bureau = pd.read_csv(BUREAU_CSV)
    bureau = bureau[bureau["SK_ID_CURR"].isin(app["SK_ID_CURR"])]
    log.info("app=%d rows, bureau=%d rows", len(app), len(bureau))
    return app, bureau


def main() -> None:
    app, bureau = load_sample()

    # 1) Target imbalance
    default_rate = app["TARGET"].mean()
    log.info("Default rate: %.4f", default_rate)

    # 2) DAYS_EMPLOYED sentinel
    n_sentinel = (app["DAYS_EMPLOYED"] == DAYS_EMPLOYED_SENTINEL).sum()
    log.info("DAYS_EMPLOYED sentinel: %d (%.2f%%)", n_sentinel, 100 * n_sentinel / len(app))

    # 3) Missing top 20
    miss = app.isna().mean().sort_values(ascending=False).head(20)
    log.info("Top 20 missing:\n%s", miss.to_string())

    # 4) EXT_SOURCE
    for c in ("EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"):
        log.info("%s non-null: %d / %d", c, app[c].notna().sum(), len(app))

    # 5) Bureau coverage
    n_with = bureau["SK_ID_CURR"].nunique()
    log.info("Bureau coverage: %d / %d (%.2f%%)", n_with, len(app), 100 * n_with / len(app))

    # 6) Numerical describe (only first 10 cols to keep output short)
    num_cols = app.select_dtypes(include=[np.number]).columns[:10]
    log.info("Numeric describe (first 10):\n%s", app[num_cols].describe().to_string())


if __name__ == "__main__":
    main()
