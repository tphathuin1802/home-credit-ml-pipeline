"""Local-only loader cho application_train_sample.csv (5K rows, 2.7MB).

File duoc commit san trong repo (data/raw/application_train_sample.csv),
nen chi can doc truc tiep tu disk. Khi deploy len Streamlit Cloud, file
nay cung duoc pull theo git nen khong can download runtime.

Public API:
    get_sample_csv_path()  -> Path
    get_sample_df()        -> pd.DataFrame
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src import config

logger = logging.getLogger(__name__)

# Local CSV (committed to git, present on every environment incl. Cloud).
_LOCAL_PATH = config.DATA_RAW / "application_train_sample.csv"


def get_sample_csv_path() -> Path:
    """Tra ve Path toi sample CSV local.

    Raises:
        FileNotFoundError: neu file khong ton tai tren disk.
    """
    if not _LOCAL_PATH.exists():
        raise FileNotFoundError(
            f"Missing required file: {_LOCAL_PATH}. "
            "Run `git checkout HEAD -- data/raw/application_train_sample.csv` "
            "or re-clone the repo."
        )
    return _LOCAL_PATH


def get_sample_df(nrows: int | None = None) -> pd.DataFrame:
    """Doc sample CSV thanh DataFrame.

    Args:
        nrows: so dong doc (None = het file). Mac dinh None.

    Returns:
        DataFrame. Raises FileNotFoundError neu khong co file.
    """
    return pd.read_csv(get_sample_csv_path(), nrows=nrows)


__all__ = [
    "get_sample_csv_path",
    "get_sample_df",
]
