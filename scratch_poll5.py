import time, pathlib, sys
log = pathlib.Path(r"C:\Dev\home-credit-default-risk\logs_train_v6.log")
prev = 0
print("Polling training v6...")
for i in range(120):  # 20 min max
    time.sleep(10)
    if not log.exists():
        print(f"not found"); break
    size = log.stat().st_size
    delta = size - prev
    prev = size
    with open(log, "r", encoding="utf-8", errors="replace") as f:
        try:
            f.seek(0, 2); pos = max(0, f.tell() - 1500); f.seek(pos)
            tail = f.read()
        except Exception:
            tail = ""
    last = tail.splitlines()[-1] if tail.strip() else ""
    print(f"[{(i+1)*10:>4}s] {size:>7}B d={delta:>5} | {last[:100]}", flush=True)
    if "Tong thoi gian" in tail or "T\u1ed5ng th\u1eddi gian" in tail or "Saving model" in tail[-500:]:
        print("\n=== DONE ==="); print(tail[-3000:]); break
    if ("MemoryError" in tail[-1500:] or "LightGBMError" in tail[-1500:] or "bad allocation" in tail[-1500:]) and "Traceback" in tail[-2000:]:
        print("\n=== FAILED ==="); print(tail[-2000:]); break
print("END")
