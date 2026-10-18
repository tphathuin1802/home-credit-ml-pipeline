"""Download the Home Credit Default Risk dataset via the kagglehub API.

Tài chính/Math:
- Tập dữ liệu public trên Kaggle (~2.5 GB nén). Dùng ``kagglehub`` (API mới
  của Kaggle) sẽ tự quản lý cache, tránh tải lại nhiều lần.
- Trước khi chạy cần đặt biến môi trường ``KAGGLE_USERNAME`` và
  ``KAGGLE_KEY`` (lấy từ https://www.kaggle.com/settings -> "Create New Token").

Usage::

    python -m src.download_data            # tải mặc định
    python -m src.download_data --force    # xóa cache rồi tải lại
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path

from src.config import DATA_RAW

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger(__name__)

COMPETITION_SLUG = "home-credit-default-risk"


def download(force: bool = False) -> Path:
    """Tải (hoặc lấy từ cache) toàn bộ competition về ``data/raw``.

    Parameters
    ----------
    force : bool
        Nếu ``True``, xóa cache hiện tại của kagglehub rồi tải lại.

    Returns
    -------
    Path
        Đường dẫn thư mục chứa các file CSV.
    """
    if force:
        cache = Path.home() / ".cache" / "kagglehub"
        if cache.exists():
            logger.info("Xóa cache kagglehub: %s", cache)
            shutil.rmtree(cache, ignore_errors=True)

    try:
        import kagglehub  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "Chưa cài kagglehub. Chạy: pip install kagglehub"
        ) from exc

    # Đảm bảo biến môi trường đã có (kagglehub sẽ tự báo lỗi nếu thiếu).
    logger.info("Bắt đầu tải competition '%s' ...", COMPETITION_SLUG)
    path = Path(kagglehub.competition_download(COMPETITION_SLUG))
    logger.info("Đã tải về: %s", path)

    # Copy/symlink các CSV cần thiết vào data/raw (giữ tên gốc).
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    required = [
        "application_train.csv",
        "application_test.csv",
        "bureau.csv",
        "HomeCredit_columns_description.csv",
    ]
    for fname in required:
        src = path / fname
        dst = DATA_RAW / fname
        if not src.exists():
            logger.warning("Thiếu file %s trong cache Kaggle - bỏ qua.", src)
            continue
        if dst.exists():
            logger.info("Đã có %s - bỏ qua.", dst.name)
            continue
        shutil.copy2(src, dst)
        logger.info("Copy %s -> %s", src.name, dst)

    logger.info("Hoàn tất. Dữ liệu ở: %s", DATA_RAW)
    return DATA_RAW


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Xóa cache kagglehub rồi tải lại từ đầu.",
    )
    args = parser.parse_args(argv)
    download(force=args.force)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
