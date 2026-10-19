# 📊 Home Credit Default Risk — Power BI Dashboard

> **Dashboard BA chuẩn** cho dự án Home Credit Default Risk. 5 page, theme
> trắng-đỏ Home Credit, font Segoe UI, ~25 DAX measures, data export tự
> động từ `model/metrics.json` + `model/predictions_test.csv`.

---

## 🚀 Quick start (3 bước)

### 1. Xem preview ngay trên browser (không cần Power BI)
```bash
start powerbi\preview.html          # Windows
# hoặc open powerbi/preview.html    # macOS
```
Mở ra 5 page dashboard với data thật, KPI, donut, histogram, table.

### 2. Export data (nếu vừa train model mới)
```bash
python powerbi\export_powerbi_data.py
```
Tạo 6 file CSV trong `powerbi/data/`.

### 3. Mở trong Power BI Desktop
1. Tải Power BI Desktop miễn phí: <https://powerbi.microsoft.com/desktop/>
2. Double-click `powerbi\HomeCreditRiskDashboard.pbit`
3. Power BI sẽ nhắc chọn data source → trỏ vào `powerbi\data\`
4. `View` → `Themes` → `Browse` → chọn `powerbi\theme\home_credit_theme.json`
5. Mở `powerbi\docs\build_guide.md` → làm theo hướng dẫn từng bước

---

## 📁 Cấu trúc

```
powerbi/
├── HomeCreditRiskDashboard.pbit      ← Power BI template (mở file này)
├── preview.html                       ← HTML preview (xem ngay)
├── data/                              ← 6 CSV files
├── theme/
│   └── home_credit_theme.json        ← Theme trắng-đỏ
├── docs/
│   ├── dax_measures.dax              ← 25+ DAX measures
│   ├── build_guide.md                ← Hướng dẫn build từng visual
│   └── dashboard_spec.md             ← Spec chuẩn BA
├── export_powerbi_data.py            ← Export data từ model
├── build_pbit.py                     ← Build .pbit file
└── build_preview.py                  ← Build HTML preview
```

---

## 🎨 Theme (Home Credit brand)

| Color   | Hex       | Dùng cho                |
|---------|-----------|-------------------------|
| 🔴 Red  | `#ED1C24` | Primary, KPI, brand     |
| 🟥 Dark | `#B11226` | Highest risk            |
| 🟧 Org  | `#F5A623` | Medium risk             |
| 🟢 Grn  | `#3FAE5C` | Low risk                |
| ⚫ Dk   | `#1A1A1A` | Text                    |
| ⚪ Gy   | `#6B6B6B` | Subtext                 |
| ⬜ Wht  | `#FFFFFF` | Background              |
| 🌸 Lt   | `#FFF5F5` | Highlight bg            |

Font: **Segoe UI** (headings: Semibold, KPI: Light 28pt).

---

## 📄 5 Page

| #  | Page                  | For                  | Highlights                                  |
|----|----------------------|----------------------|---------------------------------------------|
| 1  | Executive Summary    | CEO, CRO             | 5 KPI + Risk donut + Score hist + Top 10    |
| 2  | Model Performance    | Data Science Lead    | 4 model compare + Confusion matrix          |
| 3  | Risk Segmentation    | Risk Manager         | 3 risk band + Bad rate by band              |
| 4  | Feature Importance   | Model Validator      | Top 20 features SHAP gain                   |
| 5  | Portfolio Drill-down | Credit Officer       | PD distribution + Customer table            |

---

## 📈 KPIs (chuẩn Basel II)

| KPI              | Value    | Status        |
|------------------|----------|---------------|
| Default Rate     | 8.04%    | ✓             |
| AUC              | 0.7582   | ✓ (≥ 0.75)    |
| Gini             | 0.5164   | ✓ (≥ 0.50)    |
| KS               | 0.3751   | ✓ (≥ 0.30)    |
| Brier            | 0.0678   | ✓ (≤ 0.10)    |
| Avg PD (cal)     | 7.45%    | —             |
| Avg Credit Score | ~600     | —             |

---

## 🔄 Refresh workflow

```bash
# Sau khi train model mới
python src/train.py
python powerbi\export_powerbi_data.py
# Trong Power BI Desktop: Home > Refresh
```

Hoặc auto-refresh với Power BI Service + Gateway.

---

## 🛟 Troubleshooting

| Lỗi                              | Cách sửa                                              |
|----------------------------------|--------------------------------------------------------|
| "Cannot find file xxx.csv"      | Transform Data → Data source settings → trỏ lại      |
| Theme không apply                | View → Themes → Browse → chọn `home_credit_theme.json` |
| Slicer trống                    | Model view → check relationships                       |
| PD hiển thị 0.07 thay vì 7%    | Modeling → column → Format: Percentage                 |

---

## 📚 Tài liệu chi tiết

- [`docs/build_guide.md`](docs/build_guide.md) — Hướng dẫn build từng visual (từng bước)
- [`docs/dashboard_spec.md`](docs/dashboard_spec.md) — Spec chuẩn BA (KPIs, design system)
- [`docs/dax_measures.dax`](docs/dax_measures.dax) — 25+ DAX measures sẵn sàng dùng
- `../model/metrics.json` — Model metrics nguồn
- `../model/predictions_test.csv` — Predictions nguồn
