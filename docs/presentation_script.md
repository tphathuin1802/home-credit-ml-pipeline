# PRESENTATION SCRIPT — D4 MIDTERM REPORT
**Duration:** 12–15 minutes (about 1 min/slide)
**Language:** English
**Presenters:** Phat Huynh (K234131613), Duy Nguyen (K234131591)
**Topic:** Home Credit Default Risk — Credit-Risk Scoring with LightGBM and Probability Calibration

> **How to use this script.** Each slide has two blocks — **ON THE SLIDE** (a short reminder of what is projected) and **SAY THIS** (a continuous, spoken paragraph). The estimated time is given at the top of each slide.

---

## SLIDE 1 — TITLE / INTRODUCTION *(~60 sec)*

**On the slide:**
- Title: HOME CREDIT DEFAULT RISK SCORING
- Tagline: A reproducible end-to-end ML pipeline that turns 7 raw tables into a deployable PD model — with scorecard, risk bands and a Streamlit front-end.
- Authors: Phat Huynh, Duy Nguyen — Applied Mathematics in Finance — Python, LightGBM, Streamlit
- HC // CREDIT-RISK, 01 / 15

**Say this:**

"Good morning, professors and friends. I'm Phat, and together with Duy we are presenting our D4 midterm project on **Home Credit Default Risk Scoring** — that is, a reproducible credit-scoring pipeline that takes Home Credit's seven raw tables all the way to a deployable Probability-of-Default model, complete with a scorecard, five risk bands and a web demo.

The project has a **dual objective**. First, the model must **discriminate** between who defaults and who does not — we measure that with AUC and the KS statistic. Second, the probabilities it outputs must be **reliable enough to drive credit policy**, because Basel computes expected loss as `PD × LGD × EAD`. A model that ranks well but produces sloppy probabilities is useless for pricing or provisioning.

Everything here is reproducible from a single notebook, and the final model is packaged in Docker and deployed on Streamlit Cloud. Let me begin."

---

## SLIDE 2 — THE PROBLEM *(~60 sec)*

**On the slide:**
- 02 / 15 — SECTION 01: THE PROBLEM
- Three pillars: Default rate is low (~8%) — imbalanced classification / Cost asymmetry / Calibrated PD feeds downstream credit policy, expected loss and loan pricing
- Sub: Home Credit serves underbanked borrowers with thin credit files. The business problem: score each applicant for default risk using alternative data.

**Say this:**

"First, why does this problem matter?

Home Credit lends to people that mainstream banks normally turn away — borrowers in emerging markets with little or no formal credit history. For them a traditional bureau score is either missing or of limited value. That is why Home Credit assembled **seven tables**: the current application, bureau records, previous applications, instalment histories, POS balances and credit-card balances — an **alternative-data credit footprint**.

Three points define the problem.

**First, the default rate is only about 8%.** This is an **imbalanced** classification problem. A model that always predicts "no default" is still right 92% of the time, so **accuracy carries almost no information**. We therefore report AUC, KS, the Brier score, and recall at a fixed operating threshold.

**Second, the costs are asymmetric.** Missing a defaulter is far more expensive than rejecting a good borrower. A wrong decline only costs us a lost sale; a wrong approval costs us the loss. That is exactly why we pick our threshold to protect **recall at or above 80%** rather than simply maximising F1.

**Third, Basel demands that PD be both discriminating and well calibrated.** Those two requirements can pull in opposite directions, and that tension is the reason this project exists: find one pipeline in which **ranking** and **calibration** both succeed."

---

## SLIDE 3 — DELIVERABLES *(~45 sec)*

**On the slide:**
- Deliverables: trained and calibrated model (model.joblib), metrics table (model/metrics_table.csv), per-customer PD and rating (model/predictions_test.csv), Streamlit web app and Docker, model card (model/model_card.json), slide deck.

**Say this:**

