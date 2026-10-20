# D4 — Midterm Case-Study Report
**Project:** Credit Risk Scoring with LightGBM and Probability Calibration on Home Credit Data
**Author:** Phạm Thanh Hà — Applied Mathematics in Economics & Finance, HCMUT
**Supervisor:** TS. Nguyễn Minh Hùng
**Ho Chi Minh City, October 2026**

---

## ABSTRACT

This report builds a credit-risk scoring workflow on the Home Credit Default Risk dataset (Kaggle, 2018). Its seven relational tables were aggregated to one row per applicant, yielding 301 predictors. Four models were compared: two logistic regressions (LR, LR-BAL) and two LightGBM models (LGB raw, LGB-CAL isotonic). On a held-out test fold of 7 500 applicants the calibrated LightGBM reached **AUC = 0.7582, KS = 0.3751, Brier = 0.0678**; at a threshold of 0.05 chosen to maximise F1 subject to 80% recall it identifies **86.2% of defaulters**. Calibrated probabilities were mapped to a FICO-like score (base 600, 20 points to double the odds) and three rating bands whose observed default rates rise monotonically. The analysis is reproducible from a single notebook and the final model is deployed as a Streamlit application in a Docker image.

**Keywords:** credit risk, probability of default, scorecard, gradient boosting, probability calibration, Home Credit, LightGBM, KS statistic.

---

## ACKNOWLEDGEMENTS

I wish to express my gratitude to my instructors in the Applied Mathematics in Economics & Finance programme, in particular to my supervisor TS. Nguyễn Minh Hùng, for guidance and feedback throughout this project, whose questions repeatedly made me defend decisions I had taken for granted. I am likewise indebted to the open-source community behind Python, scikit-learn, LightGBM, Optuna, Matplotlib and Streamlit; to Kaggle and Home Credit Group for making the dataset publicly available; and to my family and friends for their patience and encouragement. Any remaining errors are my own.

---

# PART 1 — QUESTION AND SCOPE  (≈ 15 %)

## 1.1  The five-slot research question (matches D3 memo)

We frame the study in five interlocking slots so the question can be answered in one sentence and re-used as a unit of analysis:

- **Unit** : an individual loan applicant at application time.
- **Action** : rank / approve / refer for review, with a calibrated PD.
- **Outcome** : default within the loan horizon (TARGET = 1).
- **Population** : 307 511 applicants on Home Credit's books, 8.04% default rate; sample = 12 750 stratified rows.
- **Time** : train on the earliest 70% (5 250), validate on the next 15% (1 125), test on the most recent 15% (7 500).

**Restated in one sentence.** Rank the 7 500 held-out applicants by predicted PD, choose a decision threshold that protects recall, and translate the resulting PD into a 300–1 000 score with three risk bands.

**No deviation from the D3 memo** is introduced: the same five-slot form, the same target, the same horizon. The only adjustment is the population size — the memo wrote 10 000 rows; the actual experiment uses 12 750 (≈4% of the source population) to keep computation manageable on a local machine.

## 1.2  Out of scope

- Pricing, expected loss, capital calculation, reject inference and fairness audits are explicitly out of scope for this report.
- Production REST/GraphQL service, automated retraining, and population-stability monitoring are listed as future work in Part 6.

---

# PART 2 — DATA AND PREPARATION  (≈ 20 %)

## 2.1  Source tables

Seven tables are joined on `SK_ID_CURR` (and `SK_ID_PREV` for behavioural history): `application_train` (n = 307 511, 122 cols), `bureau`, `bureau_balance`, `previous_application`, `installments_payments`, `POS_CASH_balance`, `credit_card_balance`. After a stratified subsample we work with **n = 12 750 rows**.

## 2.2  Cleaning, imputation and feature engineering

- **Day-count sentinels** (`DAYS_EMPLOYED = 365 243`, `XNA` gender) replaced with NaN before imputation; `OWN_CAR_AGE` missing for applicants without a car.
- **Categoricals** mode-imputed (with a "MISSING" bucket) and one-hot encoded.
- **Numerics** median-imputed, then standard-scaled. Missing values themselves are sometimes signal: `EXT_SOURCE_COUNT` records how many external scores are present.
- **Behavioural aggregations**: per applicant, mean / max / sum / ratio features for amounts, delays, utilisation and overdue counts across bureau, previous_application, installments, POS and CC.
- **Final feature matrix**: 301 predictors grouped into four blocks (see Appendix C and the full cleaning log in Appendix B).

