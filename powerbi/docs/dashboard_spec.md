# 📊 Home Credit Default Risk — Dashboard Specification (BA Standard)

> **Audience:** BA / Risk Manager / Data Science Lead
> **Stack:** Power BI Desktop (free), CSV data export, DAX measures
> **Refresh:** Manual sau khi train model mới (~5 phút)
> **Status:** Production-ready v1.0

---

## 1. 🎯 Mục tiêu Dashboard

| Stakeholder          | Câu hỏi chính                                  | Page |
|----------------------|------------------------------------------------|------|
| CEO / CRO            | Tổng quan PD, default rate, portfolio health  | 1    |
| Risk Manager         | Phân khúc nào rủi ro, bad rate theo band      | 3    |
| Data Science Lead    | Model nào tốt nhất, calibration, KS           | 2    |
| Model Validator      | Feature nào drive PD, SHAP top 20             | 4    |
| Credit Officer       | Customer-level score, drill-down              | 5    |

---

## 2. 📏 KPI Definitions (chuẩn Basel II / IFRS 9)

| KPI                       | Công thức                                                | Threshold   |
|---------------------------|----------------------------------------------------------|-------------|
| **PD (Probability of Default)** | `y_proba` (calibrated)                              | 0–100%      |
| **Default Rate**          | `SUM(actual_default) / COUNT(*)`                         | Hiện tại 8.04% |
| **AUC**                   | ROC area under curve                                     | ≥ 0.75 ✓ (0.758) |
| **Gini**                  | `2 * AUC - 1`                                            | ≥ 0.50 ✓ (0.516) |
| **KS (Kolmogorov-Smirnov)** | `max|CDF(0) - CDF(1)|`                                 | ≥ 0.30 ✓ (0.375) |
| **Brier Score**           | `mean((y_proba - y_true)^2)`                             | ≤ 0.10 ✓ (0.068) |
| **F1**                    | `2 * P * R / (P + R)` at threshold                      | trade-off   |
| **Expected Loss Rate**    | `SUM(pd) / COUNT(*)` (LGD=EAD=1 placeholder)            | 8.04%       |

---

## 3. 🎨 Design System (Home Credit brand)

### Colors
```
PRIMARY:    #ED1C24  (Home Credit Red)   ← KPI, brand accent
DANGER:     #B11226  (Dark Red)          ← highest risk
WARNING:    #F5A623  (Orange)            ← medium risk, alerts
SUCCESS:    #3FAE5C  (Green)             ← low risk, positive
DARK:       #1A1A1A  (Text)
GRAY:       #6B6B6B  (Subtext)
BG:         #FFFFFF  (Main)
BG-SOFT:    #FFF5F5  (Highlight)
```

### Typography
```
Headings:  Segoe UI Semibold / 16pt / #1A1A1A
Subhead:   Segoe UI Semibold / 12pt / #1A1A1A
Body:      Segoe UI / 10pt / #1A1A1A
Caption:   Segoe UI / 9pt / #6B6B6B
KPI value: Segoe UI Light / 28pt / #ED1C24
```

### Layout rules
- Snap to 8px grid.
- Page size: 1280 × 720 (16:9).
- Padding: 40px outer, 16px inner.
- Cards: rounded 4px, border 2px #ED1C24.
- Tables: alternate row #F9F9F9.

---

## 4. 📄 Page-by-page spec

### Page 1 — Executive Summary

**Visual 1.1 — Header bar**
- Logo: Home Credit H (SVG inline)
- Title: "EXECUTIVE SUMMARY · 30,000 CUSTOMERS"
- Subtitle: ngày refresh, model version

**Visual 1.2 — 5 KPI cards (top row)**
| Card                   | Measure                                  | Color       |
|------------------------|------------------------------------------|-------------|
| TỔNG KHÁCH HÀNG        | Total Customers                          | #1A1A1A     |
| TỈ LỆ VỠ NỢ           | Default Rate %                           | #ED1C24     |
| PD TRUNG BÌNH          | Average Probability of Default %          | #F5A623     |
| AUC (MÔ HÌNH TỐT NHẤT) | Top Model AUC                             | #3FAE5C     |
| ĐIỂM TÍN DỤNG TB       | Average Credit Score                      | #1A1A1A     |

**Visual 1.3 — Risk Band Donut (middle-left)**
- Legend: risk_band
- Data colors: #ED1C24 (Cao), #F5A623 (TB), #3FAE5C (Thấp)

**Visual 1.4 — Score Distribution Histogram (middle-right)**
- X-axis: score (300–850), bin 50
- Y-axis: count customer

**Visual 1.5 — Top 10 Risky Customers (bottom)**
- Table: customer_id, score, pd_calibrated, risk_band, actual_default
- Conditional format: pd_calibrated → Data bar #ED1C24
- Sort: pd_calibrated DESC

### Page 2 — Model Performance

**Visual 2.1 — 5 KPI cards**
| Card         | Measure              | Color   |
|--------------|----------------------|---------|
| AUC (BEST)   | Top Model AUC         | #3FAE5C |
| GINI (BEST)  | Top Model Gini        | #3FAE5C |
| KS (BEST)    | Top Model KS          | #3FAE5C |
| BRIER (MIN)  | Top Model Brier Score | #3FAE5C |
| F1 SCORE     | F1 Score              | #1A1A1A |