"The project delivers six concrete artefacts. **One** — the trained and calibrated model, saved as `model.joblib`. **Two** — a metrics table comparing all four candidate models. **Three** — `predictions_test.csv`, which stores a calibrated PD and an A-to-E rating for every test applicant; this is what the business-impact analysis in Chapter 4 uses to compute capture rates and lift. **Four** — a Streamlit web demo, containerised in Docker and deployed. **Five** — `model_card.json`, the model's curriculum vitae, recording exactly what it was trained on and how it performed. And **six** — this slide deck."

---

## SLIDE 4 — DATASET *(~60 sec)*

**On the slide:**
- Table of 7 tables with rows and use: application_train (307,511), bureau (1.7M), bureau_balance (27.3M), previous_application (1.7M), installments_payments (13.6M), POS_CASH_balance (10.0M), credit_card_balance (3.8M).

**Say this:**

"The dataset consists of seven tables, several of them very large. The smallest, `application_train`, has 307 thousand rows — and it is the **master table**, carrying the `TARGET` column we want to predict. The other six are **auxiliary** tables. `bureau` and `bureau_balance` hold credit histories reported by other institutions. `previous_application` holds earlier applications from the same customer at Home Credit. `installments_payments` records repayments instalment by instalment. `POS_CASH_balance` and `credit_card_balance` are monthly balance snapshots.

The key structural difficulty is this: a single customer appears **many times** in these auxiliary tables — someone with five instalment plans contributes five rows to `installments_payments`. So we **cannot join directly**. Each table must first be aggregated down to exactly one row per customer before merging into the master table.

That aggregation raises an important engineering question: which summary function suits each column? For `DAYS_CREDIT` — days since the bureau record was filed — the **minimum** is far more informative than the mean; for `AMT_CREDIT_SUM_DEBT` the **maximum** outstanding balance best reflects current risk. After careful design we end up with **301 engineered features**, a number you will see again shortly."

---

## SLIDE 5 — EDA: CLASS IMBALANCE AND MISSINGNESS *(~60 sec)*

**On the slide:**
- Exploratory Data Analysis // Target and Missing
- Findings: default rate about 8%, broadly stable across age groups, the 20–25 cohort is riskiest. Some 50 or more columns have meaningful missingness, dominated by housing characteristics and the external scores.

**Say this:**

"Two initial observations drive every downstream modelling choice.

First, the default rate is roughly **8%** and is broadly stable across age groups, with the 20-to-25 cohort running slightly higher — a finding worth remembering when we come to the fairness discussion.

Second, **more than 50 columns** carry substantial missing values — concentrated in housing characteristics and, importantly, the **three external credit scores** `EXT_SOURCE_1/2/3`. Instead of imputing those three aggressively with a mean or a median — the common reflex — we preserve a signal in a variable we call `EXT_SOURCE_COUNT`, which simply records **how many external scores are present**. The reasoning is that the *fact* that a customer has any bureau footprint at all is itself informative about their credit history, and filling the gap with a constant would erase exactly that signal.

These two decisions — refusing to use accuracy, and treating missingness as signal — shape the entire pipeline that follows."

---

## SLIDE 6 — EDA: KEY FEATURES BY TARGET *(~60 sec)*

**On the slide:**
- Comparing distributions of AMT_CREDIT, AMT_INCOME, AGE and the three EXT_SOURCE scores between defaulters and non-defaulters.
- Chart: all three EXT_SOURCE variables tagged STRONG.

**Say this:**

"This slide compares the **distributions** of four variables between the default and non-default groups.

Unsurprisingly, all three **external credit scores** — `EXT_SOURCE_1`, `EXT_SOURCE_2` and `EXT_SOURCE_3` — show **very strong discrimination**: their distributions between the two groups are almost fully separated. We tag all three as STRONG, because these are the variables most widely discussed in the Home Credit community.

By contrast, **age**, **income** and **loan amount** have distributions that largely overlap between defaulters and non-defaulters. On their own they are **not sufficient** for prediction. That is precisely the motivation for the engineered feature block on the next slide: we need 301 features, not 122, to give even a linear model a real chance of capturing the signal."

