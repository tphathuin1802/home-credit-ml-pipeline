# 🚀 Streamlit Cloud deployment — troubleshooting

## Lỗi gốc

```
ModuleNotFoundError: No module named 'joblib'
File "/mount/src/home-credit-ml-pipeline/app/streamlit_app.py", line 24, in <module>
    import joblib
```

Nghĩa là: repo deploy trên Streamlit Cloud **thiếu `joblib` trong `requirements.txt`**.

## Fix đã áp dụng

Đã cập nhật các file sau trong repo của bạn:

### 1. `requirements.txt` — bộ dependencies cho Streamlit Cloud
- Chuyển từ pin chặt (`==`) sang pin lỏng (`>=`) để tránh resolver conflict
- Loại bỏ các package **không cần cho inference**:
  - `shap` — không dùng trong `app/streamlit_app.py`
  - `seaborn` — không dùng (chỉ dùng matplotlib)
  - `scipy` — không dùng trực tiếp
  - `kagglehub` — không cần (deploy, không phải training)
  - `pydantic` — không dùng
  - `pytest`, `pytest-cov` — không dùng
- **Giữ lại** các package bắt buộc: `numpy`, `pandas`, `scikit-learn`, `lightgbm`, `joblib`, `matplotlib`, `streamlit`

### 2. `.python-version`
Pin Python 3.11 — version ổn định nhất cho các gói trên.

## ✅ Checklist deploy

1. **Commit & push** cả 2 file:
   ```bash
   git add requirements.txt .python-version
   git commit -m "fix: requirements for Streamlit Cloud"
   git push origin main
   ```

2. **Vào Streamlit Cloud → app của bạn → "Reboot"** (không cần redeploy, chỉ reboot).

3. **Nếu vẫn lỗi**: mở tab **"Logs"** trong Streamlit Cloud và kiểm tra traceback.
   - Có thể thiếu `lightgbm` (build khá nặng, đôi khi bị cache miss). 
   - Nếu lỗi `libgomp.so.1 cannot open shared object`: cần thêm `packages.txt` với `libgomp1`.

## 🔍 Debug nhanh

Đã thêm file `debug_imports.py` ở root. Để chạy:

1. Trong Streamlit Cloud, set main file tạm thời là `debug_imports.py` (Settings → Main file path).
2. App sẽ hiển thị bảng versions của tất cả packages.
3. Nếu bất kỳ package nào thiếu, bạn sẽ thấy ngay.

Sau khi debug xong, set lại main file về `app/streamlit_app.py`.

## ⚙️ Cấu hình Streamlit Cloud chuẩn

| Setting | Value |
|---------|-------|
| **Repository** | `tphathuin1802/home-credit-ml-pipeline` |
| **Branch** | `main` |
| **Main file path** | `app/streamlit_app.py` |
| **Python version** | 3.11 (đọc từ `.python-version`) |

## 📦 Lỗi thường gặp & fix

| Lỗi | Nguyên nhân | Fix |
|-----|-------------|-----|
| `ModuleNotFoundError: No module named 'X'` | Thiếu trong requirements | Thêm vào `requirements.txt` |
| `libgomp.so.1: cannot open shared object` | Thiếu system lib cho lightgbm | Tạo `packages.txt` với `libgomp1` |
| `FileNotFoundError: model.joblib` | Model file chưa commit (do quá lớn hoặc .gitignore) | Dùng Git LFS hoặc load từ URL/S3 |
| `MemoryError` khi load model | Streamlit Cloud free tier giới hạn 1GB RAM | Giảm SAMPLE_ROWS hoặc upgrade |

## 🔧 Cần thiết `packages.txt`?

Nếu gặp lỗi `libgomp.so.1` (lightgbm cần), tạo file `packages.txt`:

```
libgomp1
```

Commit và push, Streamlit Cloud sẽ tự động cài system packages.
