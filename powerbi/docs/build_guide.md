# 🏠 Home Credit Default Risk — Power BI Dashboard

Power BI dashboard for the Home Credit Default Risk project. Đầy đủ 5 page, theme
trắng-đỏ Home Credit, font Segoe UI / Inter.

---

## 📁 Cấu trúc thư mục

```
powerbi/
├── HomeCreditRiskDashboard.pbit      ← Mở file này trong Power BI Desktop
├── data/                             ← 6 file CSV (auto-load khi mở .pbit)
│   ├── fact_predictions.csv          ← 7,500 khách hàng test
│   ├── fact_feature_importance.csv   ← 30 features
│   ├── dim_models.csv                ← 4 mô hình so sánh
│   ├── dim_risk_bands.csv            ← 3 risk band (Thấp/TB/Cao)
│   ├── dim_segments.csv              ← 16 cut points (Age/Income/PD)
│   └── fact_thresholds.csv           ← 30 threshold points
├── theme/
│   └── home_credit_theme.json        ← Theme trắng-đỏ
├── docs/
│   ├── dax_measures.dax              ← 25+ DAX measures sẵn sàng
│   ├── build_guide.md                ← Hướng dẫn build từng page (file này)
│   └── dashboard_spec.md             ← Spec chuẩn BA
├── export_powerbi_data.py            ← Script xuất data từ model
└── build_pbit.py                     ← Script build file .pbit
```

---

## 🚀 Hướng dẫn sử dụng (5 bước)

### Bước 1 — Cài Power BI Desktop
Tải miễn phí: <https://powerbi.microsoft.com/desktop/>

### Bước 2 — Export data
```bash
cd C:\Dev\home-credit-default-risk
python powerbi\export_powerbi_data.py
```
Sẽ sinh ra 6 file CSV trong `powerbi/data/`.

### Bước 3 — Mở template
Double-click `powerbi\HomeCreditRiskDashboard.pbit`.
Power BI sẽ mở + nhắc chọn đường dẫn data. Trỏ vào `powerbi/data/`.

### Bước 4 — Apply theme
`View` → `Themes` → `Browse for themes` → chọn
`powerbi/theme/home_credit_theme.json`.

### Bước 5 — Build visuals
Xem chi tiết bên dưới. Tham chiếu 5 page theo chuẩn BA.

---

## 📐 Layout 5 page (1.280 × 720 px, lưới 8px)

```
┌─────────────────────────────────────────────────────────────┐
│ Page 1 · EXECUTIVE SUMMARY                                  │
│  [KPI:Total] [KPI:Default%] [KPI:Avg PD] [KPI:AUC] [KPI:Score]│
│  ┌────────────────┐  ┌──────────────────────────────────┐  │
│  │ Risk Band Donut│  │ Score Histogram (300-850)        │  │
│  └────────────────┘  └──────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Top 10 Highest-Risk Customers (Table)               │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│ Page 2 · MODEL PERFORMANCE                                 │
│  [KPI:AUC] [KPI:Gini] [KPI:KS] [KPI:Brier] [KPI:F1]       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Model Comparison Table (Top: AUC bar chart)         │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌────────────────┐  ┌────────────────┐                   │
│  │ Precision/Recall by Threshold (Line) │ Confusion   │   │
│  └────────────────┘  └────────────────┘                   │
├─────────────────────────────────────────────────────────────┤
│ Page 3 · RISK SEGMENTATION                                 │
│  [KPI:High] [KPI:Medium] [KPI:Low] [KPI:High% Share]      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Risk Band Bar Chart (Red gradient)                  │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌────────────────┐  ┌────────────────┐                   │
│  │ Bad Rate by Risk Band │ Customers by Score Bucket    │   │
│  └────────────────┘  └────────────────┘                   │
├─────────────────────────────────────────────────────────────┤
│ Page 4 · FEATURE IMPORTANCE                                │
│  [KPI:Top 1 Feature] [KPI:Total Features]                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Top 20 Features Horizontal Bar (Home Credit Red)    │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Feature Group Donut (num_/cat_)                     │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│ Page 5 · PORTFOLIO DRILL-DOWN                              │
│  [KPI:Total] [KPI:EL Rate] [KPI:Acc] [KPI:Recall] [KPI:Prec]│
│  ┌──────────────────┐  ┌──────────────────────────────┐  │
│  │ PD Distribution  │  │ Customer Detail Table (with   │  │
│  │ (Histogram)      │  │ drill-through)                │  │
│  └──────────────────┘  └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Bước 5: Hướng dẫn build từng visual

### Page 1 — Executive Summary

1. **Insert** → **Card** (KPI) → kéo `fact_predictions` vào `Fields`.
   - Đổi tên thành `Total Customers` (đã có sẵn trong DAX).
2. Copy/paste 4 card còn lại theo cùng pattern với measure:
   - `Default Rate %`, `Average Probability of Default %`, `Top Model AUC`,
     `Average Credit Score`.
3. **Insert** → **Donut chart**
   - Legend: `fact_predictions[risk_band]`
   - Values: Count of `customer_id`
   - Format data colors:
     - `Cao` → `#ED1C24`
     - `Trung bình` → `#F5A623`
     - `Thấp` → `#3FAE5C`