---

## SLIDE 7 — FEATURE ENGINEERING: FOUR BLOCKS *(~75 sec)*

**On the slide:**
- 01 / Application cleaning — `DAYS_EMPLOYED` sentinel, `XNA` gender, `OWN_CAR_AGE`, time and ratio features, `EXT_SOURCE` aggregates.
- 02 / Bureau aggregation — `BUR_ACTIVE_CNT`, `BUR_DEBT_SUM`, `BUR_DEBT_RATIO`, `HAS_BUREAU`.
- 03 / Previous applications and instalments — `PREV_APPROVE_RATE`, `PREV_CNT_PAYMENT_MEAN`, `INST_PAY_RATIO`, `INST_LATE_MEAN`, `INST_LATE_7D_SUM`.
- 04 / POS_CASH and credit card — `POS_UTIL_MEAN`, `POS_CNT`, `CC_UTIL_MEAN`.

**Say this:**

"This is the slide I am most proud of — the **feature-engineering blueprint**. From 122 raw columns we build **301 features**, organised into four functional blocks.

**Block one — cleaning and ratios on the master table.** We handle three traps. `DAYS_EMPLOYED = 365243` is a sentinel value, converted to NaN plus a binary flag. `CODE_GENDER = XNA` likewise becomes NaN. And `OWN_CAR_AGE` stays NaN for customers without a car — because "no car" is itself a signal. We then build ratio features such as `CREDIT_INCOME_RATIO`, `CREDIT_TERM` and `ANNUITY_INCOME_RATIO`, plus mean, min, max, standard deviation, product and count for the three external scores.

**Block two — bureau aggregates.** We group by `SK_ID_CURR` and take counts of active credits, sums of outstanding debt, and one important ratio, `BUR_DEBT_RATIO` = debt divided by credit limit, plus a `HAS_BUREAU` flag for customers with **no** bureau record whatsoever.

**Block three — previous applications and instalments.** The approval rate `PREV_APPROVE_RATE`, the lateness history `INST_LATE_MEAN`, and the total days late by at least seven, `INST_LATE_7D_SUM`. These are the features that will climb to the top of our importance ranking shortly.

**Block four — POS and credit cards.** Average utilisation, `POS_UTIL_MEAN` and `CC_UTIL_MEAN` — the closer a customer runs to their limit, the higher the risk.

All four blocks merge back into the master table to give a **301-dimensional** feature vector per customer. Everything is implemented inside a **single `ColumnTransformer`**, fitted on the training fold and applied unchanged to validation and test — our structural guarantee against data leakage."

---

## SLIDE 8 — METHODOLOGY: MODELLING PIPELINE *(~75 sec)*

**On the slide:**
- Seven steps: Split / Preprocess (ColumnTransformer) / Baselines LR and LR-balanced / Tuned LightGBM (Optuna, 15 trials) / Isotonic calibration on validation / Threshold F1-driven (recall at or above 80%) / Evaluate AUC, Gini, KS, Brier, PR-AUC, F1.
- Summary: `n_estimators = 205`, `num_leaves = 53`, `lr = 0.047`; Brier pre = 0.0677, post = 0.0678; tau = 0.05.

**Say this:**

"The modelling pipeline has **seven clearly separated steps**.

**Step 1, splitting.** We divide train, validation and test with a **stratified** split so that every fold preserves the same 8% default rate. `random_state = 42` is fixed throughout so every comparison is reproducible. This version of the report uses **50,000 rows** in total — 35,000 train, 7,500 validation and 7,500 test. Note that we increased the sample relative to the original 12,750-row draft, which gives more stable results and still fits comfortably in memory.

**Step 2, preprocessing.** A single `ColumnTransformer` — median imputation for numeric variables, most-frequent imputation plus one-hot encoding with drop-first for categoricals.

**Step 3, baselines.** Two logistic regressions — one unweighted with `C = 0.5`, one with `class_weight = 'balanced'`. Both serve as **benchmarks** throughout the report; we deliberately use that word so the comparison is explicit.