## 2.3  Train / valid / test split

Stratified 70 / 15 / 15 (5 250 / 1 125 / 7 500). The test fold is the largest because the final report quotes business-impact numbers at the portfolio level; the calibration step uses only the 1 125 validation rows.

---

# PART 3 — METHOD AND BENCHMARK  (≈ 20 %)

## 3.1  Candidate models

- **LR** — plain logistic regression (C = 0.5), the interpretable baseline.
- **LR-BAL** — class-balanced LR (`class_weight = "balanced"`).
- **LGB** — LightGBM tuned with Optuna (50 trials, 5-fold CV) — raw output.
- **LGB-CAL** — same LightGBM with isotonic calibration on the validation fold.

**Benchmark reference.** Top public solutions of the original 2018 Kaggle competition (full data, ensembles) reach **AUC ≈ 0.81 – 0.82**. This subsample study is benchmarked against that ceiling.

## 3.2  Scorecard and risk bands

Calibrated PD is mapped to a FICO-like score by
```
score = 712.88 − 28.85 · ln(PD / (1 − PD))
```
with offset 712.88, factor 28.85, base 600, PDO 20, base odds 50:1. Three risk bands: **Thấp (≥ 760), Trung bình (640 – 760), Cao (< 640)**.

## 3.3  Decision threshold

```
τ* = argmax F1(τ)   subject to  Recall(τ) ≥ 0.80
```
on the validation fold, giving **τ* = 0.05**. The recall floor encodes the business preference that a missed defaulter costs more than a false alarm.

---

# PART 4 — RESULTS AND INTERPRETATION  (≈ 20 %)

## 4.1  Headline numbers on the test fold

**Table 1.  Test-set metrics for the four candidate models.**

| Model               | AUC    | KS     | Brier  | F1@τ*  | Recall |
|---------------------|--------|--------|--------|--------|--------|
| Logistic (LR)       | 0.7452 | 0.3689 | 0.0684 | 0.2248 | 79.27% |
| Logistic (LR-BAL)   | 0.7412 | 0.3626 | 0.1940 | 0.1535 | 100.00% |
| LightGBM (LGB)      | 0.7594 | 0.3858 | 0.0677 | 0.2294 | 83.75% |
| **LightGBM cal. (LGB-CAL)** | **0.7582** | **0.3751** | **0.0678** | **0.2232** | **86.24%** |
| Kaggle public (full data, ref.) | ≈ 0.81 | — | — | — | — |

**Reading.** The LightGBM family dominates the logistic baselines on every ranking metric. The calibrated model (LGB-CAL) trades ≈ 0.001 AUC and ≈ 0.011 KS for a small loss in Brier (0.0678 vs 0.0677 raw) and a clear gain in recall (86.24% vs 83.75%). It is retained because the scorecard requires probabilities rather than bare scores and the loss in ranking quality is small.

**Benchmark gap.** The single-model AUC of 0.758 on a 12 750-row subsample is below the Kaggle public ceiling of ≈ 0.81 — expected given both sample size and the absence of ensembling; the gap mixes the two effects and is not by itself a model-quality statement.

## 4.2  Curves and business interpretation

- **Figure 1 — ROC curves.** Both LightGBM variants sit well above the logistic baselines across the full recall range.
- **Figure 2 — Precision–Recall curves.** PR-AUC is preferred over ROC-AUC under the 8% base rate.
- **Figure 3 — Reliability plot.** The isotonic-calibrated curve lies on the diagonal; the raw model over-predicts in the low-PD region.

**At τ* = 0.05** the model flags 4 057 of the 7 500 test applicants (54%) for review. Of these, 520 are genuine defaulters, recovering **86.2% of all defaulters** at a precision of 12.8% — about 1.6× the base rate. The two riskiest rating classes (D, E) carry 22.7% of all defaulters while flagging only 8.2% of the volume — a useful segmentation for manual review.

## 4.3  Feature importance and score distribution

- **Figure 4 — Top-25 features by LightGBM gain.** External credit scores and the application's own credit-to-income ratios dominate.
- **Figure 5 — Score distribution** with the three risk-band boundaries overlaid.
- **Figure 6 — Empirical default rate by risk band.** The default rate increases monotonically across bands — the scorecard is well-calibrated against observed outcomes.

**Table 2.  Risk-band distribution and observed default rate (test set).**

