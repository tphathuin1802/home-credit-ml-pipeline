"""Helper: push application_train.csv qua Git LFS len GitHub.

Huong dan:
1. Tai dataset tu Kaggle:
   https://www.kaggle.com/c/home-credit-default-risk/data
   (can dang nhap Kaggle + accept rules)
2. Giai nen, copy application_train.csv vao:
   data/raw/application_train.csv
3. Chay script nay trong Git Bash / PowerShell:

   python scripts/push_data_lfs.py

   Script se:
   - Track application_train.csv qua Git LFS
   - Commit + push len origin main
   - (Streamlit Cloud se auto-pull LFS file)
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "raw" / "application_train.csv"
LFS_KEEP_FILE = ROOT / "data" / "raw" / ".gitattributes"


def main() -> None:
    if not CSV_PATH.exists():
        print(f"❌ Khong tim thay {CSV_PATH}")
        print("   Tai file tu Kaggle roi dat vao day truoc.")
        sys.exit(1)

    size_mb = CSV_PATH.stat().st_size / 1e6
    print(f"✅ Tim thay file: {size_mb:.1f} MB")

    # Track qua LFS (idempotent)
    print("🔧 Track file qua Git LFS...")
    subprocess.run(["git", "lfs", "track", "data/raw/application_train.csv"],
                   cwd=ROOT, check=True)

    # Add + commit + push
    print("📦 Git add...")
    subprocess.run(["git", "add", str(CSV_PATH.relative_to(ROOT))], cwd=ROOT, check=True)
    subprocess.run(["git", "add", ".gitattributes"], cwd=ROOT, check=False)

    print("💾 Commit...")
    subprocess.run(["git", "commit", "-m", "data: add application_train.csv via LFS"],
                   cwd=ROOT, check=False)

    print("⬆️  Push to origin...")
    result = subprocess.run(["git", "push", "origin", "main"], cwd=ROOT)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
