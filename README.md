# 🏦 Home Credit Default Risk

> **End-to-end ML pipeline** — từ 7 bảng dữ liệu thô → model xác suất vỡ nợ (PD) → điểm tín dụng (scorecard) → web app Streamlit có thể deploy.

![Streamlit — Predict Tab](assets/predict_tab.png)

---

## 🎯 Một câu — dự án làm gì?

**Score mỗi đơn đăng ký Home Credit: khách này có trả nợ không?**  
Pipeline chuẩn hóa dữ liệu 307k hồ sơ, huấn luyện LightGBM + Isotonic Calibration, và trả về **PD (0–1) + Credit Score (0–1000) + Risk Band (A–E)**.

---

## 📊 Kết quả nổi bật

| Metric | Giá trị |
|---|---|
| **AUC** | **0.758** |
| **Gini** | **0.516** |
| **KS Statistic** | **0.375** |
| **Recall @ τ=0.05** | **86.2%** |
| **Features** | **301** |
| **Default Rate** | **8.0%** |

> Baseline "luôn đoán không vỡ nợ" đã đúng 92% → Accuracy vô nghĩa.  
> **AUC 0.758** nghĩa là model phân tách tốt giữa defaulter và non-defaulter.

---

## ⚡ Demo nhanh

```
# Clone & chạy web app ngay lập tức
git clone https://github.com/phat/home-credit-default-risk.git
cd home-credit-default-risk

pip install -r requirements-app.txt
streamlit run app/streamlit_app.py
```

> App đã load sẵn trained model từ `model/`.  
> Không cần tải dữ liệu Kaggle để demo.

---

## 🖥️ Web App — 4 Tabs

| Tab | Nội dung |
|---|---|
| **Overview** | Giới thiệu dataset, phân bố TARGET, kiến trúc pipeline |
| **EDA** | Biểu đồ interactive: EXT_SOURCE, income, age theo TARGET |
| **Predict** | Nhập hồ sơ khách → PD + Score + Risk Band ngay lập tức |
| **Performance** | Bảng metrics, ROC / PR / KS / Calibration curves, Feature Importance |

### 📈 Performance Dashboard
![Performance Dashboard](assets/performance.png)

### 🔮 Predict Tab — Live Scoring
![Predict Tab](assets/predict_tab.png)

---

## 🔬 Methodology

### Data Pipeline (7 bảng → 301 features)

```
application_train.csv      ← master table + TARGET (307,511 rows)
         │
         ├── bureau                   (1.7M) → BUR_ACTIVE_CNT, BUR_DEBT_RATIO …
         ├── bureau_balance           (27.3M) → monthly status aggregation
         ├── previous_application     (1.7M) → PREV_AMT_SUM, PREV_APPROVE_RATE …
         ├── installments_payments    (13.6M) → INST_PAY_RATIO, INST_LATE_7D_SUM …
         ├── POS_CASH_balance        (10.0M) → POS_UTIL_MEAN, POS_CNT …
         └── credit_card_balance      (3.8M) → CC_UTIL_MEAN …
```

### Feature Engineering Blocks

| Block | Features |
|---|---|
| **Application Cleaning** | `AGE_YEARS`, `EMPLOYED_YEARS`, `CREDIT_TERM`, `EXT_SOURCE_MEAN/STD/PROD` |
| **Bureau Aggregation** | `BUR_ACTIVE_CNT`, `BUR_OVERDUE_CNT`, `BUR_DEBT_RATIO`, `HAS_BUREAU` |
| **Previous Apps + Installments** | `PREV_APPROVE_RATE`, `INST_LATE_7D_SUM`, `PREV_CNT_PAYMENT_MEAN` |
| **POS + Credit Card** | `POS_UTIL_MEAN`, `CC_UTIL_MEAN` |

### Modeling Pipeline

```
Train / Valid / Test  (70 / 15 / 15)  ← stratified split, seed=42
        │
        ▼
ColumnTransformer
  ├─ Median imputation (numeric)
  ├─ Most-frequent + one-hot (categorical)
  └─ StandardScaler (numeric)
        │
        ▼
┌──────────────────┬──────────────────┐
│  Logistic Reg   │  LightGBM (Optuna) │
│  baseline        │  n_est=205, lr=0.047│
│  class_weight    │  num_leaves=53      │
│  = balanced      │  early-stop 15 rounds│
└──────────────────┴──────────────────┘
        │
        ▼
Isotonic Regression (calibration)
  Brier: 0.0677 → 0.0678
  Recall @ τ=0.05: 86.2%
```

### Scorecard Formula (Siddiqui 2013)

```
score(PD) = 712.88 − 28.85 · ln( PD / (1 − PD) )
```

| Band | Score Range | Avg PD | Empirical Default |
|---|---|---|---|
| **A** (Low risk) | 760–1000 | 1.79% | 1.92% |
| **B** (Acceptable) | 640–760 | 4.67% | 5.02% |
| **C** (Watch-list) | 480–640 | 8.47% | 8.70% |
| **D** (Sub-standard) | 360–480 | 14.89% | 14.84% |
| **E** (High risk) | 0–360 | 31.59% | 30.04% |

