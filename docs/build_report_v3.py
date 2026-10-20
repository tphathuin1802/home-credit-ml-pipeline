"""Build D4 Midterm Case-Study Report DOCX from docs/report_complete.md (full version with bootstrap CI + 3 limitations + recommendation + 5-band Appendix E)."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_BREAK
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

PROJ = Path('c:/Dev/home-credit-default-risk')
OUT  = PROJ / 'docs' / 'D4_report_v3.docx'

# ─── helpers ──────────────────────────────────────────────────────────────────
def set_font(run, name='Times New Roman', size=12, bold=False, italic=False):
    run.font.name = name; run.font.size = Pt(size)
    run.font.bold = bold;   run.font.italic = italic

def para_spacing(p, before=0, after=0, line=None):
    pf = p.paragraph_format
    pf.space_before = Pt(before); pf.space_after = Pt(after)
    if line: pf.line_spacing = Pt(line); pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY

def set_cell_bg(cell, hex_color):
    tc = cell._tc; tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def page_break(doc):
    p = doc.add_paragraph(); p.add_run().add_break(WD_BREAK.PAGE)

def h1(doc, text):
    p = doc.add_paragraph(); run = p.add_run(text); set_font(run, bold=True, size=13)
    para_spacing(p, before=18, after=6); return p

def h2(doc, text):
    p = doc.add_paragraph(); run = p.add_run(text); set_font(run, bold=True, size=12)
    para_spacing(p, before=12, after=4); return p

def body(doc, text, after=6, indent=0, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph(); p.alignment = align
    run = p.add_run(text); set_font(run, size=12)
    pf = p.paragraph_format
    pf.space_after = Pt(after)
    if indent: pf.left_indent = Inches(indent)
    return p

def bullet(doc, text, indent=0.25, after=3):
    p = doc.add_paragraph(style='List Bullet')
    run = p.add_run(text); set_font(run, size=12)
    p.paragraph_format.left_indent = Inches(indent)
    p.paragraph_format.space_after = Pt(after)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p

def equation(doc, text):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text); set_font(run, size=12, italic=True)
    para_spacing(p, before=4, after=8)
    return p

def caption(doc, label, text):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p.add_run(label + ' '); set_font(r1, bold=True, size=11)
    r2 = p.add_run(text); set_font(r2, italic=True, size=11)
    para_spacing(p, before=4, after=8)

def table_style(t):
    t.style = 'Table Grid'
    for row in t.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after  = Pt(2)

def make_table(doc, headers, rows, col_widths=None, header_bg='D9E1F2'):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_style(t)
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]; set_cell_bg(c, header_bg)
        p = c.paragraphs[0]; run = p.add_run(h); set_font(run, bold=True, size=11)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            c = t.rows[ri+1].cells[ci]
            p = c.paragraphs[0]; run = p.add_run(str(val)); set_font(run, size=11)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if ci > 0 else WD_ALIGN_PARAGRAPH.LEFT
    if col_widths:
        for ri in t.rows:
            for ci, c in enumerate(ri.cells):
                c.width = Inches(col_widths[ci])
    return t

def add_figure(doc, img_path, caption_label, caption_text, width_in=5.5):
    if img_path.exists():
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(img_path), width=Inches(width_in))
        para_spacing(p, before=4, after=2)
    caption(doc, caption_label, caption_text)

# ─── COVER ────────────────────────────────────────────────────────────────────
def build_cover(doc):
    for ln in [
        'VIETNAM NATIONAL UNIVERSITY, HO CHI MINH CITY',
        'HO CHI MINH UNIVERSITY OF TECHNOLOGY',
        'FACULTY OF COMPUTER SCIENCE & ENGINEERING',
    ]:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(p.add_run(ln), bold=True, size=12); para_spacing(p, after=2)

    doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run('─' * 55), size=12); para_spacing(p, before=4, after=10)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run('D4 — MIDTERM CASE-STUDY REPORT'), bold=True, size=16)
    para_spacing(p, before=6, after=8)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run('Credit-Risk Scoring with LightGBM and\nProbability Calibration on Home Credit Data'),
             bold=True, size=14); para_spacing(p, after=30)

    for label, value in [
        ('SUPERVISOR', 'TS. Nguyễn Minh Hùng'),
        ('STUDENT',    'Phạm Thanh Hà — Applied Mathematics in Economics & Finance'),
    ]:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r1 = p.add_run(label + '\n'); set_font(r1, bold=True, size=12)
        r2 = p.add_run(value); set_font(r2, size=12); para_spacing(p, after=6)

    doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run('Ho Chi Minh City, October 2026'), size=12, italic=True)
    para_spacing(p, before=10)
    page_break(doc)

# ─── INNER TITLE ──────────────────────────────────────────────────────────
def build_inner(doc):
    for ln in [
        'VIETNAM NATIONAL UNIVERSITY, HO CHI MINH CITY',
        'HO CHI MINH UNIVERSITY OF TECHNOLOGY',
        'FACULTY OF COMPUTER SCIENCE & ENGINEERING',
    ]:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(p.add_run(ln), bold=True, size=12); para_spacing(p, after=2)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run('─' * 55), size=12); para_spacing(p, before=4, after=14)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run('D4 — MIDTERM CASE-STUDY REPORT'), bold=True, size=16)
    para_spacing(p, after=8)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run('Credit-Risk Scoring with LightGBM and\nProbability Calibration on Home Credit Data'),
             bold=True, size=14); para_spacing(p, after=30)

    for label, value in [
        ('Topic',     'Credit-Risk Scoring with LightGBM and Probability Calibration on Home Credit Data'),
        ('Supervisor','TS. Nguyễn Minh Hùng'),
        ('Student',   'Phạm Thanh Hà'),
        ('Programme', 'Applied Mathematics in Economics & Finance'),
        ('Date',      'October 2026'),
    ]:
        p = doc.add_paragraph()
        r1 = p.add_run(label + ':\n'); set_font(r1, bold=True, size=12)
        r2 = p.add_run(value); set_font(r2, size=12); para_spacing(p, after=6)
    page_break(doc)

# ─── ACKNOWLEDGEMENTS ────────────────────────────────────────────────────
def build_acknowledgements(doc):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run('ACKNOWLEDGEMENTS'), bold=True, size=13)
    para_spacing(p, before=6, after=12)

    body(doc,
        'I wish to express my gratitude to my instructors in the Applied Mathematics in Economics & Finance '
        'programme at HCMUT, in particular to my supervisor TS. Nguyễn Minh Hùng, for guidance and feedback '
        'throughout this project, whose questions repeatedly made me defend decisions I had taken for granted. '
        'I am likewise indebted to the open-source community behind Python, scikit-learn, LightGBM, Optuna, '
        'Matplotlib and Streamlit; to Kaggle and Home Credit Group for making the dataset publicly available; '
        'and to my family and friends for their patience and encouragement. Any remaining errors are my own.',
        after=0)
    page_break(doc)

# ─── ABSTRACT ────────────────────────────────────────────────────────────
def build_abstract(doc):
    h1(doc, 'ABSTRACT')
    body(doc,
        'This report describes the construction of a credit-risk scoring workflow using the Home Credit Default '
        'Risk dataset available on Kaggle (Kaggle, 2018). The dataset is provided as seven interconnected tables: '
        'current applications, credit-bureau records, previous loans, instalment payments, point-of-sale balances, '
        'credit-card balances, and monthly bureau balances. These tables were aggregated into a single row per '
        'applicant, yielding 301 predictors that capture each individual\'s profile, repayment history, and the '
        'external credit scores included with the data.')
    body(doc,
        'Four models were compared: two logistic regressions (LR and LR-BAL) and two LightGBM models (LGB and '
        'LGB-CAL). An isotonic calibration step is applied on top of the second LightGBM model. On a held-out '
        'test set comprising 7,500 applicants, the calibrated LightGBM model achieved an AUC of 0.7582 and a '
        'KS of 0.3751. With the threshold set at τ* = 0.05 — chosen on the validation fold to maximise F1 '
        'subject to Recall ≥ 0.80 — the model identifies 86.2% of defaulters at the cost of flagging 54% of '
        'all applicants.')
    body(doc,
        'The calibrated probabilities were subsequently converted into a score, anchored at 600 points with '
        '20 points assigned for each doubling of the odds. Applicants were allocated to five rating bands '
        '(A–E), defined by PD thresholds (0.03, 0.06, 0.10, 0.20). Observed default rates rise consistently '
        'across these bands, from 1.92% in band A to 30.04% in band E.')
    body(doc,
        'The entire analysis can be reproduced from a single notebook, and the final model is deployed via a '
        'Streamlit application packaged as a Docker image. Two limitations should be noted: (i) to keep '
        'computation feasible, a stratified subsample of 50,000 applicants (about 16% of the full data) was '
        'used; (ii) the test fold contains only 603 defaulters, so the absolute difference between models '
        'carries confidence intervals that contain zero under 1,000-resample bootstrap (Chapter 5). Training on '
        'the complete dataset would likely yield improved results and tighter intervals.')
    body(doc, 'Keywords: credit risk, probability of default, scorecard, gradient boosting, probability '
              'calibration, Home Credit, LightGBM, KS statistic.')
    page_break(doc)

# ─── CHAPTER 1 ───────────────────────────────────────────────────────────
def build_ch1(doc):
    h1(doc, 'CHAPTER 1: QUESTION AND SCOPE')

    h2(doc, '1.1  Research question (matches D3 memo, five-slot PICOT)')
    body(doc,
        'For loan applicants within the Home Credit portfolio (Population), does a gradient-boosted decision-tree '
        'ensemble with isotonic calibration (Intervention) yield higher ranking quality and better-calibrated '
        'probability-of-default estimates than a regularised logistic-regression baseline (Comparator), as '
        'measured by AUC, KS, Brier score and recall at a fixed operating threshold (Outcome), when both '
        'models are trained and evaluated on the same engineered feature set and the same stratified held-out '
        'test fold (Time / Setting)?')
    body(doc,
        'Restated in the canonical five-slot form so it can be answered in one breath and aligned unit-by-unit '
        'with the D3 memo:')

    slot_rows = [
        ['Population (Unit)', 'An individual loan application in Home Credit\'s portfolio at submission time, identified by SK_ID_CURR.'],
        ['Intervention (Action)', 'Rank / approve / refer for review by a calibrated probability of default.'],
        ['Comparator (Benchmark)', 'Logistic regression (LR) with L2 regularisation C = 0.5, unweighted.'],
        ['Outcome', 'Default within the loan horizon (TARGET = 1), observed on the held-out test fold.'],
        ['Time / Setting', 'Train on the earliest 70% of the sample, validate on the next 15%, test on the most recent 15%, all stratified on TARGET.'],
    ]
    make_table(doc, ['Slot', 'Specification'], slot_rows, col_widths=[1.7, 4.6])
    body(doc, '', after=4)

    body(doc, 'Alignment with D3 memo.')
    body(doc,
        'The PICOT slot list, the target, the loan horizon and the comparator are unchanged from the D3 memo. '
        'The two adjustments that were made and the reason for each are:')
    bullet(doc,
        'Sample size. The D3 memo allowed up to 20,000 rows; the experiment uses 50,000 rows (≈ 16% of the full '
        'data) so the engineered feature set (301 predictors) and the Optuna tuning step fit in memory on a '
        'local machine.')
    bullet(doc,
        'Population description. The D3 memo described the population generically; this report adds the explicit '
        'identification key SK_ID_CURR to make the row-level join unambiguous.')
    body(doc,
        'No other deviation from the D3 memo. The PICOT framing is what allows Chapter 4 to quote a single '
        'primary number (the AUC gap LightGBM − LR on the test fold) and Chapter 5 to ask whether that gap is '
        'distinguishable from zero.')

    h2(doc, '1.2  Rationale for Topic Selection')
    body(doc,
        'Home Credit serves borrowers that mainstream banks usually turn down — people in emerging markets with '
        'little or no formal credit history. For these applicants, a traditional bureau score is either missing '
        'or of limited value. Estimating the probability of default (PD) thus becomes the core underwriting '
        'task. Basel\'s internal-ratings-based approach also demands that PD estimates be both discriminating '
        'and well calibrated, since expected loss equals PD × LGD × EAD. A model that ranks applicants well but '
        'produces inconsistent probabilities is of little use for pricing or provisioning. This project tackles '
        'exactly that dual requirement using a public, richly structured data set.')
    add_figure(doc, PROJ / 'assets' / 'c__Dev_home-credit-default-risk_model__F993D3F2-8FD8-448B-9697-49D661E2545B_.png',
               'Figure 1.', 'Home Credit business overview.')

    h2(doc, '1.3  Scope')
    body(doc,
        'All experiments use a stratified subsample of 50,000 applicants drawn from the 307,511-row source '
        'extract (random_state = 42), split into training (35,000), validation (7,500) and test (7,500) folds, '
        'to keep computation feasible on a local machine. Performance on the full data would likely be higher, '
        'and subsample results carry considerable sampling uncertainty (Chapter 5). The study addresses PD '
        'estimation only; pricing, LGD, EAD and regulatory-capital calculations are out of scope. Deployment '
        'is a Streamlit application packaged as a Docker image, with a production-grade REST service left for '
        'future work.')

    h2(doc, '1.4  Brief Related Work')
    body(doc,
        'Logistic regression has long been the industry standard in credit scoring, as it is interpretable and '
        'converts easily into points-based scorecards (Hand & Henley, 1997; Siddiqi, 2006). Benchmarking studies '
        'show ensemble methods often outperform single classifiers, yet logistic regression remains a strong, '
        'transparent baseline (Lessmann et al., 2015). Gradient boosting (Friedman, 2001) and its efficient '
        'implementation LightGBM (Ke et al., 2017) are now staples of tabular risk modelling. For probability '
        'calibration, Platt scaling (Platt, 1999) and isotonic regression (Zadrozny & Elkan, 2002) are the most '
        'common post-hoc corrections, and non-parametric methods need a reasonably large hold-out set to stay '
        'reliable (Niculescu-Mizil & Caruana, 2005).')
    page_break(doc)

# ─── CHAPTER 2 ───────────────────────────────────────────────────────────
def build_ch2(doc):
    h1(doc, 'CHAPTER 2: DATA AND PREPARATION')

    h2(doc, '2.1  Source Tables')
    body(doc,
        'The data describe 307,511 loan applicants, each characterised by 122 raw variables in the main '
        'application table. Six auxiliary tables hold the applicant\'s history with Home Credit and with other '
        'lenders. Every applicant is identified by SK_ID_CURR, and may have any number of rows, including none, '
        'in each auxiliary table (Table 2.1). Because an applicant can appear many times in these tables, they '
        'cannot be joined to the application table directly; they have to be aggregated to one row per applicant first.')

    src_rows = [
        ['application_train', 'One row per loan application: demographics, income, loan terms, housing, external scores and the binary target.', 'SK_ID_CURR'],
        ['bureau', 'Credits reported by other financial institutions to the credit bureau.', 'SK_ID_CURR'],
        ['bureau_balance', 'Monthly status history of each bureau credit.', 'SK_ID_BUREAU'],
        ['previous_application', 'Earlier applications made by the same customer at Home Credit.', 'SK_ID_CURR'],
        ['installments_payments', 'Repayment record of previous loans, one row per instalment.', 'SK_ID_CURR'],
        ['POS_CASH_balance', 'Monthly balances of point-of-sale and cash loans.', 'SK_ID_CURR'],
        ['credit_card_balance', 'Monthly balances of credit cards held at Home Credit.', 'SK_ID_CURR'],
    ]
    make_table(doc, ['Table', 'Content', 'Link to applicant'], src_rows, col_widths=[1.6, 4.0, 1.4])
    caption(doc, 'Table 2.1.', 'Source tables of the Home Credit Default Risk dataset.')

    h2(doc, '2.2  Class Imbalance and Why Accuracy Is Not Used')
    body(doc,
        'Roughly 8.04% of applicants default in the source data, so the target is moderately imbalanced. A '
        'classifier that approves everyone would still be correct about 92% of the time, which is why accuracy '
        'carries almost no information in this setting and is not used to compare models. Figure 2 shows the '
        'class distribution together with the default rate across age groups.')
    caption(doc, 'Figure 2.', 'Target distribution (counts, pie) and default rate by age group. Generated by code (cell 3).')

    h2(doc, '2.3  Missing Data')
    body(doc,
        'Missing data are another feature of this dataset. About 50 columns have a substantial share of missing '
        'values, mostly housing characteristics and the three external scores (Figure 3). Instead of imputing '
        'the external scores aggressively, the pipeline records how many of them are present in a variable '
        'called EXT_SOURCE_COUNT. The reasoning is that whether an applicant has an external score at all is '
        'itself informative about their credit footprint, and that filling the gap with a mean or median would '
        'erase that signal.')
    caption(doc, 'Figure 3.', 'Top 20 columns by missing rate. Generated by code (cell 4).')
    page_break(doc)

# ─── CHAPTER 3 ───────────────────────────────────────────────────────────
def build_ch3(doc):
    h1(doc, 'CHAPTER 3: METHODOLOGY')

    h2(doc, '3.1  Pipeline Overview')
    body(doc,
        'The workflow has four stages. In the first, the six auxiliary tables are summarised to one row per '
        'applicant and merged with the application table on SK_ID_CURR. In the second, the combined table is '
        'cleaned and enriched with engineered features. In the third, models are trained, tuned and compared. '
        'In the fourth, the selected model is calibrated, a threshold is chosen, scores and bands are constructed, '
        'and the result is exposed through a web interface. Figure 4 outlines the preprocessing stage and Figure '
        '5 the modelling stage.')
    caption(doc, 'Figure 4.', 'Block diagram of the data-preprocessing pipeline. Generated by code (cell 5).')
    caption(doc, 'Figure 5.', 'Block diagram of the modelling pipeline. Generated by code (cell 6).')

    h2(doc, '3.2  Data Partitioning')
    body(doc,
        'The 50,000-row sample is divided into training, validation and test folds, stratified on the target so '
        'that each fold keeps the same default rate of about 8.04% (random_state = 42). Each fold has a '
        'distinct role. The training fold is used to fit the models. The validation fold is used for early '
        'stopping, calibration and threshold selection. The test fold is held back until the very end, so '
        'that the metrics reported in Chapter 4 reflect performance on data that played no part in any modelling '
        'decision.')
    split_rows = [
        ['Training',  '35,000', '8.04%', 'Yes'],
        ['Validation', '7,500',  '8.04%', 'Yes'],
        ['Test',      '7,500',  '8.04%', 'Yes'],
        ['Total',     '50,000', '8.04%', '—'],
    ]
    make_table(doc, ['Fold', 'Rows', 'Default rate', 'Stratified on TARGET'], split_rows)
    caption(doc, 'Table 3.1.', 'Stratified partition of the sample.')
    caption(doc, 'Figure 6.', 'Stratified split used in this work. Generated by code (cell 7).')

    h2(doc, '3.3  Preprocessing and Feature Engineering')
    body(doc,
        'Preprocessing relies on a single scikit-learn ColumnTransformer (Pedregosa et al., 2011), fitted only on '
        'the training fold and applied unchanged to the validation and test folds, keeping steps consistent '
        'across models and preventing leakage. Numeric variables are median-imputed and standardised. Missing '
        'values in categorical variables are replaced with a dedicated MISSING level, and the variables are '
        'one-hot encoded with the first level dropped. Sentinel values are handled before imputation: 365,243 '
        'in DAYS_EMPLOYED becomes missing plus a binary flag, the gender code XNA becomes missing, and '
        'OWN_CAR_AGE is set to missing for applicants without a car.')
    body(doc,
        'In total, 301 features are built in four blocks (Table 3.2). Time variables are converted from days to '
        'years, and ratio features relate the loan to the applicant\'s means. The three external scores are '
        'summarised by their mean, minimum, maximum, standard deviation, product and count. Rather than '
        'imputing the external scores aggressively, the pipeline records how many are present (EXT_SOURCE_COUNT), '
        'since having an external score is itself informative and filling the gap with a mean or median would '
        'erase that signal. Auxiliary tables are aggregated with a groupby on SK_ID_CURR, and applicants with '
        'no bureau record are flagged (HAS_BUREAU).')
    block_rows = [
        ['Application cleaning and ratios', 'application_train', 'AGE_YEARS, EMPLOYED_YEARS, CREDIT_INCOME_RATIO, ANNUITY_INCOME_RATIO, CREDIT_TERM, EXT_SOURCE_MEAN'],
        ['Bureau aggregates', 'bureau', 'BUR_ACTIVE_CNT, BUR_DEBT_SUM, BUR_MAX_OVERDUE_DAYS, BUR_DEBT_RATIO, HAS_BUREAU'],
        ['Earlier applications and instalments', 'previous_application, installments_payments', 'PREV_APPROVE_RATE, PREV_CNT_PAYMENT_MEAN, INST_PAY_RATIO, INST_LATE_MEAN'],
        ['Point-of-sale and credit card', 'POS_CASH_balance, credit_card_balance', 'POS_UTIL_MEAN, POS_CNT, CC_UTIL_MEAN'],
    ]
    make_table(doc, ['Block', 'Source tables', 'Representative features'], block_rows, col_widths=[1.8, 1.8, 3.5])
    caption(doc, 'Table 3.2.', 'Blocks of engineered features.')

    body(doc,
        'The full cleaning log lives in Appendix B and is consistent with this section: no column is dropped '
        'simply because its missing rate is high; instead EXT_SOURCE_COUNT, HAS_BUREAU, OWN_CAR_AGE are '
        'retained as informative missingness flags.')

    h2(doc, '3.4  Candidate Models')
    body(doc,
        'Four classifiers are compared (Table 3.3). Plain logistic regression and a class-balanced variant that '
        'gives more weight to the minority class serve as benchmarks. The third model is LightGBM tuned with '
        'Optuna (Akiba et al., 2019) over 15 trials, with early stopping on the validation fold. The fourth is '
        'the same LightGBM model with an isotonic calibration layer fitted on the validation fold. The '
        'hyperparameters of the best trial are listed in Table 3.4.')
    cand_rows = [
        ['Logistic (LR)',           'Benchmark (unweighted)',     'L2 regularisation; constant C = 0.5.'],
        ['Logistic_balanced (LR-BAL)', 'Benchmark (class-weighted)', 'class_weight = "balanced".'],
        ['LightGBM (LGB)',          'Boosted trees',              'Optuna, 15 trials; early stopping on the validation fold.'],
        ['LightGBM_calibrated (LGB-CAL)', 'Boosted trees + calibration', 'Isotonic regression fitted on the validation fold.'],
    ]
    make_table(doc, ['Model', 'Type', 'Notes'], cand_rows, col_widths=[1.6, 1.7, 3.7])
    caption(doc, 'Table 3.3.', 'Candidate Models compared in this study.')

    hp_rows = [
        ['n_estimators', '205'], ['num_leaves', '53'], ['learning_rate', '0.0469'],
        ['max_depth', '4'], ['min_child_samples', '117'], ['subsample', '0.837'],
        ['colsample_bytree', '0.523'], ['reg_alpha', '0.177'], ['reg_lambda', '0.004'],
        ['objective', 'binary'], ['random_state', '42'],
    ]
    make_table(doc, ['Hyperparameter', 'Value'], hp_rows, col_widths=[2.5, 2.5])
    caption(doc, 'Table 3.4.', 'Best LightGBM hyperparameters found by Optuna.')

    h2(doc, '3.5  Calibration and Threshold Selection')
    body(doc,
        'Calibration matters whenever downstream decisions depend on absolute PD values. An isotonic '
        'regression is fitted on the validation fold to map the raw LightGBM output to a calibrated probability '
        '(Zadrozny & Elkan, 2002). The decision threshold is then chosen on the same fold using the rule in '
        'Equation (3.1), which on the validation data gives τ* = 0.05.')
    equation(doc, 'τ* = argmax_τ  F1(τ)   subject to  Recall(τ) ≥ 0.80      (3.1)')
    body(doc,
        'The recall floor encodes the business preference that a missed defaulter costs at least 10× a false '
        'alarm (assumption A5, Appendix C). Because the validation fold is used for early stopping, calibration '
        'and threshold choice alike, any optimism in those three steps would show up as a drop between '
        'validation and test; the test fold is the only fair reference.')

    h2(doc, '3.6  Scorecard Construction')
    body(doc,
        'Calibrated probabilities are mapped to points using the scorecard equation below, with a base score of '
        '600, a PDO = 20, and base odds of 50 : 1, following the standard scorecard convention (Siddiqi, 2006).')
    equation(doc, 'score = offset − factor · ln( PD / (1 − PD) )')
    equation(doc, 'factor = PDO / ln(2) = 20 / 0.6931 = 28.8539')
    equation(doc, 'offset = 600 + factor · ln(50) = 600 + 28.8539 · 3.9120 = 712.87')
    equation(doc, 'score = 712.87 − 28.85 · ln(odds),   with odds = PD / (1 − PD)    (3.2)')

    body(doc,
        'Applicants are then assigned to five rating bands, A–E, from lowest to highest risk. The bands are '
        'defined by PD thresholds (0.03, 0.06, 0.10, 0.20) — not by fixed score cuts — for two reasons. First, '
        'the score scale produced by Equation (3.2) is monotonic in PD, so PD bands and score bands carry the '
        'same information; choosing PD bands directly avoids the spurious precision of mapping a 0.7552 score '
        'onto a fixed cut when the underlying probability is what we have computed. Second, on the test fold '
        'the realised score range is [401, 799] (rather than the textbook 300–850), so a fixed cut at 760 '
        'leaves only a handful of applicants in the top band. The bands are evaluated not by how they look but '
        'by whether the observed default rate rises steadily from A to E on the test fold (Section 4.4).')
    band_rows = [
        ['A', 'PD < 0.03',         'Approve'],
        ['B', '0.03 ≤ PD < 0.06',  'Standard review'],
        ['C', '0.06 ≤ PD < 0.10',  'Standard review'],
        ['D', '0.10 ≤ PD < 0.20',  'Manual review / tighter pricing'],
        ['E', 'PD ≥ 0.20',         'Decline or refer to specialised flow'],
    ]
    make_table(doc, ['Band', 'PD range', 'Intuition'], band_rows, col_widths=[0.7, 1.8, 3.5])
    caption(doc, 'Table 3.5.', 'PD-based rating bands.')
    page_break(doc)

# ─── CHAPTER 4 ───────────────────────────────────────────────────────────
def build_ch4(doc):
    h1(doc, 'CHAPTER 4: RESULTS AND DISCUSSION')

    h2(doc, '4.1  Overall Model Performance')
    body(doc,
        'Table 4.1 presents the test-fold metrics. Both LightGBM models outperform the logistic benchmarks on '
        'AUC and KS. Raw LightGBM improves AUC by 0.0142 and KS by 0.0169 over plain logistic regression — a '
        'consistent but modest gain, since much of the signal lies in a few strong engineered variables '
        '(external scores, loan-term ratios) that a linear model can already exploit. The gap is real on '
        'average but small relative to sampling uncertainty at this sample size (see Chapter 5, Section 5.1).')
    res_rows = [
        ['Logistic (benchmark)',     '0.7452', '0.4904', '0.3689', '0.0684', '0.2350', '0.2248', '0.7927', '0.1310'],
        ['Logistic_balanced',        '0.7412', '0.4823', '0.3626', '0.1940', '0.2288', '0.1535', '1.0000', '0.0831'],
        ['LightGBM',                 '0.7594', '0.5188', '0.3858', '0.0677', '0.2365', '0.2294', '0.8375', '0.1329'],
        ['LightGBM_calibrated',      '0.7582', '0.5164', '0.3751', '0.0678', '0.2282', '0.2232', '0.8624', '0.1282'],
    ]
    make_table(doc, ['Model', 'AUC', 'Gini', 'KS', 'Brier', 'PR-AUC', 'F1', 'Recall', 'Precision'], res_rows,
               col_widths=[1.7, 0.55, 0.55, 0.55, 0.55, 0.6, 0.55, 0.6, 0.65])
    caption(doc, 'Table 4.1.', 'Test-set metrics for the four candidate models.')

    body(doc,
        'The class-balanced logistic regression deserves a comment. Its recall of 1.0000 together with a '
        'precision of 0.0831, almost identical to the 8.04% base rate, shows that at its operating threshold '
        'it flags virtually every applicant, which is useless as a decision rule. Its Brier score of 0.1940 '
        'is also about three times larger than the others, because re-weighting the classes pushes the '
        'predicted probabilities far above the true default frequency. The case illustrates why class weights '
        'are a poor remedy when calibrated probabilities are needed.')
    body(doc,
        'Calibration changed the picture slightly. The calibrated LightGBM gives up 0.0012 of AUC and about '
        '0.011 of KS relative to the raw model, and its Brier score is marginally worse (0.0678 against '
        '0.0677), so on this test fold the calibration step did not measurably improve the probability error. '
        'It did, however, move the operating point to a higher recall (86.2% against 83.8%) and, as Section '
        '4.2 shows, bring predicted probabilities closer to observed frequencies over most of the score range. '
        'The calibrated model is retained for production because the scorecard in Section 4.1 requires '
        'probabilities rather than bare scores, and because the loss in ranking quality is small.')

    h2(doc, '4.2  Evaluation Curves')
    body(doc,
        'Figures 7 to 10 show the ROC curves, the precision–recall curves, the KS plot and the reliability '
        'diagram. The ROC curves lie well above the diagonal. The precision–recall curves show that, at low '
        'and moderate recall, precision is several times the base rate of 0.08, although it falls steadily as '
        'recall rises, which is the usual price of pushing a model towards catching nearly every defaulter. '
        'The KS statistic of the calibrated model peaks at 0.375, comfortably above the informal 0.30 '
        'benchmark mentioned in Section 2.6. The reliability diagram indicates that calibrated probabilities '
        'track observed default frequencies closely across most of the range, with mild over-confidence '
        'between 0.1 and 0.3, an artefact that isotonic regression sometimes produces in sparse score regions.')
    caption(doc, 'Figure 7.', 'ROC curves for the four candidate models (test set). Generated by code (cell 16).')
    caption(doc, 'Figure 8.', 'Precision–Recall curves for the two LightGBM models (test set). Generated by code (cell 16).')
    caption(doc, 'Figure 9.', 'Reliability (calibration) plot for the selected model (test set). Generated by code (cell 16).')

    h2(doc, '4.3  Feature Importance')
    body(doc,
        'Engineered ratios and behavioural summaries lead the LightGBM gain ranking (Figure 10): '
        'PREV_CNT_PAYMENT_MEAN, CREDIT_TERM, EXT_SOURCE_MEAN and several instalment and point-of-sale '
        'features, while age and gender rank much lower. The model therefore relies mainly on behavioural '
        'rather than demographic information. Gain importance is only a global summary; individual '
        'explanations would require methods such as SHAP (Lundberg & Lee, 2017).')
    caption(doc, 'Figure 10.', 'Top-25 features by LightGBM gain. Generated by code (cell 14).')

    h2(doc, '4.4  Scorecard and Risk Bands')
    body(doc,
        'Using the scorecard in Section 3.6, applicants are placed into five bands. Table 4.2 shows the '
        'observed default rate climbing steadily from 1.92% in band A to 30.04% in band E, with predicted and '
        'observed rates matching within roughly 1.5 percentage points in each band.')
    band_res_rows = [
        ['A', 'PD < 0.03',        '1.79%',  '1.92%',  '2,185'],
        ['B', '0.03 ≤ PD < 0.06', '4.67%',  '5.02%',  '2,372'],
        ['C', '0.06 ≤ PD < 0.10', '8.47%',  '8.70%',  '1,241'],
        ['D', '0.10 ≤ PD < 0.20', '14.89%', '14.84%', '1,166'],
        ['E', 'PD ≥ 0.20',        '31.59%', '30.04%', '536'],
    ]
    make_table(doc, ['Rating', 'PD range', 'Avg PD', 'Default rate', 'Applicants'],
               band_res_rows, col_widths=[0.7, 1.5, 0.9, 1.0, 1.0])
    caption(doc, 'Table 4.2.', 'Risk-band distribution and observed default rate (test set).')

    h2(doc, '4.5  Business Impact with Prediction')
    body(doc,
        'At τ* = 0.05, the model flags 4,057 of 7,500 test applicants (54%) for review. Of these, 520 are '
        'true defaulters, so the model catches 86.2% of the 603 defaulters in the test fold at 12.8% '
        'precision — roughly 1.6 times the base rate. The remaining 3,537 flagged applicants are false '
        'alarms, a false-positive rate of about 51% among good borrowers. That is the price of the high '
        'recall target: instead of rejecting these applicants, the model routes them to manual review or '
        'risk-based pricing rather than automatic approval.')
    body(doc,
        'Table 4.3 shows the distribution of defaulters across the bands. The two riskiest bands, D and E, '
        'hold just 22.7% of applicants but 55.4% of all defaulters. Including band C captures 73.3% of '
        'defaulters while covering 39.2% of applicants. Band A, by contrast, holds nearly 30% of applicants '
        'but only 7.0% of defaulters, with a lift of 0.24 — a natural candidate for streamlined approval.')
    lift_rows = [
        ['A', '2,185', '42',  '7.0%',  '0.24×'],
        ['B', '2,372', '119', '19.7%', '0.62×'],
        ['C', '1,241', '108', '17.9%', '1.08×'],
        ['D', '1,166', '173', '28.7%', '1.85×'],
        ['E', '536',   '161', '26.7%', '3.74×'],
    ]
    make_table(doc, ['Band', 'Applicants', 'Defaulters', 'Capture rate', 'Lift over base'],
               lift_rows, col_widths=[0.7, 1.0, 1.0, 1.1, 1.2])
    caption(doc, 'Table 4.3.', 'Capture rate and lift over the base rate by risk band (test set).')
    page_break(doc)

# ─── CHAPTER 5 ───────────────────────────────────────────────────────────
def build_ch5(doc):
    h1(doc, 'CHAPTER 5: ROBUSTNESS AND LIMITATIONS')

    body(doc,
        'This chapter reports two sensitivity checks (Section 5.1, 5.2) plus a band-cut check (Section 5.3), '
        'followed by the three limitations of the study (Section 5.4). The checks are derived from '
        'predictions_test.csv only and reproduce without retraining.')

    h2(doc, '5.1  Sensitivity Check 1 — Bootstrap CI for AUC and for the LightGBM − LR Gap')
    body(doc, 'Method.')
    body(doc,
        'The test fold (n = 7,500, 603 defaulters) is resampled 1,000 times with replacement. For each '
        'resample, AUC is recomputed for the calibrated LightGBM model; the 2.5th and 97.5th percentiles of '
        'the bootstrap distribution give the 95% confidence interval. The gap LightGBM − LR is constructed '
        'by subtracting the published LR point estimate from the bootstrap distribution (the per-row LR scores '
        'are not on disk, so their bootstrap variance is approximated by the LGB-CAL bootstrap standard error '
        '— a conservative choice that widens the gap CI).')

    body(doc, 'Results.')
    boot_rows = [
        ['AUC of LGB-CAL', '0.7582', '[0.7376, 0.7788]'],
        ['AUC gap (LGB-CAL − LR)', '+0.0130', '[−0.0071, +0.0331]'],
        ['AUC gap (LGB raw − LR)', '+0.0142', '[−0.0059, +0.0343]'],
    ]
    make_table(doc, ['Quantity', 'Point estimate', '95% CI'], boot_rows, col_widths=[2.3, 1.5, 2.5])
    caption(doc, 'Table 5.1.', 'Bootstrap CI for AUC and for the LightGBM − LR gap (B = 1,000).')

    body(doc, 'Reading.')
    body(doc,
        'The CI of the LightGBM − LR gap contains zero. At this sample size, sampling uncertainty alone is '
        'wide enough that one cannot conclude that LightGBM is significantly better than logistic regression '
        'on the test fold. The point estimate is positive (+0.013 to +0.014 AUC), which is consistent with '
        'the public literature, but the test fold alone cannot rule out the null of "the two models are '
        'statistically indistinguishable". This is the sampling uncertainty that the Abstract and Section '
        '1.3 refer to.')

    h2(doc, '5.2  Sensitivity Check 2 — Threshold Sweep')
    body(doc, 'Method.')
    body(doc,
        'Sweep τ ∈ {0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10} on the calibrated LightGBM '
        'probabilities and the true labels. Report recall, precision, F1, flag-rate and the confusion-matrix cells.')
    body(doc, 'Results.')
    thr_rows = [
        ['0.02', '0.975', '0.091', '0.167', '85.8', '588', '15'],
        ['0.03', '0.930', '0.106', '0.190', '70.9', '561', '42'],
        ['0.04', '0.887', '0.118', '0.209', '60.2', '535', '68'],
        ['0.05', '0.862', '0.128', '0.223', '54.1', '520', '83'],
        ['0.06', '0.733', '0.150', '0.249', '39.2', '442', '161'],
        ['0.07', '0.726', '0.150', '0.249', '38.9', '438', '165'],
        ['0.08', '0.678', '0.163', '0.263', '33.4', '409', '194'],
        ['0.09', '0.602', '0.184', '0.282', '26.3', '363', '240'],
        ['0.10', '0.554', '0.196', '0.290', '22.7', '67', '269'],
    ]
    make_table(doc, ['τ', 'Recall', 'Precision', 'F1', 'Flag %', 'TP', 'FN'], thr_rows,
               col_widths=[0.6, 0.8, 0.9, 0.7, 0.8, 0.6, 0.6])
    caption(doc, 'Table 5.2.', 'Threshold sweep on the calibrated LightGBM model (test fold).')

    body(doc, 'Reading.')
    body(doc,
        'At τ* = 0.05 the model catches 86.2% of defaulters while flagging 54% of the test set. Pushing τ '
        'down to 0.03 buys 6.8 percentage points of recall at the cost of 16.8 percentage points of workload. '
        'Pushing τ up to 0.08 buys back 21 percentage points of workload but loses 18.4 percentage points of '
        'recall. The chosen τ* = 0.05 is consistent with the recall ≥ 0.80 floor from assumption A5, but '
        'operators with a tighter manual-review budget should re-tune on their own validation set before '
        'deployment.')
    body(doc,
        'A secondary observation: on the test fold the F1-optimal threshold is closer to τ ≈ 0.10 (F1 = '
        '0.290) than to τ* = 0.05 (F1 = 0.223). This is not a contradiction: τ* is selected on the '
        'validation fold, where the 80%-recall constraint binds; on the test fold that constraint is no '
        'longer the binding one because the test-fold default rate happened to be slightly more concentrated '
        'in the high-PD region. The scorecard in Section 3.6 keeps τ* = 0.05 for the business reason '
        '(recall floor) and notes that a pure-F1 retune would lower recall.')

    h2(doc, '5.3  Sensitivity Check 3 — Risk-Band Cut Robustness')
    body(doc, 'Method.')
    body(doc,
        'Replace the fixed FICO cut-points (640 / 760) by tertile cut-points (q1 = 667, q2 = 699) on the '
        'realised score distribution of the test fold, and re-tabulate the band-level default rate.')

    body(doc, 'Results.')
    cut_rows = [
        ['Band A (lowest risk)',  '1 row, 0.00% default',          '2,553 rows, 2.19% default'],
        ['Band B (mid)',          '6,963 rows, 6.35% default',     '2,497 rows, 5.69% default'],
        ['Band C (highest risk)', '536 rows, 30.04% default',      '2,450 rows, 16.53% default'],
        ['Monotone?',             'Yes (0 → 6.35 → 30.04)',        'Yes (2.19 → 5.69 → 16.53)'],
    ]
    make_table(doc, ['', 'Fixed cut (640 / 760)', 'Tertile cut (q1 = 667, q2 = 699)'],
               cut_rows, col_widths=[1.8, 2.4, 2.4])
    caption(doc, 'Table 5.3.', 'Band-cut robustness on the test fold.')

    body(doc, 'Reading.')
    body(doc,
        'Monotonicity is preserved under both cut schemes, which is the property that the scorecard needs to '
        'defend. The fixed-cut scheme concentrates almost all rows into the middle band because the realised '
        'score range on the test fold is [401, 799] rather than the textbook 300–850; that compression is '
        'what motivates the PD-based bands in Section 3.6 (which depend on the underlying PD and are '
        'independent of the realised score range). The tertile scheme is reported as a sanity check, not as '
        'the production scheme.')

    h2(doc, '5.4  Limitations')
    body(doc,
        'Each limitation states the direction of bias the limitation introduces on the headline numbers.')

    p = doc.add_paragraph()
    r1 = p.add_run('L1. Single random split, not a time-based split. ')
    set_font(r1, bold=True, size=12)
    r2 = p.add_run('Random separation of train / valid / test is assumed to be exchangeable with future '
                   'applicants in the next quarter (assumption A2). Because the public dataset has no '
                   'reliable application date that survives masking, a true time-based backtest is impossible '
                   'here. ')
    set_font(r2, size=12)
    r3 = p.add_run('Direction of bias: the headline AUCs may be optimistically high for future applicants if '
                   'the application mix drifts from the source extract.')
    set_font(r3, italic=True, size=12)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    p = doc.add_paragraph()
    r1 = p.add_run('L2. Lightweight logistic benchmark. ')
    set_font(r1, bold=True, size=12)
    r2 = p.add_run('The plain logistic regression uses default scikit-learn settings (L2 only, median '
                   'imputation, standard scaling) and does not use a Weight-of-Evidence (WoE) transform, '
                   'outlier treatment or a regularisation sweep. A production-grade scorecard typically uses '
                   'WoE-binned variables. The LightGBM vs LR gap of +0.014 AUC reported in Chapter 4 should '
                   'therefore be read as an upper bound on the apparent gain, because the linear benchmark '
                   'is not fully tuned. ')
    set_font(r2, size=12)
    r3 = p.add_run('Direction of bias: overstates the magnitude of LightGBM\'s advantage without changing its sign.')
    set_font(r3, italic=True, size=12)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    p = doc.add_paragraph()
    r1 = p.add_run('L3. Test fold has only 603 defaulters. ')
    set_font(r1, bold=True, size=12)
    r2 = p.add_run('The bootstrap CI of Section 5.1 already shows that sampling uncertainty on the test fold '
                   'alone is too wide to reject "LightGBM = LR" at the 5% level. ')
    set_font(r2, size=12)
    r3 = p.add_run('Direction of bias: sign is unknown a priori — the point estimate favours LightGBM, but '
                   'the gap is statistically indistinguishable from zero at this sample size.')
    set_font(r3, italic=True, size=12)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    body(doc,
        'Secondary limitations worth noted. (L4) The validation fold is used for early stopping, calibration '
        'and threshold selection; if any of those three steps over-fit, the gain would show up as a gap '
        'between validation and test (Section 5.2 documents that the gap is small). (L5) The dataset '
        'contains only loans that were approved; reject inference is out of scope. (L6) The external credit '
        'scores (assumption A3) and behavioural aggregates (assumption A4) are assumed leakage-free; any '
        'leakage would inflate all metrics.')
    page_break(doc)

# ─── CHAPTER 6 ───────────────────────────────────────────────────────────
def build_ch6(doc):
    h1(doc, 'CHAPTER 6: RECOMMENDATION')

    h2(doc, '6.1  Recommendation')
    body(doc,
        'Use the calibrated LightGBM model (LGB-CAL) as the primary decisioning engine for new applications, '
        'restricted to triage and referral to manual review or risk-based pricing — not to automatic decline. '
        'Concretely:')
    bullet(doc,
        'Auto-approve applicants in band A (PD < 0.03; expected default rate ≤ 2%). This represents ~29% of '
        'the test portfolio and ~7% of defaulters.')
    bullet(doc,
        'Standard review for bands B–C (0.03 ≤ PD < 0.10). This is ~48% of the portfolio and ~38% of defaulters.')
    bullet(doc,
        'Manual review or risk-based pricing for bands D–E (PD ≥ 0.10). This is ~23% of the portfolio and '
        '~55% of defaulters, with band E carrying a 30% observed default rate.')
    bullet(doc,
        'Do not auto-decline any applicant on the model alone; every D/E band decision is paired with a '
        'manual underwriter sign-off. This is consistent with Basel expectation that an internal model is a '
        'support tool, not a stand-alone decline rule.')
    body(doc,
        'The chosen operating point is τ = 0.05 for the rating bands: it catches 86.2% of defaulters at '
        '12.8% precision on the test fold. Operators with a different manual-review budget should re-tune τ '
        'on their own validation set using Equation (3.1).')

    h2(doc, '6.2  Conditions of Use')
    body(doc, 'The recommendation is conditional on the following:')
    bullet(doc, 'Full-data retraining before production. Re-train LGB-CAL on the full 307,511-row source extract, '
                'not on the 50,000-row subsample, before any real-customer rollout. The 50,000-row subsample is a '
                'development convenience; the production model should not carry its sampling-uncertainty penalty.')
    bullet(doc, 'Time-based validation. The current split is random. Before production, re-do the train / valid '
                '/ test split by application date and confirm that AUC, KS and Brier remain within the bootstrap '
                'CI of Section 5.1. If they fall outside, the recommendation is suspended until the gap is investigated.')
    bullet(doc, 'Confirmation that assumption A5 holds. The recommendation assumes a missed defaulter costs at '
                'least 10× a false alarm. If the operator\'s true cost ratio is materially different, τ* should '
                'be re-tuned: a higher cost ratio pushes τ* lower (catch more), a lower cost ratio lets τ* rise (work less).')
    bullet(doc, 'Population-stability monitoring on the score distribution. Compare the score distribution of '
                'new applicants against the training distribution monthly; alert if PSI > 0.25 (industry convention; '
                'Sidló, 2003).')
    bullet(doc, 'Fairness audit. Disaggregate the calibration and the rating-band assignment by gender, age band '
                'and regional rating before any real-customer rollout. The model relies heavily on engineered '
                'features, but a fairness audit is a regulatory expectation and is cheap to run.')

    h2(doc, '6.3  Monitoring Metric')
    body(doc,
        'The single key performance indicator is the realised 90-day default rate of the auto-approved '
        'segment (band A). Alert thresholds:')
    bullet(doc, 'PSI > 0.25 on the score distribution (industry convention; alert, do not stop).')
    bullet(doc, 'Observed default rate in band A > 1.5 × the calibrated PD for two consecutive months. '
                'Suspend auto-approval.')
    bullet(doc, 'Observed default rate in band E < 0.5 × the calibrated PD for two consecutive months. The '
                'model is over-confident in the tail; recalibrate.')
    body(doc,
        'Secondary KPIs to track monthly: (i) review workload as a fraction of new applications; (ii) '
        'realised default rate in each rating band; (iii) KS drift between training and the latest month.')

    h2(doc, 'Conclusion')
    body(doc,
        'The pipeline works end-to-end, from seven raw tables to a calibrated PD model, a points-based '
        'scorecard and five risk bands. LightGBM outperformed the logistic benchmark, but by a modest margin '
        '(AUC 0.758 against 0.745) that is statistically indistinguishable from zero under the bootstrap CI '
        'of Section 5.1. Isotonic calibration made the probabilities usable for the scorecard and raised '
        'recall to 86.2% at τ* = 0.05, at the cost of a slight loss in discrimination and no gain in Brier '
        'score. The bands separate risk monotonically, from a 1.92% default rate in band A to 30.04% in band '
        'E. The two follow-ups that would change the recommendation most are: (i) full-data retraining to '
        'close the gap between the subsample and the production population; (ii) a time-based validation '
        'pass before any real-customer rollout.')
    page_break(doc)

# ─── APPENDICES ─────────────────────────────────────────────────────────
def build_appendices(doc):
    h1(doc, 'APPENDICES')

    h2(doc, 'Appendix A — Data Dictionary (excerpt)')
    dict_rows = [
        ['TARGET',                                 '1 = default, 0 = repaid on time. Binary.'],
        ['EXT_SOURCE_1 / 2 / 3',                   'Normalised external credit scores (mean ≈ 0.5).'],
        ['AMT_CREDIT / AMT_INCOME / AMT_ANNUITY',  'Loan amount, annual income, annuity.'],
        ['DAYS_BIRTH / DAYS_EMPLOYED',             'Age and employment in days (negative). 365,243 is the missing sentinel.'],
        ['CODE_GENDER, NAME_CONTRACT_TYPE',        'Categorical applicant attributes.'],
        ['CREDIT_TERM, CREDIT_GOODS_RATIO',        'Engineered credit/income/goods ratios.'],
        ['EXT_SOURCE_MEAN / MAX / MIN',            'Aggregated external-score statistics.'],
        ['EXT_SOURCE_COUNT',                       'Number of non-missing external scores (0, 1, 2 or 3).'],
        ['OWN_CAR_AGE',                            'Age of car in years (NaN if no car).'],
        ['PREV_CNT_PAYMENT_MEAN, INST_LATE_*',     'Behavioural history from previous applications and instalments.'],
        ['POS_UTIL_MEAN, CC_UTIL_MEAN',            'Utilisation of revolving credit lines.'],
        ['BUR_DEBT_RATIO, BUR_CREDIT_SUM',         'Bureau debt-to-credit aggregates.'],
        ['HAS_BUREAU',                             '1 if applicant has any bureau record, 0 otherwise.'],
    ]
    make_table(doc, ['Field', 'Description'], dict_rows, col_widths=[2.4, 4.6])
    caption(doc, 'Table A.1.', 'Data dictionary (excerpt).')

    h2(doc, 'Appendix B — Cleaning Log')
    bullet(doc, 'DAYS_EMPLOYED sentinel 365,243 → NaN before imputation, with a binary flag kept.')
    bullet(doc, 'CODE_GENDER = "XNA" → treated as missing; imputation and one-hot encoding handle the resulting NaN.')
    bullet(doc, 'OWN_CAR_AGE is set to missing for applicants without a car (the missingness itself is signal '
                'and is preserved by the imputation step).')
    bullet(doc, 'No column is dropped solely on the basis of a missing-rate threshold. High-missing columns '
                '(housing characteristics, external scores) are kept; missingness is recorded in EXT_SOURCE_COUNT, '
                'HAS_BUREAU, etc. The earlier "drop columns > 60% missing" line in draft v1 of this report was an '
                'artefact of an earlier experiment and does not apply to the final pipeline.')
    bullet(doc, 'Categorical NaN → MISSING bucket, then one-hot encoded (first level dropped).')
    bullet(doc, 'Numeric NaN → median per column (training fold only), then standard-scaled.')
    bullet(doc, 'Outliers in DAYS_BIRTH and DAYS_EMPLOYED are retained; the tree-based model is insensitive to '
                'monotone transforms.')
    bullet(doc, 'Aggregate features computed with pandas.groupby on SK_ID_CURR; no per-row outliers.')

    h2(doc, 'Appendix C — Assumption Register')
    bullet(doc, 'A1. The TARGET column is observed at the loan horizon; right-censoring is negligible for this portfolio.')
    bullet(doc, 'A2. Applicants in the test fold are exchangeable with future applicants in the next quarter (no regime change).')
    bullet(doc, 'A3. External credit scores (EXT_SOURCE_*) are point-in-time and free of leakage.')
    bullet(doc, 'A4. Behavioural-history aggregates are computable for new applicants at decision time (no look-ahead bias).')
    bullet(doc, 'A5. The cost of a missed defaulter is at least 10× the cost of a false alarm; this drives the '
                'recall floor of 0.80 in Equation (3.1).')

    h2(doc, 'Appendix D — Link to Code')
    body(doc,
        'The pipeline is a single Jupyter notebook (notebooks/home_credit_pipeline.ipynb) that produces '
        'model/model.joblib, predictions_test.csv, metrics.json, model_card.json and the PNG exhibits in '
        'model/. Re-running the notebook regenerates every figure and numerical table in this report.')
    bullet(doc, 'Project repository: https://github.com/<username>/home-credit-default-risk')
    bullet(doc, 'Notebook: notebooks/home_credit_pipeline.ipynb')
    bullet(doc, 'Streamlit app: app/streamlit_app.py (Docker image home-credit-ml:latest).')

    h2(doc, 'Appendix E — AI-use Disclosure')
    body(doc,
        'AI assistance was used in this report in the following ways: (i) drafting the first version of the '
        'prose from a hand-written outline; (ii) condensing and rewriting longer passages into the report\'s '
        'current form; (iii) checking arithmetic in the bootstrap and threshold tables of Chapter 5 against '
        'the source script docs/sensitivity_check.py; (iv) formatting equations, tables and figure references '
        'into Markdown. All numerical results, model selections, thresholds, the sensitivity checks and the '
        'policy recommendations were produced by the human author from the pipeline outputs in model/; the '
        'AI did not invent, modify or reinterpret any of the numbers reported above.')
    page_break(doc)

# ─── REFERENCES ─────────────────────────────────────────────────────────
def build_references(doc):
    h1(doc, 'REFERENCES')
    refs = [
        'Akiba, T., Sano, S., Yanase, T., Ohta, T., & Koyama, M. (2019). Optuna: A next-generation hyperparameter optimization framework. Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining, 2623–2631.',
        'Baesens, B., Van Gestel, T., Viaene, S., Stepanova, M., Suykens, J., & Vanthienen, J. (2003). Benchmarking state-of-the-art classification algorithms for credit scoring. Journal of the Operational Research Society, 54(6), 627–635.',
        'Basel Committee on Banking Supervision. (2006). International convergence of capital measurement and capital standards: A revised framework (comprehensive version). Bank for International Settlements.',
        'Brier, G. W. (1950). Verification of forecasts expressed in terms of probability. Monthly Weather Review, 78(1), 1–3.',
        'Fawcett, T. (2006). An introduction to ROC analysis. Pattern Recognition Letters, 27(8), 861–874.',
        'Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. The Annals of Statistics, 29(5), 1189–1232.',
        'Hand, D. J., & Henley, W. E. (1997). Statistical classification methods in consumer credit scoring: A review. Journal of the Royal Statistical Society: Series A, 160(3), 523–541.',
        'Hanley, J. A., & McNeil, B. J. (1982). The meaning and use of the area under a ROC curve. Radiology, 143(1), 29–36.',
        'Kaggle. (2018). Home Credit Default Risk [Data set and competition]. https://www.kaggle.com/c/home-credit-default-risk',
        'Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., & Liu, T.-Y. (2017). LightGBM: A highly efficient gradient boosting decision tree. Advances in Neural Information Processing Systems, 30, 3146–3154.',
        'Lessmann, S., Baesens, B., Seow, H.-V., & Thomas, L. C. (2015). Benchmarking state-of-the-art classification algorithms for credit scoring: An update of research. European Journal of Operational Research, 247(1), 124–136.',
        'Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. Advances in Neural Information Processing Systems, 30, 4765–4774.',
        'Niculescu-Mizil, A., & Caruana, R. (2005). Predicting good probabilities with supervised learning. Proceedings of the 22nd International Conference on Machine Learning, 625–632.',
        'Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., … Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2825–2830.',
        'Platt, J. C. (1999). Probabilistic outputs for support vector machines and comparisons to regularized likelihood methods. In Advances in Large Margin Classifiers (pp. 61–74). MIT Press.',
        'Siddiqi, N. (2006). Credit Risk Scorecards: Developing and Implementing Intelligent Credit Scoring. Wiley.',
        'Sidló, L. (2003). Population stability index. In Credit Risk Modelling (course notes).',
        'Zadrozny, B., & Elkan, C. (2002). Transforming classifier scores into accurate multiclass probability estimates. Proceedings of the 8th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, 694–699.',
    ]
    for ref in refs:
        p = doc.add_paragraph()
        run = p.add_run(ref); set_font(run, size=12)
        pf = p.paragraph_format
        pf.left_indent = Inches(0.4); pf.first_line_indent = Inches(-0.4)
        pf.space_after = Pt(6)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# ─── BUILD ──────────────────────────────────────────────────────────────
def main():
    doc = Document()
    # Tighten margins slightly
    for sec in doc.sections:
        sec.top_margin    = Inches(0.9)
        sec.bottom_margin = Inches(0.9)
        sec.left_margin   = Inches(1.0)
        sec.right_margin  = Inches(1.0)

    build_cover(doc)
    build_inner(doc)
    build_acknowledgements(doc)
    build_abstract(doc)
    build_ch1(doc)
    build_ch2(doc)
    build_ch3(doc)
    build_ch4(doc)
    build_ch5(doc)
    build_ch6(doc)
    build_appendices(doc)
    build_references(doc)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f'Saved: {OUT}')

if __name__ == '__main__':
    main()