**Step 4, tuned LightGBM.** We optimise the hyper-parameters with **Optuna over 15 trials**, with early stopping on the validation fold. The winning trial gives `n_estimators = 205`, `num_leaves = 53`, `learning_rate = 0.0469`.

**Step 5, calibration.** We fit an **isotonic regression** on the validation fold to recalibrate the output probabilities. The Brier score moves from 0.0677 to 0.0678 — essentially unchanged, because only a small range of the scale is affected — but the resulting probabilities are the ones we can actually trust in a scorecard.

**Step 6, the threshold.** We apply **Equation 3.1** — maximise F1 subject to recall of at least 0.80 — which yields **tau\* = 0.05**.

**Step 7, evaluation.** We report AUC, Gini, KS, Brier, PR-AUC and F1 on a **test fold of 7,500 applicants** that played no part in any of the six steps above."

---

## SLIDE 9 — RESULTS: TEST-SET COMPARISON *(~75 sec)*

**On the slide:**
- Four-model table: Model / AUC / Gini / KS / Brier / PR-AUC / F1 / Recall / Precision.
- Logistic 0.7452 · LR-BAL 0.7412 · LGB 0.7594 · LGB-CAL 0.7582.
- Selected model: LightGBM with isotonic calibration — catches 86.2% of defaulters at 12.8% precision.

**Say this:**

"This is the headline table — all four models evaluated on the same 7,500-row test fold.

**Logistic**, our benchmark, reaches an AUC of **0.7452** and a KS of **0.369**. That is the baseline to beat.

**Logistic-balanced** deserves a specific comment. Its recall is 100%, but its precision is only 8.3% — essentially identical to the base rate. In other words, at its operating threshold it flags virtually every applicant, which is useless as a decision rule. Its Brier score is also roughly three times worse, because class weighting pushes predicted probabilities far above the true default frequency. This is exactly the point made on slide 2: **class weighting is not a remedy when you need calibrated probabilities**.

**Raw LightGBM** achieves the best ranking: AUC **0.7594**, KS **0.386**.

**Calibrated LightGBM** gives up 0.0012 of AUC and about 0.011 of KS, but reaches a **higher recall** — 86.2% against 83.8% — and produces probabilities fit for the scorecard. This is the model we take forward.

That 0.014 AUC gap looks small, and I want to be honest about it: the bootstrap analysis in Chapter 5 shows this gap **falls inside a 95% confidence interval that contains zero** at a 50,000-row sample. I will come back to that on the final slide, and it is precisely why we added a full robustness chapter."

---

## SLIDE 10 — EVALUATION PLOTS *(~45 sec)*

**On the slide:**
- ROC, PR, KS and calibration plots.
- "KS = 0.375 at the optimal cut-off — well above the 0.20 acceptable and 0.30 good credit-scoring benchmarks."

**Say this:**

"This slide packages the four core diagnostic plots.

**ROC**, top left — all four curves sit **clearly above the diagonal**; no model is poor. **Precision–recall**, below it — given a base rate of only 8%, precision remains several times the base rate at low-to-moderate recall, which is a good sign.

**The KS plot**, top right, is the one I want to dwell on. Our KS reaches **0.375** at the optimal cut-off, **comfortably above the 0.30 good benchmark** used in credit scoring. In other words, the largest vertical separation between the good and bad cumulative distributions is 37.5 percentage points — **enough to segment a real portfolio** in practice.

The **reliability plot**, bottom right, shows calibrated probabilities tracking the diagonal across most of the range, with mild over-confidence between 0.1 and 0.3 — a known artefact of isotonic regression in sparse regions of the score space."

---

## SLIDE 11 — FEATURE IMPORTANCE *(~45 sec)*