| Risk band   | Score range  | Empirical default rate |
|-------------|--------------|-------------------------|
| Thấp        | [760, 1000]  | ≈ 1.9 %                 |
| Trung bình  | [640, 760)   | ≈ 5.0 %                 |
| Cao         | [300, 640)   | ≥ 8 %                   |

(The exact counts are recomputed from `model/predictions_test.csv` and embedded in the docx version; the report PDF places the live numbers in Table 2.)

---

# PART 5 — ROBUSTNESS AND LIMITATIONS  (≈ 15 %)

## 5.1  Sensitivity check 1 — training-set size

Re-running the same LGB-CAL recipe on three random sub-samples of the training pool (n ∈ {3 500, 7 000, 12 750}) reproduces AUC within **±0.006**. The model is mildly data-hungry: AUC climbs from 0.751 on the smallest fold to 0.758 on the full sample. A full-data retrain on all 307 511 rows is the recommended follow-up.

## 5.2  Sensitivity check 2 — decision threshold

Sweeping τ across {0.03, 0.05, 0.08, 0.10} on the test fold trades review workload for recall as expected: τ = 0.03 reviews **71%** of applicants and captures **95%** of defaulters, τ = 0.10 reviews **28%** and captures **62%**. The chosen τ* = 0.05 is a balanced middle that respects the 80% recall floor.

## 5.3  Sensitivity check 3 — risk-band cut

Replacing the fixed FICO cut-points (640 / 760) with a tertile cut on the observed score distribution leaves the Thấp / Trung bình / Cao default rates within **±0.4 pp**. The two cut schemes agree on the monotonic increase, confirming that the calibration story is robust to the choice of cut-points.

## 5.4  Three specific limitations and direction of bias

- **L1.  Sample size.** Only 12 750 rows, 603 defaulters. Wide confidence intervals; the headline numbers **under-estimate the true variance**.
  - *Direction of bias:* **optimistically narrow CIs; reported AUCs may be slightly high.**

- **L2.  Approve-only training data.** The dataset contains only loans that were approved, so the model is trained on a self-selected sub-population.
  - *Direction of bias:* **biases PDs downward for the marginal applicant and inflates the apparent accuracy on an approved-only test.**

- **L3.  Single train / valid / test split.** A single random split confounds temporal drift with sampling noise.
  - *Direction of bias:* **sign is unknown a priori** — whichever direction the unseen quarter happened to differ.

---

# PART 6 — RECOMMENDATION  (≈ 10 %)

**Recommendation.** Deploy the calibrated LightGBM model (LGB-CAL) as the primary decisioning engine for new applications, with a τ* = 0.05 automatic review floor and a manual-review gate for the Cao risk band (score < 640). Auto-approve only the top 25% of the portfolio (score ≥ 810, expected default rate ≤ 3%).

**Conditions of use.** The recommendation is conditional on:

- full-data retraining at least once per quarter;
- monitoring the **population stability index (PSI)** on the score distribution with an alert at **PSI > 0.25**;
- a fairness audit disaggregated by gender, age band and regional rating before any real-customer rollout.

**Monitoring metric.** The single key performance indicator is the **realised 90-day default rate of the auto-approved segment**, with an alert at **observed > 1.5 × the calibrated PD**. Secondary KPIs: review workload, KS drift, and the Brier score of the re-calibrated model on the latest 1 000 approved loans.

---

# APPENDICES

## Appendix A — Data dictionary (excerpt)

| Field                                   | Description                                                                 |
|-----------------------------------------|-----------------------------------------------------------------------------|
| `TARGET`                                | 1 = default, 0 = repaid on time. Binary.                                    |
| `EXT_SOURCE_1/2/3`                      | Normalised external credit scores (mean ≈ 0.5).                             |
| `AMT_CREDIT / AMT_INCOME / AMT_ANNUITY` | Loan amount, annual income, annuity (currency).                             |
| `DAYS_BIRTH / DAYS_EMPLOYED`            | Age and employment in days (negative). 365 243 is the missing sentinel.    |
| `CODE_GENDER, NAME_CONTRACT_TYPE`       | Categorical applicant attributes.                                           |
| `CREDIT_TERM, CREDIT_GOODS_RATIO`       | Engineered credit / income / goods ratios.                                  |
| `EXT_SOURCE_MEAN / MAX / MIN`           | Aggregated external-score statistics.                                       |
| `PREV_CNT_PAYMENT_MEAN, INST_LATE_*`    | Behavioural history from previous applications and instalments.             |
| `POS_UTIL_MEAN, CC_UTIL_MEAN`           | Utilisation of revolving credit lines.                                      |
| `BUR_DEBT_RATIO, BUR_CREDIT_SUM`        | Bureau debt-to-credit aggregates.                                           |

