# Home Credit Default Risk — Power BI Dashboard

> A five-page Business Intelligence dashboard for the Home Credit Default Risk project, themed in the Home Credit red-and-white brand palette, built around ~25 DAX measures and an automated export pipeline that feeds directly off `model/metrics.json` and `model/predictions_test.csv`.

---

## Table of contents

1. [Highlights](#-highlights)
2. [Quick start](#-quick-start)
3. [Project structure](#-project-structure)
4. [Design system](#-design-system)
5. [Page-by-page overview](#-page-by-page-overview)
6. [KPIs and acceptance thresholds](#-kpis-and-acceptance-thresholds)
7. [Refresh workflow](#-refresh-workflow)
8. [Troubleshooting](#-troubleshooting)
9. [Documentation index](#-documentation-index)
10. [Author and version](#-author-and-version)

---

## Highlights

- **Five purpose-built pages** — Executive Summary, Model Performance, Risk Segmentation, Feature Importance and Portfolio Drill-down — one persona per page.
- **Home Credit brand theme** — primary red `#ED1C24`, dark red `#B11226`, semaphore colours for risk, Segoe UI typography, supplied as a reusable `.json` theme file.
- **~25 ready-to-use DAX measures** — Basel II-aligned KPIs (default rate, AUC, Gini, KS, Brier, average PD), time-since and risk-band helpers.
- **Hand-off-ready data model** — a star schema of three dimension tables (`dim_models`, `dim_risk_bands`, `dim_segments`) and three fact tables (`fact_predictions`, `fact_thresholds`, `fact_feature_importance`).
- **Automated export** — `powerbi/export_powerbi_data.py` rebuilds the six CSV inputs from the latest training run in one command.
- **Two ways to view** — open the static HTML preview instantly, or open the full Power BI Desktop template for editing and publishing.

---

## Quick start

### 1. Browser preview — zero install

```bash
# Windows
start powerbi\preview.html

# macOS / Linux
open powerbi/preview.html
```

Renders all five pages with live data: KPIs, donut, score histogram, model comparison, risk bands, feature importance and a customer table.

### 2. Export data after a fresh model run

```bash
python powerbi\export_powerbi_data.py
```

Regenerates the six CSV files in `powerbi/data/`, sourced from `model/metrics.json` and `model/predictions_test.csv`.

### 3. Power BI Desktop — full edit and publish

1. Install Power BI Desktop (free): <https://powerbi.microsoft.com/desktop/>
2. Open `powerbi/homecredit.pbix` (or double-click `powerbi/HomeCreditRiskDashboard.pbit` if you have a template file).
3. When prompted, point the data sources to `powerbi/data/`.
4. `View` → `Themes` → `Browse for themes` → select `powerbi/theme/home_credit_theme.json`.
5. See `powerbi/docs/build_guide.md` for visual-by-visual instructions.
6. See `powerbi/docs/dax_measures.dax` for the measures library.

> **Tip.** Run steps 2 → 3 in order: if the CSV files are missing or stale, Power BI will report data-source errors on open.

---

## Project structure

```
powerbi/
├── homecredit.pbix                  ← Power BI Desktop report (open this)
├── README.md                        ← This file
├── preview.html                     ← Static HTML preview of the dashboard
├── export_powerbi_data.py           ← Regenerate CSV inputs from the model
│
├── data/                            ← Six CSV inputs (auto-generated)
│   ├── dim_models.csv
│   ├── dim_risk_bands.csv
│   ├── dim_segments.csv
│   ├── fact_predictions.csv
│   ├── fact_feature_importance.csv
│   └── fact_thresholds.csv
│
├── theme/
│   └── home_credit_theme.json       ← Brand theme (JSON)
│
└── docs/
    ├── build_guide.md               ← Visual-by-visual build instructions
    ├── dashboard_spec.md            ← BA-grade specification
    └── dax_measures.dax             ← Reusable DAX measure library
```

---

## Design system

| Role           | Hex       | Usage                                             |
|----------------|-----------|---------------------------------------------------|
| Primary red    | `#ED1C24` | Brand, primary KPI, header accents               |
| Dark red       | `#B11226` | Highest-risk band, danger emphasis                |
| Amber          | `#F5A623` | Medium-risk band, warning emphasis               |
| Green          | `#3FAE5C` | Low-risk band, positive KPI delta                 |
| Ink (text)     | `#1A1A1A` | Body copy, axis labels                            |
| Subtext        | `#6B6B6B` | Captions, footnotes, axis secondary               |
| Paper          | `#FFFFFF` | Canvas background                                 |
| Tint           | `#FFF5F5` | Highlight band behind brand-red KPIs              |

**Type.** Segoe UI throughout — Semibold for section titles, Light 28 pt for the hero KPI, Regular 12 pt for body and table cells, Light 10 pt for footnotes.

**Layout.** 1280 × 720 canvas, 8 px grid, 16 px outer padding, generous white space, KPI cards 240 × 140 px, full-width tables allowed.

---

## Page-by-page overview

| # | Page                  | Primary persona | Headline visuals                                                                                       |
|---|-----------------------|-----------------|--------------------------------------------------------------------------------------------------------|
| 1 | Executive Summary     | CEO, CRO        | Hero KPI strip (default rate, AUC, Gini, KS, Brier), risk donut, score histogram, top-10 feature bar   |
| 2 | Model Performance     | Data Science    | Four-model AUC and KS comparison, calibration overlay, confusion matrix                                  |
| 3 | Risk Segmentation     | Risk Manager    | Three-band view (A–B / C / D–E), bad rate by band, score distribution by band                          |
| 4 | Feature Importance    | Model Validator | LightGBM gain top-20, behavioural vs demographic split, EXT_SOURCE cluster                              |
| 5 | Portfolio Drill-down  | Credit Officer  | PD distribution histogram, slicer-driven customer table with score, PD, band and actual default status |

---

## KPIs and acceptance thresholds

The hero KPI strip on page 1 is the same set the D4 report defends. All values reference the production model — LightGBM with isotonic calibration — on the held-out test fold of 7,500 applicants.

| KPI                 | Current value | Acceptance threshold (Basel II-aligned) |
|---------------------|---------------|------------------------------------------|
| Default rate        | 8.04 %        | informational                           |
| AUC                 | 0.7582        | ≥ 0.75                                  |
| Gini                | 0.5164        | ≥ 0.50                                  |
| KS                  | 0.3751        | ≥ 0.30                                  |
| Brier               | 0.0678        | ≤ 0.10                                  |
| Average PD (cal)    | 7.45 %        | informational                           |
| Average credit score| ≈ 600         | informational                           |
| Recall at τ = 0.05  | 86.2 %        | ≥ 80 %                                  |
| Precision at τ      | 12.8 %        | informational                           |

A KPI flashes green only when both colour contrast against `#FFFFFF` and WCAG AA contrast (≥ 4.5:1) pass.

---

## Refresh workflow

### Manual

```bash
python src/train.py
python powerbi\export_powerbi_data.py
# In Power BI Desktop: Home → Refresh
```

Use this during development and after any model change.

### Scheduled

1. Publish `homecredit.pbix` to the Power BI Service.
2. Install an On-Premises Data Gateway on a host that can read `powerbi/data/`.
3. Configure a scheduled refresh in the Service (recommended cadence: weekly).

### Continuous Integration

Run `python powerbi\export_powerbi_data.py` as a post-deploy step in your CI pipeline so the CSVs are always in sync with the latest training run. Power BI will pick them up on the next refresh.

---

## Troubleshooting

| Symptom                                        | Likely cause                                          | Fix                                                                                                       |
|------------------------------------------------|-------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| "Cannot find file …csv" on open                | Data source path is absolute from another machine     | Transform Data → Data source settings → repoint to the local `powerbi/data/` folder                       |
| Theme does not apply                           | `.json` not loaded                                   | View → Themes → Browse for themes → pick `home_credit_theme.json` → Reset to default                       |
| Slicer shows empty values                      | Relationship missing                                  | Model view → drag `dim_risk_bands[band_id]` to `fact_predictions[band_id]` → verify cardinality          |
| PD shows as 0.07 instead of 7 %                | Column formatted as decimal                          | Modeling → select the column → Format → Percentage, 2 decimal places                                       |
| Hero KPI reads 0                               | Measure context wrong                                 | Check `dax_measures.dax` for `[Default Rate]` and verify `DIVIDE` returns a non-zero numerator              |
| Bars do not sort by gain                       | Sort axis not pinned                                  | Click column → Sort axis → `Gain DESC`                                                                    |
| HTML preview shows stale data                  | No rebuild after model update                         | Run `python powerbi/build_preview.py` (if available) or refresh the underlying CSVs                       |

---

## Documentation index

| File / artefact                          | Purpose                                                                          |
|------------------------------------------|----------------------------------------------------------------------------------|
| `README.md`                              | This file — onboarding and reference                                            |
| `preview.html`                           | Static HTML render of all five pages                                            |
| `homecredit.pbix`                        | Power BI Desktop report (open and edit)                                         |
| `docs/build_guide.md`                    | Step-by-step instructions for every visual                                       |
| `docs/dashboard_spec.md`                 | BA-grade specification, including persona, KPIs, navigation                     |
| `docs/dax_measures.dax`                  | Reusable DAX measure library (~25 measures)                                     |
| `theme/home_credit_theme.json`           | Brand theme — colours, text styles, visual defaults                              |
| `export_powerbi_data.py`                | Regenerates the six CSV inputs from `model/metrics.json` and `predictions_test.csv` |
| `../model/metrics.json`                  | Source of truth for KPIs                                                        |
| `../model/predictions_test.csv`          | Source of truth for per-customer predictions and bands                          |

---

## Author and version

| Field    | Value                                                                              |
|----------|------------------------------------------------------------------------------------|
| Project  | D4 Midterm — Home Credit Default Risk                                              |
| Course   | Thematic unit 1 — Applied Mathematics in Economics & Finance                       |
| Authors  | Phat Huynh (K234131613), Duy Nguyen (K234131591)                                   |
| Owner    | Phat Huynh                                                                         |
| Stack    | Python 3.13 · scikit-learn 1.6 · LightGBM 4.x · Optuna · Power BI Desktop           |
| Version  | 1.0.0 — released October 2026                                                      |
| Status   | Active — refreshed nightly                                                        |
| Licence  | Academic use only — please retain this header if you fork or reuse                |

---

*Data refreshes are driven by `python powerbi\export_powerbi_data.py` and assume the latest training run is in place under `../model/`. Any discrepancy between the dashboard and the report v3 reflects the timestamp of the last CSV regeneration — re-run the export script to reconcile.*
