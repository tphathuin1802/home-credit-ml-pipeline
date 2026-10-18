# Credit Risk Scoring (Home Credit Default Risk)

Dự án mini — đồ án giữa kỳ. Mục tiêu: dự đoán xác suất vỡ nợ (`PD`) và chuyển
thành điểm tín dụng (300-850 kiểu FICO), có web app demo + Docker.

> Tài chính: `TARGET = 1` nghĩa là khách vỡ nợ trong vòng đời khoản vay. Tỉ lệ
> dương ~8% → bài toán mất cân bằng. Vì vậy ta dùng **AUC, Gini, KS** thay cho
> Accuracy.

## Cấu trúc

```
credit-risk-app/
├── data/raw/             # application_train.csv, bureau.csv, ... (không commit)
├── data/processed/       # cache feature engineering
├── notebooks/            # 01_eda.ipynb, 02_modeling.ipynb
├── src/
│   ├── config.py         # đường dẫn, seed, SAMPLE_ROWS, scorecard
│   ├── download_data.py  # tải Kaggle bằng kagglehub
│   ├── features.py       # làm sạch + feature engineering (GĐ 2)
│   ├── train.py          # train + đánh giá (GĐ 3)
│   ├── evaluate.py       # AUC, Gini, KS, ROC, calibration (GĐ 3)
│   └── predict.py        # load_artifacts / score_customer / what_if (GĐ 4)
├── app/main.py           # Streamlit 3 tab (GĐ 5)
├── model/                # model.joblib, metrics.json, defaults.json, *.png
├── tests/                # test_features.py, test_predict.py (GĐ 6)
├── requirements.txt
├── requirements-app.txt
├── Dockerfile
└── README.md
```

## Lộ trình triển khai

1. ✅ Khung repo + config + download + ignore
2. ✅ EDA + `features.py` (clean + ratios + bureau aggregate)
3. ✅ `train.py` + `evaluate.py` (Logistic vs LightGBM, 70/15/15 split, calibration tự động)
4. ⏳ Calibration + scorecard + SHAP + `predict.py` + `defaults.json`
5. ⏳ `app/main.py` (3 tab)
6. ⏳ Dockerfile + tests + README đầy đủ
7. ⏳ (Tuỳ chọn) FastAPI + docker-compose

## Kết quả nhanh (sample 100k, seed=42)

| Model | Test AUC | Test KS | Test Brier | Note |
|---|---|---|---|---|
| Logistic | 0.7591 | 0.391 | 0.067 | baseline |
| LightGBM | **0.7682** | **0.409** | **0.067** | best, early-stop iter=271 |

Calibration tự nhiên đã đạt (Brier 0.067, ECE 0.005 < ngưỡng 0.05) → không cần fit thêm.
Để tái lập: `python -X utf8 -m src.train` (khoảng 60s trên 100k).

## Bắt đầu

```bash
# 1. Tạo venv và cài deps
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 2. Đặt Kaggle credentials
copy .env.example .env          # sửa username/key

# 3. Tải dữ liệu (~2.5 GB)
python -m src.download_data
```

Dữ liệu đã có sẵn trong `data/raw/` thì bỏ qua bước 3.
