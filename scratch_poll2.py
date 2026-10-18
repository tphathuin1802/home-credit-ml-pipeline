import time
import os
path = r"C:\Users\phath\.cursor\projects\c-Dev-home-credit-default-risk\terminals\940112.txt"
prev = 0
for i in range(80):
    time.sleep(20)
    if not os.path.exists(path):
        print("no file")
        break
    size = os.path.getsize(path)
    print(f"[{(i+1)*20:>4}s] size={size:>8} delta={size-prev:>7}")
    prev = size
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        try:
            f.seek(0, 2)
            pos = max(0, f.tell() - 6000)
            f.seek(pos)
            tail = f.read()
        except Exception as e:
            tail = f"err: {e}"
    if "Tong thoi gian" in tail or "T\u1ed5ng th\u1eddi gian" in tail or "Traceback" in tail[-3000:]:
        print("=== DONE ===")
        print(tail[-4000:])
        break