**On the slide:**
- Top features by LightGBM gain: `PREV_CNT_PAYMENT_MEAN`, `CREDIT_TERM`, `EXT_SOURCE_MEAN`, `CREDIT_GOODS_RATIO`, `INST_PAY_RATIO`, `POS_UTIL_MEAN`, `EMPLOYED_YEARS`, `BUR_DEBT_RATIO`, `PREV_APPROVE_RATE`, `ANNUITY_INCOME_RATIO`.
- "Top features come from engineered ratios, instalment history and external scores — the model relies on behavioural signals, not raw demographics."

**Say this:**

"The ten strongest features by **LightGBM gain**:

**First, `PREV_CNT_PAYMENT_MEAN`** — the average number of instalments in the customer's repayment history, our single strongest signal. **Second, `CREDIT_TERM`**, the loan term. **Third, `EXT_SOURCE_MEAN`**, the average of the three external bureau scores. Then come **`CREDIT_GOODS_RATIO`** (loan relative to goods value), **`INST_PAY_RATIO`** and **`INST_LATE_MEAN`** (repayment ratio and average lateness), **`POS_UTIL_MEAN`** (POS utilisation), **`EMPLOYED_YEARS`**, **`BUR_DEBT_RATIO`** and **`PREV_APPROVE_RATE`** with **`ANNUITY_INCOME_RATIO`**.

The important observation is what is *absent* from that list: **age and gender rank very low**. The model relies predominantly on **financial behaviour** rather than raw demographics — which is a reassuring signal from a fairness standpoint."

---

## SLIDE 12 — SCORECARD AND RISK BANDS *(~75 sec)*

**On the slide:**
- Formula: `score = 712.88 − 28.8539 × ln( PD / (1 − PD) )`
- Band table A to E: score range / average PD / empirical default rate / population.
- A (760–1000): 1.92% · B (640–760): 5.02% · C (480–640): 8.70% · D (360–480): 14.84% · E (0–360): 30.04%.

**Say this:**

"This is the **core product** of the project — converting a probability of default into a FICO-style credit score.

The formula is `score = 712.88 − 28.85 × ln(odds)`, with a base of 600, a PDO of 20 — that is, twenty points for every doubling of the odds — and base odds of 50 to 1, following the Siddiqi convention. We derive `factor = PDO / ln 2 = 28.85` and `offset = 600 + factor × ln 50 = 712.88`.

We then split applicants into **five risk bands, A to E**, using **PD thresholds** of 0.03, 0.06, 0.10 and 0.20 rather than fixed score cuts. The reason is empirical: the realised score range on the test fold is only **401 to 799**, not the textbook 300 to 850, so a fixed cut at 640 and 760 would push nearly the entire test set into a single middle band.

The **empirical default rates rise monotonically**:

- **Band A**, PD below 3%: **1.92%** across 2,185 applicants.
- **Band B**, 3 to 6%: **5.02%** across 2,372.
- **Band C**, 6 to 10%: **8.70%** across 1,241.
- **Band D**, 10 to 20%: **14.84%** across 1,166.
- **Band E**, 20% and above: **30.04%** across 536.

Average predicted PD and observed default rate agree to within **1.5 percentage points** in every band. The scorecard works."

---

## SLIDE 13 — BUSINESS IMPACT *(~75 sec)*

**On the slide:**
- At tau = 0.05, on 7,500 test customers with 603 defaulters, the model flags roughly 520 defaulters for manual review — compare to the 8% base rate.
- Capture rate and lift table: A 7.0% / 0.24× · B 19.7% / 0.62× · C 17.9% / 1.08× · D 28.7% / 1.85× · E 26.7% / 3.74×.

**Say this:**

"At our operating point tau\* = 0.05 — chosen on the validation fold to protect recall above 80% — we can quantify the **business impact** on the test set.

**In aggregate**, there are 603 defaulters. The model catches 86.2% of them, so **520 customers** are routed to manual review. A precision of 12.8% means roughly one in eight flagged applicants is a true defaulter; against an 8% base rate that is a **lift of about 1.6 times** — good enough to justify the review workload.

**By band**:

- **Band A** contains 30% of applicants but only 7% of defaulters, a lift of just 0.24× — the natural candidate for **streamlined approval**.
- **Bands D and E together** hold only 22.7% of applicants yet contain **55.4% of all defaulters** — that is where manual review should concentrate.
- **Bands B through E** cover 70% of applicants while capturing **93% of defaulters**.
- **Band E** carries a lift of **3.74×** — nearly four times the base rate — and clearly warrants scrutiny.

The conclusion is that this model should **not** be used to auto-decline anyone. Its role is **triage**: auto-approve band A, standard review for B and C, and manual review for D and E. That is exactly how Basel expects an internal model to be used."

---

## SLIDE 14 — CONCLUSION, LIMITATIONS, FUTURE WORK *(~75 sec)*

**On the slide:**
- Summary table of three models: AUC / Gini / KS / Brier / Recall at tau = 0.05.
- Logistic 0.7452 / 0.4904 / 0.3689 / 0.0684 / 79.3% · LightGBM raw 0.7594 / 0.5188 / 0.3858 / 0.0677 / 83.7% · LightGBM calibrated 0.7582 / 0.5164 / 0.3751 / 0.0678 / 86.2%.
- Limitations: reject inference, deep tabular models, time series of instalment history, calibration refresh.
- Future work: sample size, macro recall-versus-precision policy, PSI and KS drift monitoring, fairness audit.

**Say this:**

"To conclude the project as a whole.

**The pipeline runs end to end**: from seven raw tables to a calibrated PD model, a FICO-style scorecard, five risk bands and a Streamlit front-end — with every step **reproducible** from one notebook.

**Three numbers to remember**: an AUC of **0.7582**, a KS of **0.3751**, and **86.2% recall** at tau = 0.05 — strong performance for a problem with an 8% positive rate and genuinely noisy alternative-data signals.

**Two limitations I want to state plainly.**

**First**, the LightGBM-versus-Logistic gap of about 0.014 AUC lies **inside a 95% bootstrap confidence interval that contains zero** when we resample the test predictions 1,000 times. Put bluntly: on this test fold we cannot statistically claim LightGBM beats logistic regression. That is genuine sampling uncertainty, and we report it rather than overstate it.

**Second**, our logistic benchmark is a **default scikit-learn configuration** — no Weight-of-Evidence binning, no outlier treatment, no regularisation sweep. The 0.014 AUC gap should therefore be read as an **upper bound** on LightGBM's true advantage, not a point estimate.

**Future work** falls into three groups. Modelling: reject inference to address approved-only training data, deep tabular architectures such as TabNet and FT-Transformer, and sequence models over instalment history. Operations: quarterly re-fitting of the isotonic regression as the portfolio mix drifts, and PSI and KS drift monitoring on the external scores and amount variables. And governance: a fairness audit disaggregated by gender and age band before any production rollout."

---

"Thank you. I am happy to take any questions."

---

## SLIDE 15 — THANK YOU / Q&A *(~30 sec)*

**On the slide:**
- "THANK YOU."
- "Questions, feedback, collaboration — always welcome."
- https://sh-home-credit-ml-pipeline.streamlit.app

**Say this:**

"Thank you to our professors and to all of you for listening. The demo application is live at the address on the slide — you are welcome to try it. I am happy to take questions, feedback, and ideas for collaboration. Thank you."

---

# APPENDIX A — ANTICIPATED Q&A

### Q1. "Why 50,000 rows instead of the full 307,000?"

**A.** Memory and runtime. Fifty thousand rows is enough for 301 engineered features to fit comfortably on a laptop, while still allowing a 1,000-resample bootstrap in seconds. The report states the deployment condition explicitly: the model must be retrained on the full dataset before any production rollout.

### Q2. "The bootstrap CI contains zero — so is LightGBM actually better than logistic regression?"

**A.** Possibly, possibly not — at this sample size we cannot distinguish them. On published benchmarks and at full scale, LightGBM is usually clearly ahead. The +0.014 point estimate on this test fold has the right sign but is **not strong enough** to reject the null hypothesis that the two models are equivalent.