**Visual 2.2 — Model comparison table (full width)**
- Table: model_name, auc, gini, ks, brier, pr_auc, f1, recall, precision
- Sort: rank_auc ASC
- Data bars: AUC, Gini, KS columns
- Recommended row: yellow background `#FFF5F5`

**Visual 2.3 — Model AUC bar chart (top-right)**
- X: model_name
- Y: auc
- Color: #ED1C24

**Visual 2.4 — Confusion Matrix (table)**
|                | Predicted = 0 | Predicted = 1 |
|----------------|---------------|---------------|
| Actual = 0     | TN            | FP            |
| Actual = 1     | FN            | TP            |

- Conditional: TP green, FP orange, FN red, TN light gray.

### Page 3 — Risk Segmentation

**Visual 3.1 — 4 KPI cards**
| Card                    | Measure                | Color   |
|-------------------------|------------------------|---------|
| KHÁCH HÀNG RỦI RO CAO  | High Risk Customers     | #ED1C24 |
| RỦI RO TRUNG BÌNH       | Medium Risk Customers   | #F5A623 |
| RỦI RO THẤP             | Low Risk Customers      | #3FAE5C |
| TỈ TRỌNG HIGH RISK      | High Risk Share %       | #ED1C24 |

**Visual 3.2 — Risk Band Bar (full width)**
- X: risk_band
- Y: count customer
- Data colors: red/orange/green

**Visual 3.3 — Bad Rate by Risk Band (line)**
- X: risk_band
- Y: Bad Rate by Risk Band (measure)

**Visual 3.4 — Score Bucket Histogram**
- X: score bin (50)
- Y: count customer
- Color: gradient red → green

### Page 4 — Feature Importance

**Visual 4.1 — 2 KPI cards**
| Card             | Measure                              | Color   |
|------------------|--------------------------------------|---------|
| SỐ FEATURES      | COUNTROWS(fact_feature_importance)   | #1A1A1A |
| TOP 1 FEATURE    | FIRSTNONBLANK([feature], 1)          | #ED1C24 |

**Visual 4.2 — Top 20 Features horizontal bar**
- Y: feature_short (sort importance DESC, top 20)
- X: importance
- Color: #ED1C24

**Visual 4.3 — Feature Group Donut**
- Legend: feature_group (num_/cat_)
- Values: SUM(importance)
- Colors: #ED1C24 / #1A1A1A

### Page 5 — Portfolio Drill-down

**Visual 5.1 — 5 KPI cards**
| Card          | Measure                  | Color   |
|---------------|--------------------------|---------|
| TỔNG          | Total Customers           | #1A1A1A |
| EXPECTED LOSS | Expected Loss Rate %      | #ED1C24 |
| ACCURACY      | Accuracy                  | #1A1A1A |
| RECALL        | Recall (Sensitivity)      | #F5A623 |
| PRECISION     | Precision                 | #3FAE5C |

**Visual 5.2 — PD Distribution (histogram)**
- X: pd_calibrated, bin 0.02
- Y: count customer

**Visual 5.3 — Customer Detail Table**
- Columns: customer_id, score, pd_calibrated, risk_band, rating_class, actual_default, predicted_default
- Drill-through: right-click → "See Records"
- Conditional format: score column → data bar #ED1C24
- Slicers: risk_band, pd_bucket, rating_class

---

## 5. 🔄 Refresh workflow

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ python train.py │ →  │ metrics.json     │ →  │ export_powerbi   │
│                 │    │ predictions_test │    │ _data.py         │
└─────────────────┘    └──────────────────┘    └────────┬─────────┘
                                                       ↓
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Power BI        │ ←  │ 6 CSV files      │ ←  │ powerbi/data/    │
│ Home > Refresh  │    │ (fact + dim)     │    │                  │
└─────────────────┘    └──────────────────┘    └──────────────────┘
```

---

## 6. 📈 Tần suất sử dụng

| Page | Tần suất | Người dùng            |
|------|----------|------------------------|
| 1    | Daily    | CEO, CRO, Head Risk    |
| 2    | Weekly   | Data Science Lead      |
| 3    | Weekly   | Risk Manager           |
| 4    | Monthly  | Model Risk Validator   |
| 5    | Daily    | Credit Officer         |

---

## 7. 🚦 Ngưỡng cảnh báo (Alerting rules)

| Indicator             | Threshold (Red)  | Threshold (Amber) |
|-----------------------|------------------|-------------------|
| AUC                   | < 0.70           | < 0.75            |
| KS                    | < 0.30           | < 0.35            |
| Default Rate drift    | > 10%            | > 8.5%            |
| High Risk share       | > 20%            | > 15%             |
| Brier                 | > 0.10           | > 0.08            |

Khi KPI chạm ngưỡng Amber → email cảnh báo Risk Manager.
Khi chạm Red → escalate lên CRO + trigger model re-train.

---

## 8. 📝 Acceptance criteria (Definition of Done)

- [x] 5 page với layout chuẩn BA
- [x] Theme trắng-đỏ Home Credit
- [x] Font Segoe UI / Inter
- [x] 25+ DAX measures (đã comment rõ ràng)
- [x] Data export script tự động từ `model/metrics.json`
- [x] File `.pbit` mở được trong Power BI Desktop
- [x] Build guide từng bước
- [x] Conditional formatting theo risk band
- [x] Drill-through customer detail
- [x] Documentation đầy đủ
