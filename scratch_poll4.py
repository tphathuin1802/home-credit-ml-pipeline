import time, os, sys
path = r"C:\Users\phath\.cursor\projects\c-Dev-home-credit-default-risk\terminals\450655.txt"
log_path = r"C:\c:\Dev\home-credit-default-risk\logs_train_v5.log"
# Use the actual log path
import pathlib
log_path = pathlib.Path(r"C:\Dev\home-credit-default-risk\logs_train_v5.log")
prev = 0
print("Waiting for training (max 12 min)...")
for i in range(72):  # 72 * 10s = 12 min
    time.sleep(10)
    if not log_path.exists():
        print(f"log not found at {log_path}")
        break
    size = log_path.stat().st_size
    delta = size - prev
    prev = size
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        try:
            f.seek(0, 2)
            pos = max(0, f.tell() - 2000)
            f.seek(pos)
            tail = f.read()
        except Exception:
            tail = ""
    lines = [l for l in tail.splitlines() if l.strip()]
    last = lines[-1] if lines else ""
    print(f"[{(i+1)*10:>4}s] size={size:>7} delta={delta:>5} | {last[:90]}")
    if "Tong thoi gian" in tail or "T\u1ed5ng th\u1eddi gian" in tail:
        print("\n=== COMPLETED ===")
        print(tail[-3000:])
        break
    if "Traceback" in tail[-2000:] and ("MemoryError" in tail[-1500:] or "LightGBMError" in tail[-1500:] or "bad allocation" in tail[-1500:]):
        print("\n=== FAILED (memory) ===")
        print(tail[-2000:])
        break
print("DONE")
