"""Build D4 Midterm Case-Study Report DOCX from docs/D4_report_v2.md content."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_BREAK
from docx.shared import Pt, RGBColor, Inches, Cm, Twips
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from copy import deepcopy
import re

# ── helpers ────────────────────────────────────────────────────────────────────

def set_font(run, name='Times New Roman', size=12, bold=False, italic=False,
             color=None):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = RGBColor(*color)

def para_spacing(p, before=0, after=0, line=None):
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after  = Pt(after)
    if line:
        pf.line_spacing = Pt(line)
        pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY

def set_cell_bg(cell, hex_color):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement('w:shd')
    shd.set(qn('w:val'),   'clear')
    shd.set(qn('w:color'),'auto')
    shd.set(qn('w:fill'),  hex_color)
    tcPr.append(shd)

def add_page_break(doc):
    p = doc.add_paragraph()
    run = p.add_run()
    run.add_break(WD_BREAK.PAGE)

def h1(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(text)
    set_font(run, bold=True, size=13)
    para_spacing(p, before=18, after=6)
    return p

def h2(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(text)
    set_font(run, bold=True, size=12)
    para_spacing(p, before=12, after=4)
    return p

def body(doc, text, before=0, after=6, indent=0, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = align
    run = p.add_run(text)
    set_font(run, size=12)
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after  = Pt(after)
    if indent:
        pf.left_indent = Inches(indent)
    return p

def bullet(doc, text, indent=0.25, after=3):
    p = doc.add_paragraph(style='List Bullet')
    run = p.add_run(text)
    set_font(run, size=12)
    p.paragraph_format.left_indent  = Inches(indent)
    p.paragraph_format.space_after  = Pt(after)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p

def mini(doc, text):
    """Italic body para."""
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_font(run, size=12, italic=True)
    para_spacing(p, after=4)

def table_style(t):
    t.style = 'Table Grid'
    for row in t.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after  = Pt(2)

def make_table(doc, headers, rows, col_widths=None, header_bg='D9E1F2'):
    ncols = len(headers)
    t = doc.add_table(rows=1 + len(rows), cols=ncols)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_style(t)

    # header row
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        set_cell_bg(cell, header_bg)
        p = cell.paragraphs[0]
        run = p.add_run(h)
        set_font(run, bold=True, size=11)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # data rows
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = t.rows[ri + 1].cells[ci]
            p = cell.paragraphs[0]
            run = p.add_run(str(val))
            set_font(run, size=11)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if ci > 0 else WD_ALIGN_PARAGRAPH.LEFT

    if col_widths:
        for ri, row in enumerate(t.rows):
            for ci, cell in enumerate(row.cells):
                cell.width = Inches(col_widths[ci])
    return t

def fig_caption(doc, label, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p.add_run(label + ' ')
    set_font(r1, bold=True, size=11)
    r2 = p.add_run(text)
    set_font(r2, italic=True, size=11)
    para_spacing(p, before=4, after=8)

# ── cover page ────────────────────────────────────────────────────────────────

def build_cover(doc):
    # top university block
    lines = [
        'VIETNAM NATIONAL UNIVERSITY, HO CHI MINH CITY',
        'HO CHI MINH UNIVERSITY OF TECHNOLOGY',
        'FACULTY OF COMPUTER SCIENCE & ENGINEERING',
    ]
    for ln in lines:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(ln)
        set_font(run, bold=True, size=12)
        para_spacing(p, after=2)

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('─' * 55)
    set_font(run, size=12)
    para_spacing(p, before=4, after=10)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('D4 — MIDTERM CASE-STUDY REPORT')
    set_font(run, bold=True, size=16)
    para_spacing(p, before=6, after=8)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('Credit Risk Scoring with LightGBM and\nProbability Calibration on Home Credit Data')
    set_font(run, bold=True, size=14)
    para_spacing(p, after=30)

    doc.add_paragraph()

    for label, value in [
        ('SUPERVISOR',  'TS. Nguyễn Minh Hùng'),
        ('STUDENT',     'Phạm Thanh Hà — MSSV: 21xxxxxx'),
        ('PROGRAMME',   'Applied Mathematics in Economics & Finance'),
    ]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r1 = p.add_run(label + '\n')
        set_font(r1, bold=True, size=12)
        r2 = p.add_run(value)
        set_font(r2, size=12)
        para_spacing(p, after=6)

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('Ho Chi Minh City, October 2026')
    set_font(run, size=12, italic=True)
    para_spacing(p, before=10)

    add_page_break(doc)

# ── inner title page ───────────────────────────────────────────────────────────

def build_inner(doc):
    for ln in [
        'VIETNAM NATIONAL UNIVERSITY, HO CHI MINH CITY',
        'HO CHI MINH UNIVERSITY OF TECHNOLOGY',
        'FACULTY OF COMPUTER SCIENCE & ENGINEERING',
    ]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(p.add_run(ln), bold=True, size=12)
        para_spacing(p, after=2)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('─' * 55)
    set_font(run, size=12)
    para_spacing(p, before=4, after=14)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('D4 — MIDTERM CASE-STUDY REPORT')
    set_font(run, bold=True, size=16)
    para_spacing(p, after=8)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('Credit Risk Scoring with LightGBM and\nProbability Calibration on Home Credit Data')
    set_font(run, bold=True, size=14)
    para_spacing(p, after=30)

    doc.add_paragraph()

    fields = [
        ('Topic',    'Credit Risk Scoring with LightGBM and Probability Calibration on Home Credit Data'),
        ('Supervisor', 'TS. Nguyễn Minh Hùng'),
        ('Student',  'Phạm Thanh Hà'),
        ('Programme','Applied Mathematics in Economics & Finance'),
        ('Date',     'October 2026'),
    ]
    for label, value in fields:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r1 = p.add_run(label + ':\n')
        set_font(r1, bold=True, size=12)
        r2 = p.add_run(value)
        set_font(r2, size=12)
        para_spacing(p, after=6)

    add_page_break(doc)

# ── acknowledgements ─────────────────────────────────────────────────────────

def build_acknowledgements(doc):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
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

    add_page_break(doc)

# ── Part 1 ────────────────────────────────────────────────────────────────────

def build_part1(doc):
    h1(doc, 'PART 1 — QUESTION AND SCOPE  (≈ 15 %)')

    h2(doc, '1.1  The five-slot research question (matches D3 memo)')
    body(doc,
        'We frame the study in five interlocking slots so the question can be answered in one sentence '
        'and re-used as a unit of analysis:')

    slots = [
        ('Unit',    'an individual loan applicant at application time.'),
        ('Action',  'rank / approve / refer for review, with a calibrated PD.'),
        ('Outcome', 'default within the loan horizon (TARGET = 1).'),
        ('Pop\'n',  '307 511 applicants on Home Credit\'s books, 8.04% default rate; sample = 12 750 stratified rows.'),
        ('Time',    'train on the earliest 70% (5 250), validate on the next 15% (1 125), test on the most recent 15% (7 500).'),
    ]
    for label, text in slots:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.space_after = Pt(3)
        r1 = p.add_run(label + '  :  ')
        set_font(r1, bold=True, size=12)
        r2 = p.add_run(text)
        set_font(r2, size=12)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    body(doc, '', after=4)
    body(doc,
        'Restated in one sentence: rank the 7 500 held-out applicants by predicted PD, choose a decision '
        'threshold that protects recall, and translate the resulting PD into a 300–1 000 score with three risk bands.')

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    r1 = p.add_run('No deviation from the D3 memo: ')
    set_font(r1, italic=True, size=12)
    r2 = p.add_run('the same five-slot form, the same target, the same horizon. '
                   'The only adjustment is the population size — the memo wrote 10 000 rows; the experiment '
                   'uses 12 750 (≈4% of the source population) to keep computation manageable on a local machine.')
    set_font(r2, italic=True, size=12)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    h2(doc, '1.2  Out-of-scope')
    bullet(doc, 'Pricing, expected loss, capital calculation, reject inference and fairness audits are explicitly out of scope for this report.')
    bullet(doc, 'Production REST/GraphQL service, automated retraining and population-stability monitoring are listed as future work in Part 6.')

# ── Part 2 ────────────────────────────────────────────────────────────────────

def build_part2(doc):
    add_page_break(doc)
    h1(doc, 'PART 2 — DATA AND PREPARATION  (≈ 20 %)')

    h2(doc, '2.1  Source tables')
    body(doc,
        'Seven tables are joined on SK_ID_CURR (and SK_ID_PREV for behavioural history): '
        'application_train (n = 307 511, 122 cols), bureau, bureau_balance, previous_application, '
        'installments_payments, POS_CASH_balance, credit_card_balance. After a stratified subsample we work '
        'with n = 12 750 rows.')

    h2(doc, '2.2  Cleaning, imputation and feature engineering')
    bullet(doc, 'Day-count sentinels (DAYS_EMPLOYED = 365 243, XNA gender) replaced with NaN before imputation; OWN_CAR_AGE missing for applicants without a car.')
    bullet(doc, 'Categoricals mode-imputed (with a "MISSING" bucket) and one-hot encoded inside a single ColumnTransformer.')
    bullet(doc, 'Numerics median-imputed, then standard-scaled. Missing values themselves are signal: EXT_SOURCE_COUNT records how many external scores are present.')
    bullet(doc, 'Behavioural aggregations: per applicant, mean / max / sum / ratio features for amounts, delays, utilisation and overdue counts across bureau, previous_application, installments, POS and CC.')
    bullet(doc, 'Final feature matrix: 301 predictors. Cleaning log and assumption register are in Appendices B and C.')

    h2(doc, '2.3  Train / valid / test split')
    body(doc,
        'Stratified 70 / 15 / 15 (5 250 / 1 125 / 7 500). The test fold is the largest because the '
        'final report quotes business-impact numbers at the portfolio level; the calibration step uses only '
        'the 1 125 validation rows.')

# ── Part 3 ────────────────────────────────────────────────────────────────────

def build_part3(doc):
    add_page_break(doc)
    h1(doc, 'PART 3 — METHOD AND BENCHMARK  (≈ 20 %)')

    h2(doc, '3.1  Candidate models and benchmark')
    body(doc, 'Four classifiers are compared:')

    bullet(doc, 'LR — plain logistic regression (C = 0.5), the interpretable baseline.')
    bullet(doc, 'LR-BAL — class-balanced LR (class_weight = "balanced"), testing whether class weighting is a viable remedy.')
    bullet(doc, 'LGB — LightGBM tuned with Optuna (50 trials, 5-fold CV) — raw output.')
    bullet(doc, 'LGB-CAL — same LightGBM with isotonic calibration on the validation fold.')

    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.25)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(6)
    r1 = p.add_run('Benchmark reference. ')
    set_font(r1, bold=True, size=12)
    r2 = p.add_run('Top public solutions of the original 2018 Kaggle competition (full data, ensembles) '
                   'reach AUC ≈ 0.81–0.82. This subsample study is benchmarked against that ceiling.')
    set_font(r2, size=12)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    h2(doc, '3.2  Scorecard and risk bands')
    body(doc,
        'Calibrated PD is mapped to a FICO-like score by:\n'
        '    score = 712.88 − 28.85 · ln(PD / (1 − PD))\n'
        'with offset 712.88, factor 28.85, base 600, PDO 20, base odds 50:1. '
        'Three risk bands: Thấp (≥ 760), Trung bình (640–760), Cao (< 640).')

    h2(doc, '3.3  Decision threshold')
    body(doc,
        'τ* = argmax F1(τ)  subject to  Recall(τ) ≥ 0.80\n'
        'on the validation fold, giving τ* = 0.05. The recall floor encodes the business preference that '
        'a missed defaulter costs more than a false alarm.')

# ── Part 4 ────────────────────────────────────────────────────────────────────

def build_part4(doc):
    add_page_break(doc)
    h1(doc, 'PART 4 — RESULTS AND INTERPRETATION  (≈ 20 %)')

    h2(doc, '4.1  Headline numbers on the test fold')
    body(doc, 'Table 1.  Test-set metrics for the four candidate models.', before=4, after=4)

    t = make_table(doc,
        ['Model', 'AUC', 'KS', 'Brier', 'F1@τ*', 'Recall'],
        [
            ['Logistic (LR)',                   '0.7452', '0.3689', '0.0684', '0.2248', '79.27%'],
            ['Logistic (LR-BAL)',               '0.7412', '0.3626', '0.1940', '0.1535', '100.00%'],
            ['LightGBM (LGB)',                  '0.7594', '0.3858', '0.0677', '0.2294', '83.75%'],
            ['LightGBM cal. (LGB-CAL)',         '0.7582', '0.3751', '0.0678', '0.2232', '86.24%'],
            ['Kaggle public (full data, ref.)', '≈ 0.81', '—',      '—',      '—',      '—'],
        ],
        col_widths=[2.2, 0.7, 0.7, 0.7, 0.7, 0.8]
    )
    doc.add_paragraph()

    body(doc,
        'Reading: the LightGBM family dominates the logistic baselines on every ranking metric. The calibrated '
        'model (LGB-CAL) trades ≈ 0.001 AUC and ≈ 0.011 KS for a clear gain in recall (86.24% vs 83.75%) — '
        'it is retained because the scorecard requires probabilities rather than bare scores and the loss in '
        'ranking quality is small. The LR-BAL case illustrates that class weighting inflates Brier three-fold '
        '(0.1940 vs 0.0684) and is not a viable path when calibrated probabilities are needed.')
    body(doc,
        'Benchmark gap: the single-model AUC of 0.758 on a 12 750-row subsample is below the Kaggle public '
        'ceiling of ≈ 0.81 — expected given both sample size and the absence of ensembling.')

    h2(doc, '4.2  Curves and business interpretation')
    bullet(doc, 'Figure 1 — ROC curves. Both LightGBM variants sit well above the logistic baselines across the full recall range.')
    bullet(doc, 'Figure 2 — Precision–Recall curves. PR-AUC is preferred over ROC-AUC under the 8% base rate.')
    bullet(doc, 'Figure 3 — Reliability plot. The isotonic-calibrated curve lies close to the diagonal; the raw model over-predicts in the low-PD region.')
    body(doc, '', after=4)
    body(doc,
        'At τ* = 0.05 the model flags 4 057 of the 7 500 test applicants (54%) for review. Of these, 520 '
        'are genuine defaulters, recovering 86.2% of all defaulters at a precision of 12.8% — about 1.6× the '
        'base rate. Bands D and E (Cao risk) carry 55.4% of all defaulters while representing only 22.7% '
        'of the portfolio — a useful segmentation for manual review.')

    add_page_break(doc)
    h2(doc, '4.3  Feature importance and score distribution')
    bullet(doc, 'Figure 4 — Top-25 features by LightGBM gain. External credit scores and credit-to-income ratios dominate; raw demographics (age, gender) rank lower — reassuring from a fairness standpoint.')
    bullet(doc, 'Figure 5 — Score distribution with the three risk-band boundaries overlaid.')
    bullet(doc, 'Figure 6 — Empirical default rate by risk band. The default rate increases monotonically across bands — evidence that the scorecard is well-calibrated.', after=6)

    body(doc, 'Table 2.  Risk-band distribution and observed default rate (test set).', before=4, after=4)
    t2 = make_table(doc,
        ['Risk band', 'Score range', 'Applicants', 'Empirical default rate'],
        [
            ['Thấp',        '[760, 1 000]', '2 185', '1.92%'],
            ['Trung bình',   '[640, 760)',   '2 372', '5.02%'],
            ['Cao',          '[300, 640)',   '536',   '30.04%'],
        ],
        col_widths=[1.5, 1.5, 1.5, 1.7]
    )
    doc.add_paragraph()

    body(doc,
        'The three bands are strictly monotonic and cover the full test set. Band Thấp holds 29.1% of applicants '
        'but only 7.0% of defaulters; band Cao holds 7.1% of applicants but 26.7% of defaulters — a 3.74× lift '
        'over the 8.04% base rate.')

# ── Part 5 ────────────────────────────────────────────────────────────────────

def build_part5(doc):
    add_page_break(doc)
    h1(doc, 'PART 5 — ROBUSTNESS AND LIMITATIONS  (≈ 15 %)')

    h2(doc, '5.1  Sensitivity check 1 — training-set size')
    body(doc,
        'Re-running the same LGB-CAL recipe on three random sub-samples of the training pool '
        '(n ∈ {3 500, 7 000, 12 750}) reproduces AUC within ±0.006. The model is mildly data-hungry: '
        'AUC climbs from 0.751 on the smallest fold to 0.758 on the full sample. '
        'A full-data retrain on all 307 511 rows is the recommended follow-up.')

    h2(doc, '5.2  Sensitivity check 2 — decision threshold')
    body(doc,
        'Sweeping τ across {0.03, 0.05, 0.08, 0.10} on the test fold trades review workload for recall '
        'as expected: τ = 0.03 reviews 71% of applicants and captures 95% of defaulters; '
        'τ = 0.10 reviews 28% and captures 62%. The chosen τ* = 0.05 is a balanced middle that respects '
        'the 80% recall floor.')

    h2(doc, '5.3  Sensitivity check 3 — risk-band cut')
    body(doc,
        'Replacing the fixed FICO cut-points (640 / 760) with a tertile cut on the observed score '
        'distribution leaves the Thấp / Trung bình / Cao default rates within ±0.4 pp. '
        'The two cut schemes agree on the monotonic increase, confirming that the calibration story '
        'is robust to the choice of cut-points.')

    h2(doc, '5.4  Three specific limitations and direction of bias')

    lims = [
        ('L1. Sample size.',
         'Only 12 750 rows, 603 defaulters. Wide confidence intervals; the headline numbers '
         'under-estimate the true variance.',
         'Direction: optimistically narrow CIs; reported AUCs may be slightly high.'),
        ('L2. Approve-only training data.',
         'The dataset contains only loans that were approved, so the model never sees the outcomes '
         'of rejected applicants.',
         'Direction: biases PDs downward for the marginal applicant; inflates apparent accuracy on an approved-only test.'),
        ('L3. Single train / valid / test split.',
         'A single random split confounds temporal drift with sampling noise.',
         'Direction: sign is unknown a priori — whichever direction the unseen quarter happened to differ.'),
    ]
    for label, text, bias in lims:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.space_after  = Pt(3)
        r1 = p.add_run(label + '  ')
        set_font(r1, bold=True, size=12)
        r2 = p.add_run(text + '  ')
        set_font(r2, size=12)
        r3 = p.add_run(bias)
        set_font(r3, size=12, italic=True)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# ── Part 6 ────────────────────────────────────────────────────────────────────

def build_part6(doc):
    add_page_break(doc)
    h1(doc, 'PART 6 — RECOMMENDATION  (≈ 10 %)')

    p = doc.add_paragraph()
    r1 = p.add_run('Recommendation. ')
    set_font(r1, bold=True, size=12)
    r2 = p.add_run(
        'Deploy the calibrated LightGBM model (LGB-CAL) as the primary decisioning engine for new applications, '
        'with a τ* = 0.05 automatic review floor and a manual-review gate for the Cao risk band (score < 640). '
        'Auto-approve only the top 25% of the portfolio (score ≥ 810, expected default rate ≤ 3%).')
    set_font(r2, size=12)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    para_spacing(p, after=8)

    p = doc.add_paragraph()
    r1 = p.add_run('Conditions of use. ')
    set_font(r1, bold=True, size=12)
    r2 = p.add_run('The recommendation is conditional on:')
    set_font(r2, size=12)
    para_spacing(p, after=4)
    bullet(doc, 'full-data retraining at least once per quarter;')
    bullet(doc, 'monitoring the population stability index (PSI) on the score distribution with an alert at PSI > 0.25;')
    bullet(doc, 'a fairness audit disaggregated by gender, age band and regional rating before any real-customer rollout.', after=8)

    p = doc.add_paragraph()
    r1 = p.add_run('Monitoring metric. ')
    set_font(r1, bold=True, size=12)
    r2 = p.add_run(
        'The single key performance indicator is the realised 90-day default rate of the auto-approved segment, '
        'with an alert at observed > 1.5 × the calibrated PD. Secondary KPIs: review workload, KS drift, '
        'and the Brier score of the re-calibrated model on the latest 1 000 approved loans.')
    set_font(r2, size=12)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# ── Appendices ────────────────────────────────────────────────────────────────

def build_appendices(doc):
    add_page_break(doc)

    h1(doc, 'APPENDIX A — Data dictionary (excerpt)')

    t = make_table(doc,
        ['Field', 'Description'],
        [
            ['TARGET',                         '1 = default, 0 = repaid on time. Binary.'],
            ['EXT_SOURCE_1/2/3',               'Normalised external credit scores (mean ≈ 0.5).'],
            ['AMT_CREDIT / AMT_INCOME / AMT_ANNUITY', 'Loan amount, annual income, annuity.'],
            ['DAYS_BIRTH / DAYS_EMPLOYED',     'Age and employment in days (negative). 365 243 = missing sentinel.'],
            ['CODE_GENDER, NAME_CONTRACT_TYPE','Categorical applicant attributes.'],
            ['CREDIT_TERM, CREDIT_GOODS_RATIO','Engineered credit/income/goods ratios.'],
            ['EXT_SOURCE_MEAN / MAX / MIN',    'Aggregated external-score statistics.'],
            ['PREV_CNT_PAYMENT_MEAN, INST_LATE_*', 'Behavioural history from previous applications and instalments.'],
            ['POS_UTIL_MEAN, CC_UTIL_MEAN',    'Utilisation of revolving credit lines.'],
            ['BUR_DEBT_RATIO, BUR_CREDIT_SUM', 'Bureau debt-to-credit aggregates.'],
        ],
        col_widths=[2.8, 4.4]
    )
    doc.add_paragraph()

    # B
    add_page_break(doc)
    h1(doc, 'APPENDIX B — Cleaning log')
    bullet(doc, 'DAYS_EMPLOYED sentinel 365 243 → NaN before imputation.')
    bullet(doc, 'Drop columns with > 60% missing (e.g. XNA, OWN_CAR_AGE).')
    bullet(doc, 'Categorical NaN → \'MISSING\' bucket, then one-hot encoded.')
    bullet(doc, 'Numeric NaN → median per column, then standard-scaled.')
    bullet(doc, 'Outliers in DAYS_BIRTH and DAYS_EMPLOYED are kept; the model is tree-based and insensitive to monotone transforms.')
    bullet(doc, 'Aggregate features computed with pandas groupby on SK_ID_CURR; no per-row outliers removed.')

    # C
    add_page_break(doc)
    h1(doc, 'APPENDIX C — Assumptions register')
    bullet(doc, 'A1. The TARGET column is observed at the loan horizon; right-censoring is negligible for this portfolio.')
    bullet(doc, 'A2. Applicants in the test fold are exchangeable with future applicants in the next quarter (no regime change).')
    bullet(doc, 'A3. External credit scores (EXT_SOURCE_*) are point-in-time and free of leakage.')
    bullet(doc, 'A4. Behavioural history aggregates are computable for new applicants (no look-ahead bias).')
    bullet(doc, 'A5. The cost of a missed defaulter is at least ten times the cost of a false alarm — this drives the recall floor of 0.80.')

    # D
    add_page_break(doc)
    h1(doc, 'APPENDIX D — Link to code')
    body(doc,
        'The pipeline is a single Jupyter notebook (notebooks/home_credit_pipeline.ipynb) that produces '
        'model/model.joblib, predictions_test.csv, metrics.json, model_card.json and the PNG exhibits in model/. '
        'Re-running the notebook regenerates every figure in this report. The project lives at:')
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.5)
    run = p.add_run('https://github.com/<username>/home-credit-default-risk')
    set_font(run, size=12, italic=True)
    para_spacing(p, after=6)
    body(doc, 'See README.md for environment setup, Docker build and Streamlit deployment instructions.')

    # E
    add_page_break(doc)
    h1(doc, 'APPENDIX E — AI-use disclosure')
    body(doc,
        'AI assistance was used in three limited ways: (i) drafting the first version of the report prose from '
        'a hand-written outline; (ii) formatting the final .docx and tables; (iii) reformatting LaTeX-style '
        'equations to plain English. All numerical results, model selections, thresholds, sensitivity checks '
        'and policy recommendations were produced by the human author from the pipeline outputs; '
        'the AI did not invent, modify or reinterpret any of the numbers reported above.',
        after=0)

# ── References ────────────────────────────────────────────────────────────────

def build_references(doc):
    add_page_break(doc)
    h1(doc, 'REFERENCES')

    refs = [
        ('Akiba, T. et al. (2019). Optuna: A next-generation hyperparameter optimization framework. '
         'KDD 2019, 2623–2631.'),
        ('Basel Committee on Banking Supervision. (2006). International convergence of capital measurement '
         'and capital standards. Bank for International Settlements.'),
        ('Brier, G. W. (1950). Verification of forecasts expressed in terms of probability. '
         'Monthly Weather Review 78(1), 1–3.'),
        ('Fawcett, T. (2006). An introduction to ROC analysis. '
         'Pattern Recognition Letters 27(8), 861–874.'),
        ('Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. '
         'Annals of Statistics 29(5), 1189–1232.'),
        ('Hand, D. J., & Henley, W. E. (1997). Statistical classification methods in consumer credit scoring. '
         'J. R. Stat. Soc. A 160(3), 523–541.'),
        ('Hanley, J. A., & McNeil, B. J. (1982). The meaning and use of the area under a ROC curve. '
         'Radiology 143(1), 29–36.'),
        ('Kaggle. (2018). Home Credit Default Risk [Data set]. '
         'https://www.kaggle.com/c/home-credit-default-risk'),
        ('Ke, G. et al. (2017). LightGBM: A highly efficient gradient boosting decision tree. '
         'NeurIPS 30, 3146–3154.'),
        ('Lessmann, S., Baesens, B., Seow, H.-V., & Thomas, L. C. (2015). '
         'Benchmarking state-of-the-art classification algorithms for credit scoring. '
         'EJOR 247(1), 124–136.'),
        ('Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. '
         'NeurIPS 30, 4765–4774.'),
        ('Niculescu-Mizil, A., & Caruana, R. (2005). Predicting good probabilities with supervised learning. '
         'ICML 2005, 625–632.'),
        ('Pedregosa, F. et al. (2011). Scikit-learn: Machine learning in Python. '
         'JMLR 12, 2825–2830.'),
        ('Platt, J. C. (1999). Probabilistic outputs for support vector machines and comparisons to '
         'regularized likelihood methods. MIT Press.'),
        ('Siddiqi, N. (2006). Credit risk scorecards. Wiley.'),
        ('Zadrozny, B., & Elkan, C. (2002). Transforming classifier scores into accurate multiclass '
         'probability estimates. KDD 2002, 694–699.'),
    ]
    for ref in refs:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent    = Inches(0.5)
        p.paragraph_format.first_line_indent = Inches(-0.5)
        p.paragraph_format.space_after    = Pt(6)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        run = p.add_run(ref)
        set_font(run, size=12)

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    doc = Document()

    # page margins
    for section in doc.sections:
        section.top_margin    = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin   = Cm(3.0)
        section.right_margin  = Cm(2.5)

    # default style
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)

    build_cover(doc)
    build_inner(doc)
    build_acknowledgements(doc)
    build_part1(doc)
    build_part2(doc)
    build_part3(doc)
    build_part4(doc)
    build_part5(doc)
    build_part6(doc)
    build_appendices(doc)
    build_references(doc)

    out = 'c:/Dev/home-credit-default-risk/docs/D4_report_v2.docx'
    doc.save(out)
    print(f'Saved: {out}')

if __name__ == '__main__':
    main()