> Empirical default rate tăng đều qua các band → scorecard well-calibrated.

---

## 🧪 Full Model Comparison (Test Set, n = 7,500)

| Model | AUC | Gini | KS | Brier | PR-AUC | Recall | Precision |
|---|---:|---:|---:|---:|---:|---:|---:|
| Logistic | 0.7452 | 0.4904 | 0.3689 | 0.0684 | 0.2350 | 0.7927 | 0.1310 |
| Logistic_balanced | 0.7412 | 0.4823 | 0.3626 | 0.1940 | 0.2288 | 1.0000 | 0.0831 |
| **LightGBM** | **0.7594** | **0.5188** | **0.3858** | **0.0677** | **0.2365** | 0.8375 | 0.1329 |
| LightGBM_calibrated ✓ | 0.7582 | 0.5164 | 0.3751 | 0.0678 | 0.2282 | **0.8624** | 0.1282 |

> **Selected for deployment**: LightGBM + Isotonic Calibration.  
> Trade-off: giảm chút AUC để đổi lấy **recall 86.2%** — bắt được hơn 5/6 defaulters.

---

## 🗂️ Cấu trúc Project

```
home-credit-default-risk/
├── data/
│   ├── raw/                    # Kaggle data (not committed)
│   └── processed/              # Cached feature cache
├── notebooks/
│   └── home_credit_pipeline.ipynb   # E2E pipeline, tất cả cells
├── src/
│   ├── config.py               # Paths, seeds, scorecard params
│   ├── download_data.py        # Kaggle download via kagglehub
│   ├── features.py             # Cleaning + aggregation
│   ├── train.py                # Model training + Optuna tuning
│   ├── evaluate.py             # AUC, Gini, KS, ROC, calibration
│   └── predict.py              # load_artifacts, predict_one, score_customer
├── app/
│   └── streamlit_app.py        # 4-tab web app
├── model/                      # ← Artifacts sau khi train
│   ├── model.joblib            # Pipeline + LightGBM + Isotonic
│   ├── metrics.json           # Full metrics all models
│   ├── defaults.json          # Threshold + scorecard formula
│   ├── model_card.json        # Model card (metadata, risk bands)
│   ├── predictions_test.csv   # Test set predictions
│   └── *.png                  # ROC, PR, KS, calibration, importance
├── powerbi/                    # Power BI dashboard (.pbix + screenshots)
├── slides/                     # Pitch deck (HTML → PDF)
│   └── assets/                 # Chart images embedded in deck
├── tests/
│   ├── test_features.py        # Unit tests feature engineering
│   └── test_predict.py        # Integration tests predict.py
├── Dockerfile
├── requirements.txt            # Full ML stack (train)
├── requirements-app.txt        # Streamlit only (deploy)
└── README.md
```

---

## 🚀 Bắt đầu

### 1. Setup

```bash
git clone https://github.com/phat/home-credit-default-risk.git
cd home-credit-default-risk

python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # macOS / Linux

pip install -r requirements.txt
```

### 2. Tải dữ liệu

```bash
# Đặt Kaggle credentials
cp .env.example .env    # sửa KAGGLE_USERNAME / KAGGLE_KEY

python -m src.download_data    # ~2.5 GB
```

> Dữ liệu đã có trong `data/raw/` → bỏ qua bước này.

### 3. Train model (60–120s trên subsample)

```bash
python -m src.train
```

Output: `model/model.joblib`, `model/metrics.json`, `model/*.png`

### 4. Chạy web app

```bash
pip install -r requirements-app.txt
streamlit run app/streamlit_app.py
```

### 5. Docker

```bash
docker build -t hc-credit-risk .
docker run -p 8501:8501 hc-credit-risk
```

---

## 🔑 Key Design Decisions

| Decision | Lý do |
|---|---|
| **LightGBM thay vì Neural Net** | Tabular data + small dataset → GBM consistently wins |
| **Isotonic thay vì Platt** | Non-parametric, handles non-linear miscalibration |
| **Recall-oriented threshold** | FN (missed defaulter) >> FP (false alarm) trong credit risk |
| **301 features** | Aggressive aggregation từ 7 bảng, đủ signal cho model |
| **Subsample 12k** | Fits local compute; full 307k run expected to lift AUC |

---

## ⚠️ Limitations & Future Work

- **Sample size** — chạy trên 12k-row subsample; full 307k sẽ cải thiện AUC
- **Drift monitoring** — PSI / KS drift tracking cần thiết khi portfolio thay đổi
- **Fairness audit** — disaggregated metrics theo giới tính, độ tuổi trước khi deploy production
- **Rejected inference** — training chỉ gồm approved loans; cần extension cho inference population

### Roadmap
- [ ] TabNet / FT-Transformer thay LightGBM
- [ ] LSTM/Transformer trên installment payment sequences
- [ ] Reject inference để close selection-bias gap
- [ ] Quarterly calibration refresh

---

## 📜 License

MIT — free to use, modify, and deploy.

---

*Built with: Python · LightGBM · scikit-learn · Streamlit · Docker · Power BI*