### Q3. "Why isotonic regression rather than Platt scaling?"

**A.** Both are standard. Platt scaling assumes a sigmoid shape and has fewer parameters, which makes it the safer choice on a small validation fold. Isotonic regression assumes nothing about shape but needs a reasonably large sample to remain reliable. Our validation fold has 7,500 rows — comfortably large enough for isotonic. Section 3.5 cites Niculescu-Mizil and Caruana (2005) on exactly this trade-off.

### Q4. "The realised score range is 401 to 799 — are fixed cut-points at 760 even sensible?"

**A.** That is why we switched to **PD thresholds** of 0.03, 0.06, 0.10 and 0.20. Because the realised score range does not span the textbook 300 to 850, fixed cuts at 640 and 760 collapse nearly the whole test set into a single middle band. PD thresholds are invariant to the score scale, so they remain meaningful.

### Q5. "Where does the PSI above 0.25 alert threshold come from?"

**A.** It is an industry convention, cited from Sidlo (2003): PSI below 0.10 indicates a stable population, 0.10 to 0.25 warrants monitoring, and above 0.25 signals a material shift requiring recalibration.

### Q6. "Band E carries a 30% default rate — can we auto-decline on that basis?"

**A.** **No.** The report is explicit that the model is a decision-support tool, not a standalone decline rule. Every D and E decision requires an underwriter sign-off. This also matches the Basel expectation for internal ratings-based models. Auto-declining at 30% observed default would discard roughly seven in ten good applicants.

### Q7. "How do you justify the 80% recall floor?"

**A.** It encodes assumption A5: the cost of a missed defaulter is at least ten times the cost of a false alarm. The threshold sweep in Section 5.2 quantifies the trade-off directly — moving the threshold from 0.05 to 0.03 buys 6.8 percentage points of recall but costs 16.8 percentage points of review workload. An operator with a tighter review budget should simply re-tune the threshold on their own validation fold.

### Q8. "How did you guard against data leakage?"

**A.** Three ways. The `ColumnTransformer` — including imputers and the scaler — is fitted **only** on the training fold and applied unchanged to validation and test. All median imputations therefore derive from training statistics alone. The isotonic calibration layer is fitted on validation, never on test. And the test fold is untouched until every modelling decision has been made, so the reported metrics reflect data that played no part in any decision.

---

# APPENDIX B — DELIVERY NOTES

### Pacing

| Segment | Slides | Target time |
|---|---|---|
| Opening and problem | 1–3 | 2 min 45 s |
| Data and features | 4–7 | 4 min 15 s |
| Method and results | 8–11 | 4 min 00 s |
| Scorecard and impact | 12–13 | 2 min 30 s |
| Conclusion and Q&A | 14–15 | 1 min 45 s |
| **Total** | **15** | **about 15 min** |

### Where to compress if you run long

- **Slide 5** — state the two findings, skip the age-cohort detail.
- **Slide 6** — keep the EXT_SOURCE observation, drop the AMT_CREDIT comparison.
- **Slide 10** — lead with the KS benchmark, summarise the other three plots in one sentence.
- **Slide 12** — read only band A and band E aloud; the table carries the middle bands.

Never compress slides 9, 13 or 14 — they carry the results, the business case and the honest limitations, which is what the panel will be examining.

### Pre-presentation checklist

- [ ] Open the slide PDF in presentation mode; verify fonts, images and table alignment render correctly.
- [ ] Open `https://sh-home-credit-ml-pipeline.streamlit.app` in a separate browser tab, pre-loaded.
- [ ] Keep `model/predictions_test.csv` and `model/sensitivity_results.json` accessible in case of a technical question.
- [ ] Have the final report PDF open and accessible so the panel can cross-reference a table.
- [ ] Rehearse once with a timer. The common failure mode is spending 90 seconds on slides 5 to 7 and then rushing the limitations.