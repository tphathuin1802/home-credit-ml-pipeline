import time, os
path = r"C:\Users\phath\.cursor\projects\c-Dev-home-credit-default-risk\terminals\918240.txt"
prev = 0
print("Waiting for training to complete...")
for i in range(100):  # up to ~33 min
    time.sleep(20)
    if not os.path.exists(path):
        print("File gone!")
        break
    size = os.path.getsize(path)
    delta = size - prev
    prev = size
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        f.seek(0, 2)
        pos = max(0, f.tell() - 3000)
        f.seek(pos)
        tail = f.read()
    # Extract just the last log line
    lines = [l for l in tail.splitlines() if l.strip()]
    last = lines[-1] if lines else ""
    print(f"[{(i+1)*20:>4}s] size={size:>8} delta={delta:>7}  {last[:100]}")
    if "Tong thoi gian" in tail or "T\u1ed5ng th\u1eddi gian" in tail or "Traceback" in tail[-2000:]:
        print("\n=== COMPLETED ===")
        print(tail[-5000:])
        break
    if "Exit code" in tail[-200:]:
        print("\n=== FAILED ===")
        print(tail[-3000:])
        break
