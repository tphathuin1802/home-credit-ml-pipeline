"""Lazy loader cho application_train_sample.csv (5K rows, 2.7MB).

Motivation: repo khong commit file CSV de giu repo nhe + tranh lo LFS.
App (Streamlit Cloud) tu download file tu GitHub raw URL va cache local
trong ``data/raw/`` de cac lan sau doc truc tiep tu disk.

Public API:
    get_sample_csv_path()  -> Path
    get_sample_df()        -> pd.DataFrame
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import pandas as pd

from src import config

logger = logging.getLogger(__name__)

# URL public cua sample CSV tren GitHub (raw content, khong can auth).
# Source: github.com/tphathuin1802/home-credit-ml-pipeline@main
GITHUB_RAW_URL = (
    "https://media.githubusercontent.com/media/"
    "tphathuin1802/home-credit-ml-pipeline/refs/heads/main/"
    "data/raw/application_train_sample.csv"
)

# Local cache file (se duoc tao khi user mo app tren cloud).
_LOCAL_PATH = config.DATA_RAW / "application_train_sample.csv"

# MD5 cua file goc (verify download dung version).
_EXPECTED_MD5: str | None = None  # None = skip check


def _md5(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for blk in iter(lambda: f.read(chunk), b""):
            h.update(blk)
    return h.hexdigest()


def _download_from_github(url: str, dest: Path) -> None:
    """Download CSV tu GitHub raw URL, hien thi tien trinh trong Streamlit."""
    import urllib.request

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")

    logger.info("Downloading %s -> %s", url, dest)
    with urllib.request.urlopen(url, timeout=60) as r, tmp.open("wb") as f:
        total = int(r.headers.get("Content-Length", 0))
        downloaded = 0
        chunk = 1 << 20  # 1 MB
        while True:
            buf = r.read(chunk)
            if not buf:
                break
            f.write(buf)
            downloaded += len(buf)
            if total:
                pct = downloaded * 100 // total
                logger.debug("Download progress: %d%%", pct)

    tmp.replace(dest)
    size_mb = dest.stat().st_size / 1e6
    logger.info("Downloaded %.2f MB to %s", size_mb, dest)


def get_sample_csv_path(*, force_download: bool = False) -> Path:
    """Tra ve Path toi sample CSV, download tu GitHub neu chua co local.

    Args:
        force_download: bat buoc download lai (bo qua cache + checksum).

    Returns:
        Path toi file CSV. Raises FileNotFoundError neu download that bai.
    """
    if _LOCAL_PATH.exists() and not force_download:
        if _EXPECTED_MD5 and _md5(_LOCAL_PATH) != _EXPECTED_MD5:
            logger.warning("Local sample CSV has unexpected MD5, re-downloading")
        else:
            return _LOCAL_PATH

    try:
        _download_from_github(GITHUB_RAW_URL, _LOCAL_PATH)
    except Exception as e:
        # Cleanup partial file
        if _LOCAL_PATH.with_suffix(".part").exists():
            _LOCAL_PATH.with_suffix(".part").unlink()
        raise FileNotFoundError(
            f"Khong the download sample CSV tu GitHub: {e}. "
            f"URL: {GITHUB_RAW_URL}"
        ) from e
    return _LOCAL_PATH


def get_sample_df(nrows: int | None = None) -> pd.DataFrame:
    """Doc sample CSV thanh DataFrame.

    Args:
        nrows: so dong doc (None = het file). Mac dinh None.

    Returns:
        DataFrame. Raises FileNotFoundError neu khong co file va download fail.
    """
    path = get_sample_csv_path()
    return pd.read_csv(path, nrows=nrows)


__all__ = [
    "GITHUB_RAW_URL",
    "get_sample_csv_path",
    "get_sample_df",
]