4. **Insert** → **Clustered column chart**
   - X-axis: bin `score` (tạo bins 300, 400, 500, 600, 700, 800, 850)
   - Y-axis: count of `customer_id`
5. **Insert** → **Table** với 5 cột:
   `customer_id`, `score`, `pd_calibrated`, `risk_band`, `actual_default`
   - Filter: `Top 10 by pd_calibrated` (sort desc)
6. **Format** → **Title**: "EXECUTIVE SUMMARY · 30,000 CUSTOMERS"
   - Font: Segoe UI Semibold, 16pt, màu `#1A1A1A`
   - Background: `#FFFFFF`

### Page 2 — Model Performance

1. 5 KPI cards tương tự Page 1, dùng measures: `Top Model AUC`,
   `Top Model Gini`, `Top Model KS`, `Top Model Brier Score`, `F1 Score`.
2. **Insert** → **Table** — bind to `dim_models`:
   - Columns: `model_name`, `auc`, `gini`, `ks`, `brier`, `f1`, `recall`,
     `precision`, `is_recommended` (icon check cho recommended).
   - Conditional formatting: cột `auc` → Data bars màu `#ED1C24`.
3. **Insert** → **Line chart** (Precision-Recall vs Threshold):
   - Axis: `fact_thresholds[threshold]`
   - Values: cần 2 measures mới (xem `dax_measures.dax` mục 3).

### Page 3 — Risk Segmentation

1. 4 KPI cards: `High Risk Customers`, `Medium Risk Customers`,
   `Low Risk Customers`, `High Risk Share %`.
2. **Insert** → **Clustered bar chart**:
   - Y-axis: `fact_predictions[risk_band]`
   - X-axis: count of `customer_id`
   - Data colors: `#ED1C24` (Cao), `#F5A623` (TB), `#3FAE5C` (Thấp)
3. **Insert** → **Line chart** (Bad Rate by Risk Band):
   - Axis: `risk_band`
   - Values: measure `Bad Rate by Risk Band` (đã có trong DAX)
4. **Insert** → **Histogram** (Score buckets):
   - Bind `score` column → tạo bin type "Bin", size 50.

### Page 4 — Feature Importance

1. 2 KPI cards: `COUNTROWS(fact_feature_importance)` (Total Features) +
   `FIRSTNONBLANK(fact_feature_importance[feature], 1)` (Top 1).
2. **Insert** → **Clustered bar chart** (horizontal):
   - Y-axis: `feature_short` (sort by `importance` desc, top 20)
   - X-axis: `importance`
   - Color: `#ED1C24`