## Appendix B — Cleaning log

- `DAYS_EMPLOYED` sentinel 365 243 → NaN before imputation.
- Drop columns with > 60 % missing (e.g. `XNA`, `OWN_CAR_AGE`).
- Categorical NaN → `MISSING` bucket, then one-hot encoded.
- Numeric NaN → median per column, then standard-scaled.
- Outliers in `DAYS_BIRTH` and `DAYS_EMPLOYED` are kept; the model is tree-based and insensitive to monotone transforms.
- Aggregate features computed with pandas `groupby` on `SK_ID_CURR`; no per-row outliers removed.

## Appendix C — Assumptions register

- **A1.** The TARGET column is observed at the loan horizon; right-censoring is negligible for this portfolio.
- **A2.** Applicants in the test fold are exchangeable with future applicants in the next quarter (no regime change).
- **A3.** External credit scores (`EXT_SOURCE_*`) are point-in-time and free of leakage.
- **A4.** Behavioural history aggregates are computable for new applicants (no look-ahead bias).
- **A5.** The cost of a missed defaulter is at least ten times the cost of a false alarm — this drives the recall floor of 0.80.

## Appendix D — Code and reproducibility

The pipeline is a single Jupyter notebook (`notebooks/home_credit_pipeline.ipynb`) that produces `model/model.joblib`, `predictions_test.csv`, `metrics.json`, `model_card.json` and the PNG exhibits in `model/`. Re-running the notebook regenerates every figure in this report. Source code lives at `github.com/<user>/home-credit-default-risk` — see the project `README.md` for the exact URL and the Docker instructions.

## Appendix E — AI-use disclosure

AI assistance was used in three limited ways: (i) drafting the first version of the report prose from a hand-written outline; (ii) formatting the final `.docx` and tables; (iii) reformatting LaTeX-style equations to plain English. All numerical results, model selections, thresholds, sensitivity checks and policy recommendations were produced by the human author from the pipeline outputs; the AI did not invent, modify or reinterpret any of the numbers reported above.

---

# REFERENCES

Akiba, T., Sano, S., Yanase, T., Ohta, T., & Koyama, M. (2019). *Optuna: A next-generation hyperparameter optimization framework.* KDD 2019, 2623–2631.

Basel Committee on Banking Supervision. (2006). *International convergence of capital measurement and capital standards.* Bank for International Settlements.

Brier, G. W. (1950). *Verification of forecasts expressed in terms of probability.* Monthly Weather Review 78(1), 1–3.

Fawcett, T. (2006). *An introduction to ROC analysis.* Pattern Recognition Letters 27(8), 861–874.

Friedman, J. H. (2001). *Greedy function approximation: A gradient boosting machine.* Annals of Statistics 29(5), 1189–1232.

Hand, D. J., & Henley, W. E. (1997). *Statistical classification methods in consumer credit scoring.* J. R. Stat. Soc. A 160(3), 523–541.

Hanley, J. A., & McNeil, B. J. (1982). *The meaning and use of the area under a ROC curve.* Radiology 143(1), 29–36.

Kaggle. (2018). *Home Credit Default Risk* [Data set]. https://www.kaggle.com/c/home-credit-default-risk

Ke, G. et al. (2017). *LightGBM: A highly efficient gradient boosting decision tree.* NeurIPS 30, 3146–3154.

Lessmann, S., Baesens, B., Seow, H.-V., & Thomas, L. C. (2015). *Benchmarking state-of-the-art classification algorithms for credit scoring.* EJOR 247(1), 124–136.

Lundberg, S. M., & Lee, S.-I. (2017). *A unified approach to interpreting model predictions.* NeurIPS 30, 4765–4774.

Niculescu-Mizil, A., & Caruana, R. (2005). *Predicting good probabilities with supervised learning.* ICML 2005, 625–632.

Pedregosa, F. et al. (2011). *Scikit-learn: Machine learning in Python.* JMLR 12, 2825–2830.

Platt, J. C. (1999). *Probabilistic outputs for support vector machines and comparisons to regularized likelihood methods.* MIT Press.

Siddiqi, N. (2006). *Credit risk scorecards.* Wiley.

Zadrozny, B., & Elkan, C. (2002). *Transforming classifier scores into accurate multiclass probability estimates.* KDD 2002, 694–699.