3. **Insert** → **Donut chart**:
   - Legend: `feature_group`
   - Values: sum of `importance`

### Page 5 — Portfolio Drill-down

1. 5 KPI cards: `Total Customers`, `Expected Loss Rate %`, `Accuracy`,
   `Recall (Sensitivity)`, `Precision`.
2. **Insert** → **Histogram** (PD Distribution):
   - Bind `pd_calibrated`, bin size 0.02.
3. **Insert** → **Table** (Customer detail với slicer):
   - Columns: `customer_id`, `score`, `pd_calibrated`, `risk_band`,
     `rating_class`, `actual_default`, `predicted_default`.
   - **Insert** → **Slicer** (left side):
     - Field: `risk_band` (multi-select)
     - Field: `pd_bucket`
     - Style: Vertical list với background `#FFF5F5`.

---

## 🎨 Color codes (Home Credit palette)

| Mã         | Màu               | Sử dụng cho                              |
|------------|-------------------|------------------------------------------|
| `#ED1C24`  | Home Credit Red   | KPI chính, primary, brand                |
| `#B11226`  | Dark Red          | Highest risk                              |
| `#F5A623`  | Orange            | Medium risk, cảnh báo                    |
| `#3FAE5C`  | Green             | Low risk, success                         |
| `#1A1A1A`  | Black             | Text, headings                            |
| `#6B6B6B`  | Gray              | Secondary text                            |
| `#FFF5F5`  | Light red bg      | Highlight rows, slicer                    |
| `#FFFFFF`  | White             | Background chính                          |

---

## 🔤 Font chuẩn

- **Headings:** Segoe UI Semibold, 16pt
- **Body:** Segoe UI, 10–12pt
- **KPI values:** Segoe UI Light, 28pt (màu `#ED1C24`)
- **Tables:** Segoe UI, 9pt

---

## 📊 25+ DAX measures (xem `dax_measures.dax`)

| Nhóm               | Measures                                                                   |
|--------------------|----------------------------------------------------------------------------|
| Core KPI           | Total Customers, Default Rate, Predicted Default Rate, Avg PD, Avg Score   |
| Model Performance  | Top Model AUC, Gini, KS, Brier                                              |
| Confusion Matrix   | TP, FP, FN, TN, Precision, Recall, F1, Accuracy                            |
| Risk Segmentation  | High/Med/Low Risk Count, High Risk Share, Bad Rate by Band                 |
| Expected Loss      | Total Expected Loss, EL Rate, EL per Customer                               |
| Drill-through      | Selected Customer, Selected PD, Selected Score                             |
| Conditional fmt    | PD Color, Score Color                                                       |

---

## 💡 Tips cho BA khi trình bày

1. **Mở đầu bằng Page 1 (Executive Summary)** — leadership chỉ cần 5 KPI + 1 donut.
2. **Khi có câu hỏi "model nào tốt nhất?"** → nhảy sang Page 2.
3. **Khi hỏi "phân khúc nào rủi ro nhất?"** → Page 3 (slicers để drill).
4. **Khi audit/shap explain** → Page 4 (top features).
5. **Khi cần customer-level** → Page 5 (drill-through).

---

## 🔄 Refresh data

Sau khi train model mới (`python src/train.py`), chạy:

```bash
python powerbi\export_powerbi_data.py
```

Trong Power BI Desktop: `Home` → `Refresh`.

---

## 🛟 Troubleshooting

| Lỗi                                | Cách sửa                                              |
|------------------------------------|--------------------------------------------------------|
| "Cannot find file xxx.csv"        | `Transform Data` → `Data source settings` → trỏ lại `powerbi/data/` |
| Theme không apply                  | `View` → `Themes` → `Browse for themes` → chọn lại   |
| Slicer trống                      | Kiểm tra relationship (bảng fact ↔ dim)                |
| PD hiển thị 0.07 thay vì 7%      | Modeling → column → Format: Percentage                 |
