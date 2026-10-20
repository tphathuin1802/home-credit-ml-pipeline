"""Build the D4 presentation script DOCX from docs/presentation_script.md content."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_BREAK
from docx.shared import Pt, RGBColor, Inches
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

PROJ = Path('c:/Dev/home-credit-default-risk')
OUT  = PROJ / 'docs' / 'presentation_script.docx'

# ─── helpers ──────────────────────────────────────────────────────────────────
def set_font(run, name='Calibri', size=12, bold=False, italic=False, color=None):
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
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def page_break(doc):
    p = doc.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)

def h1(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_font(run, bold=True, size=14, color=(0x1F, 0x3B, 0x73))
    para_spacing(p, before=18, after=8)
    return p

def h2(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_font(run, bold=True, size=13, color=(0x2E, 0x5C, 0x8A))
    para_spacing(p, before=14, after=5)
    return p

def body(doc, text, after=6, indent=0, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = align
    run = p.add_run(text)
    set_font(run, size=12)
    pf = p.paragraph_format
    pf.space_after = Pt(after)
    if indent:
        pf.left_indent = Inches(indent)
    return p

def bullet(doc, text, indent=0.3, after=3):
    p = doc.add_paragraph(style='List Bullet')
    run = p.add_run(text)
    set_font(run, size=12)
    p.paragraph_format.left_indent = Inches(indent)
    p.paragraph_format.space_after = Pt(after)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p

def blockquote(doc, text):
    """Grey-background 'On the slide' block."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(text)
    set_font(run, size=11, color=(0x44, 0x44, 0x44))
    pf = p.paragraph_format
    pf.left_indent = Inches(0.25)
    pf.space_after = Pt(6)
    # light shading
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:fill'), 'F2F2F2')
    pPr.append(shd)
    return p

def section_label(doc, text, color=(0x1F, 0x3B, 0x73)):
    """Bold coloured label line."""
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_font(run, bold=True, size=12, color=color)
    para_spacing(p, before=4, after=3)
    return p

def make_table(doc, headers, rows, col_widths=None, header_bg='D9E1F2'):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = 'Table Grid'
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        set_cell_bg(c, header_bg)
        p = c.paragraphs[0]
        run = p.add_run(h)
        set_font(run, bold=True, size=11)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            c = t.rows[ri+1].cells[ci]
            p = c.paragraphs[0]
            run = p.add_run(str(val))
            set_font(run, size=11)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if ci > 0 else WD_ALIGN_PARAGRAPH.LEFT
    if col_widths:
        for ri in t.rows:
            for ci, c in enumerate(ri.cells):
                c.width = Inches(col_widths[ci])
    return t

# ─── build ────────────────────────────────────────────────────────────────────
def build():
    doc = Document()
    for sec in doc.sections:
        sec.top_margin    = Inches(0.8)
        sec.bottom_margin = Inches(0.8)
        sec.left_margin   = Inches(0.9)
        sec.right_margin  = Inches(0.9)

    # ── cover ────────────────────────────────────────────────────────────────
    for ln in ['VIETNAM NATIONAL UNIVERSITY, HO CHI MINH CITY',
               'HO CHI MINH UNIVERSITY OF TECHNOLOGY',
               'FACULTY OF ECONOMICS & MATHEMATICS']:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(p.add_run(ln), bold=True, size=12)
        para_spacing(p, after=2)

    doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run('─' * 58), size=12)
    para_spacing(p, before=4, after=12)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run('PRESENTATION SCRIPT'), bold=True, size=18, color=(0x1F, 0x3B, 0x73))
    para_spacing(p, after=8)

    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p.add_run('Home Credit Default Risk Scoring\nD4 Midterm Project — Presentation Script'),
             bold=True, size=14)
    para_spacing(p, after=28)

    doc.add_paragraph()
    for name, role in [
        ('Phat Huynh', 'K234131613'),
        ('Duy Nguyen', 'K234131591'),
    ]:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r1 = p.add_run(name); set_font(r1, bold=True, size=13)
        r2 = p.add_run('  —  ' + role); set_font(r2, size=12)
        para_spacing(p, after=4)

    doc.add_paragraph()
    for label, value in [
        ('SUBJECT',   'Thematic unit 1 — 261EMM401001'),
        ('DURATION',  '12–15 minutes (15 slides)'),
        ('DATE',      'Ho Chi Minh City, October 2026'),
    ]:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r1 = p.add_run(label + ':  '); set_font(r1, bold=True, size=12)
        r2 = p.add_run(value); set_font(r2, size=12)
        para_spacing(p, after=5)

    page_break(doc)

    # ── how to use ───────────────────────────────────────────────────────────
    h1(doc, 'HOW TO USE THIS SCRIPT')
    body(doc,
        'Each slide below has two blocks. The first, ON THE SLIDE, is a short reminder of what is '
        'projected on screen. The second, SAY THIS, is a continuous spoken paragraph written to be '
        'read aloud at natural pace. The estimated time is given at the top of each slide.',
        after=6)
    body(doc,
        'The script is written in English so it can be delivered directly in the presentation. '
        'Slide 9 and Slide 14 contain the honest limitations of the study; the panel is likely to '
        'probe these, so rehearse those two slides carefully.',
        after=10)

    # ── SLIDE 1 ──────────────────────────────────────────────────────────────
    h1(doc, 'SLIDE 1  —  TITLE / INTRODUCTION  (~60 sec)')
    section_label(doc, 'On the slide:')
    blockquote(doc,
        'Title: HOME CREDIT DEFAULT RISK SCORING  ·  Tagline: a reproducible end-to-end ML pipeline '
        'that turns 7 raw tables into a deployable PD model  ·  Authors: Phat Huynh, Duy Nguyen  ·  01 / 15')
    section_label(doc, 'Say this:')
    body(doc,
        '"Good morning, professors and friends. I\'m Phat, and together with Duy we are presenting our D4 '
        'midterm project on Home Credit Default Risk Scoring — that is, a reproducible credit-scoring '
        'pipeline that takes Home Credit\'s seven raw tables all the way to a deployable Probability-of-'
        'Default model, complete with a scorecard, five risk bands and a web demo.\n\n'
        'The project has a dual objective. First, the model must discriminate between who defaults and who '
        'does not — we measure that with AUC and the KS statistic. Second, the probabilities it outputs must '
        'be reliable enough to drive credit policy, because Basel computes expected loss as PD times LGD '
        'times EAD. A model that ranks well but produces sloppy probabilities is useless for pricing or '
        'provisioning.\n\n'
        'Everything here is reproducible from a single notebook, and the final model is packaged in Docker '
        'and deployed on Streamlit Cloud. Let me begin."')

    # ── SLIDE 2 ──────────────────────────────────────────────────────────────
    h1(doc, 'SLIDE 2  —  THE PROBLEM  (~60 sec)')
    section_label(doc, 'On the slide:')
    blockquote(doc,
        'SECTION 01: THE PROBLEM  ·  Three pillars — default rate is low (about 8%), so imbalanced '
        'classification and naive accuracy is misleading  ·  cost asymmetry  ·  calibrated PD feeds '
        'downstream credit policy, expected loss and loan pricing.')
    section_label(doc, 'Say this:')
    body(doc,
        '"First, why does this problem matter?\n\n'
        'Home Credit lends to people that mainstream banks normally turn away — borrowers in emerging '
        'markets with little or no formal credit history. For them a traditional bureau score is either '
        'missing or of limited value. That is why Home Credit assembled seven tables: the current '
        'application, bureau records, previous applications, instalment histories, POS balances and '
        'credit-card balances — an alternative-data credit footprint.\n\n'
        'Three points define the problem.\n\n'
        'First, the default rate is only about 8%. This is an imbalanced classification problem. A model '
        'that always predicts "no default" is still right 92% of the time, so accuracy carries almost no '
        'information. We therefore report AUC, KS, the Brier score, and recall at a fixed operating '
        'threshold.\n\n'
        'Second, the costs are asymmetric. Missing a defaulter is far more expensive than rejecting a good '
        'borrower. A wrong decline only costs us a lost sale; a wrong approval costs us the loss. That is '
        'exactly why we pick our threshold to protect recall at or above 80% rather than simply maximising F1.\n\n'
        'Third, Basel demands that PD be both discriminating and well calibrated. Those two requirements can '
        'pull in opposite directions, and that tension is the reason this project exists: find one pipeline '
        'in which ranking and calibration both succeed."')

    # ── SLIDE 3 ──────────────────────────────────────────────────────────────
    h1(doc, 'SLIDE 3  —  DELIVERABLES  (~45 sec)')
    section_label(doc, 'On the slide:')
    blockquote(doc,
        'Six deliverables — trained and calibrated model (model.joblib)  ·  metrics table  ·  '
        'per-customer PD and rating (predictions_test.csv)  ·  Streamlit web app with Docker  ·  '
        'model card (model_card.json)  ·  this slide deck.')
    section_label(doc, 'Say this:')
    body(doc,
        '"The project delivers six concrete artefacts. One — the trained and calibrated model, saved as '
        'model.joblib. Two — a metrics table comparing all four candidate models. Three — '
        'predictions_test.csv, which stores a calibrated PD and an A-to-E rating for every test applicant; '
        'this is what the business-impact analysis in Chapter 4 uses to compute capture rates and lift. '
        'Four — a Streamlit web demo, containerised in Docker and deployed. Five — model_card.json, the '
        'model\'s curriculum vitae, recording exactly what it was trained on and how it performed. And six — '
        'this slide deck."')

    # ── SLIDE 4 ──────────────────────────────────────────────────────────────
    h1(doc, 'SLIDE 4  —  DATASET  (~60 sec)')
    section_label(doc, 'On the slide:')
    blockquote(doc,
        'Seven tables with row counts and purpose — application_train (307,511, master table with TARGET), '
        'bureau (1.7M), bureau_balance (27.3M), previous_application (1.7M), installments_payments (13.6M), '
        'POS_CASH_balance (10.0M), credit_card_balance (3.8M).')
    section_label(doc, 'Say this:')
    body(doc,
        '"The dataset consists of seven tables, several of them very large. The smallest, '
        'application_train, has 307 thousand rows — and it is the master table, carrying the TARGET column we '
        'want to predict. The other six are auxiliary tables. bureau and bureau_balance hold credit histories '
        'reported by other institutions. previous_application holds earlier applications from the same customer '
        'at Home Credit. installments_payments records repayments instalment by instalment. POS_CASH_balance '
        'and credit_card_balance are monthly balance snapshots.\n\n'
        'The key structural difficulty is this: a single customer appears many times in these auxiliary '
        'tables — someone with five instalment plans contributes five rows to installments_payments. So we '
        'cannot join directly. Each table must first be aggregated down to exactly one row per customer '
        'before merging into the master table.\n\n'
        'That aggregation raises an important engineering question: which summary function suits each column? '
        'For DAYS_CREDIT — days since the bureau record was filed — the minimum is far more informative than '
        'the mean; for AMT_CREDIT_SUM_DEBT the maximum outstanding balance best reflects current risk. After '
        'careful design we end up with 301 engineered features, a number you will see again shortly."')

    # ── SLIDE 5 ──────────────────────────────────────────────────────────────
    h1(doc, 'SLIDE 5  —  EDA: CLASS IMBALANCE AND MISSINGNESS  (~60 sec)')
    section_label(doc, 'On the slide:')
    blockquote(doc,
        'Exploratory Data Analysis — default rate about 8%, broadly stable across age groups, the 20–25 '
        'cohort riskiest  ·  some 50 or more columns have meaningful missingness, dominated by housing '
        'characteristics and the external scores.')
    section_label(doc, 'Say this:')
    body(doc,
        '"Two initial observations drive every downstream modelling choice.\n\n'
        'First, the default rate is roughly 8% and is broadly stable across age groups, with the 20-to-25 '
        'cohort running slightly higher — a finding worth remembering when we come to the fairness '
        'discussion.\n\n'
        'Second, more than 50 columns carry substantial missing values — concentrated in housing '
        'characteristics and, importantly, the three external credit scores EXT_SOURCE_1/2/3. Instead of '
        'imputing those three aggressively with a mean or a median — the common reflex — we preserve a signal '
        'in a variable we call EXT_SOURCE_COUNT, which simply records how many external scores are present. '
        'The reasoning is that the fact that a customer has any bureau footprint at all is itself informative '
        'about their credit history, and filling the gap with a constant would erase exactly that signal.\n\n'
        'These two decisions — refusing to use accuracy, and treating missingness as signal — shape the entire '
        'pipeline that follows."')

    # ── SLIDE 6 ──────────────────────────────────────────────────────────────
    h1(doc, 'SLIDE 6  —  EDA: KEY FEATURES BY TARGET  (~60 sec)')
    section_label(doc, 'On the slide:')
    blockquote(doc,
        'Comparing distributions of AMT_CREDIT, AMT_INCOME, AGE and the three EXT_SOURCE scores between '
        'defaulters and non-defaulters  ·  all three EXT_SOURCE variables tagged STRONG.')
    section_label(doc, 'Say this:')
    body(doc,
        '"This slide compares the distributions of four variables between the default and non-default groups.\n\n'
        'Unsurprisingly, all three external credit scores — EXT_SOURCE_1, EXT_SOURCE_2 and EXT_SOURCE_3 — show '
        'very strong discrimination: their distributions between the two groups are almost fully separated. We '
        'tag all three as STRONG, because these are the variables most widely discussed in the Home Credit '
        'community.\n\n'
        'By contrast, age, income and loan amount have distributions that largely overlap between defaulters and '
        'non-defaulters. On their own they are not sufficient for prediction. That is precisely the motivation '
        'for the engineered feature block on the next slide: we need 301 features, not 122, to give even a '
        'linear model a real chance of capturing the signal."')

    # ── SLIDE 7 ──────────────────────────────────────────────────────────────
    h1(doc, 'SLIDE 7  —  FEATURE ENGINEERING: FOUR BLOCKS  (~75 sec)')
    section_label(doc, 'On the slide:')
    blockquote(doc,
        'Four blocks — 01 application cleaning  ·  02 bureau aggregation  ·  03 previous applications and '
        'instalments  ·  04 POS_CASH and credit card  ·  from 122 raw columns to 301 features.')
    section_label(doc, 'Say this:')
    body(doc,
        '"This is the slide I am most proud of — the feature-engineering blueprint. From 122 raw columns we '
        'build 301 features, organised into four functional blocks.\n\n'
        'Block one — cleaning and ratios on the master table. We handle three traps. DAYS_EMPLOYED = 365243 is '
        'a sentinel value, converted to NaN plus a binary flag. CODE_GENDER = XNA likewise becomes NaN. And '
        'OWN_CAR_AGE stays NaN for customers without a car — because "no car" is itself a signal. We then build '
        'ratio features such as CREDIT_INCOME_RATIO, CREDIT_TERM and ANNUITY_INCOME_RATIO, plus mean, min, '
        'max, standard deviation, product and count for the three external scores.\n\n'
        'Block two — bureau aggregates. We group by SK_ID_CURR and take counts of active credits, sums of '
        'outstanding debt, and one important ratio, BUR_DEBT_RATIO = debt divided by credit limit, plus a '
        'HAS_BUREAU flag for customers with no bureau record whatsoever.\n\n'
        'Block three — previous applications and instalments. The approval rate PREV_APPROVE_RATE, the '
        'lateness history INST_LATE_MEAN, and the total days late by at least seven, INST_LATE_7D_SUM. These '
        'are the features that will climb to the top of our importance ranking shortly.\n\n'
        'Block four — POS and credit cards. Average utilisation, POS_UTIL_MEAN and CC_UTIL_MEAN — the closer a '
        'customer runs to their limit, the higher the risk.\n\n'
        'All four blocks merge back into the master table to give a 301-dimensional feature vector per customer. '
        'Everything is implemented inside a single ColumnTransformer, fitted on the training fold and applied '
        'unchanged to validation and test — our structural guarantee against data leakage."')

    # ── SLIDE 8 ──────────────────────────────────────────────────────────────
    h1(doc, 'SLIDE 8  —  METHODOLOGY: MODELLING PIPELINE  (~75 sec)')
    section_label(doc, 'On the slide:')
    blockquote(doc,
        'Seven steps — split  ·  preprocess  ·  logistic baselines  ·  tuned LightGBM (Optuna, 15 trials)  ·  '
        'isotonic calibration on validation  ·  threshold (recall at or above 80%)  ·  evaluate AUC, Gini, '
        'KS, Brier, PR-AUC, F1.')
    section_label(doc, 'Say this:')
    body(doc,
        '"The modelling pipeline has seven clearly separated steps.\n\n'
        'Step 1, splitting. We divide train, validation and test with a stratified split so that every fold '
        'preserves the same 8% default rate. random_state = 42 is fixed throughout so every comparison is '
        'reproducible. This version of the report uses 50,000 rows in total — 35,000 train, 7,500 validation '
        'and 7,500 test. Note that we increased the sample relative to the original 12,750-row draft, which '
        'gives more stable results and still fits comfortably in memory.\n\n'
        'Step 2, preprocessing. A single ColumnTransformer — median imputation for numeric variables, '
        'most-frequent imputation plus one-hot encoding with drop-first for categoricals.\n\n'
        'Step 3, baselines. Two logistic regressions — one unweighted with C = 0.5, one with class_weight = '
        '\'balanced\'. Both serve as benchmarks throughout the report; we deliberately use that word so the '
        'comparison is explicit.\n\n'
        'Step 4, tuned LightGBM. We optimise the hyper-parameters with Optuna over 15 trials, with early '
        'stopping on the validation fold. The winning trial gives n_estimators = 205, num_leaves = 53, '
        'learning_rate = 0.0469.\n\n'
        'Step 5, calibration. We fit an isotonic regression on the validation fold to recalibrate the output '
        'probabilities. The Brier score moves from 0.0677 to 0.0678 — essentially unchanged, because only a '
        'small range of the scale is affected — but the resulting probabilities are the ones we can actually '
        'trust in a scorecard.\n\n'
        'Step 6, the threshold. We apply Equation 3.1 — maximise F1 subject to recall of at least 0.80 — '
        'which yields tau = 0.05.\n\n'
        'Step 7, evaluation. We report AUC, Gini, KS, Brier, PR-AUC and F1 on a test fold of 7,500 applicants '
        'that played no part in any of the six steps above."')

    # ── SLIDE 9 ──────────────────────────────────────────────────────────────
    h1(doc, 'SLIDE 9  —  RESULTS: TEST-SET COMPARISON  (~75 sec)')
    section_label(doc, 'On the slide:')
    blockquote(doc,
        'Four-model comparison on n = 7,500 — Logistic AUC 0.7452  ·  Logistic-balanced 0.7412  ·  '
        'LightGBM 0.7594  ·  LightGBM calibrated 0.7582  ·  selected model catches 86.2% of defaulters at '
        '12.8% precision.')
    section_label(doc, 'Say this:')
    body(doc,
        '"This is the headline table — all four models evaluated on the same 7,500-row test fold.\n\n'
        'Logistic, our benchmark, reaches an AUC of 0.7452 and a KS of 0.369. That is the baseline to beat.\n\n'
        'Logistic-balanced deserves a specific comment. Its recall is 100%, but its precision is only 8.3% — '
        'essentially identical to the base rate. In other words, at its operating threshold it flags virtually '
        'every applicant, which is useless as a decision rule. Its Brier score is also roughly three times '
        'worse, because class weighting pushes predicted probabilities far above the true default frequency. '
        'This is exactly the point made on slide 2: class weighting is not a remedy when you need calibrated '
        'probabilities.\n\n'
        'Raw LightGBM achieves the best ranking: AUC 0.7594, KS 0.386.\n\n'
        'Calibrated LightGBM gives up 0.0012 of AUC and about 0.011 of KS, but reaches a higher recall — 86.2% '
        'against 83.8% — and produces probabilities fit for the scorecard. This is the model we take forward.\n\n'
        'That 0.014 AUC gap looks small, and I want to be honest about it: the bootstrap analysis in Chapter 5 '
        'shows this gap falls inside a 95% confidence interval that contains zero at a 50,000-row sample. I '
        'will come back to that on the final slide, and it is precisely why we added a full robustness chapter."')

    # ── SLIDE 10 ─────────────────────────────────────────────────────────────
    h1(doc, 'SLIDE 10  —  EVALUATION PLOTS  (~45 sec)')
    section_label(doc, 'On the slide:')
    blockquote(doc,
        'ROC, precision–recall, KS and calibration plots  ·  KS = 0.375 at the optimal cut-off, well above '
        'the 0.20 acceptable and 0.30 good credit-scoring benchmarks.')
    section_label(doc, 'Say this:')
    body(doc,
        '"This slide packages the four core diagnostic plots.\n\n'
        'ROC, top left — all four curves sit clearly above the diagonal; no model is poor. Precision–recall, '
        'below it — given a base rate of only 8%, precision remains several times the base rate at low-to-'
        'moderate recall, which is a good sign.\n\n'
        'The KS plot, top right, is the one I want to dwell on. Our KS reaches 0.375 at the optimal cut-off, '
        'comfortably above the 0.30 good benchmark used in credit scoring. In other words, the largest '
        'vertical separation between the good and bad cumulative distributions is 37.5 percentage points — '
        'enough to segment a real portfolio in practice.\n\n'
        'The reliability plot, bottom right, shows calibrated probabilities tracking the diagonal across most '
        'of the range, with mild over-confidence between 0.1 and 0.3 — a known artefact of isotonic '
        'regression in sparse regions of the score space."')

    # ── SLIDE 11 ─────────────────────────────────────────────────────────────
    h1(doc, 'SLIDE 11  —  FEATURE IMPORTANCE  (~45 sec)')
    section_label(doc, 'On the slide:')
    blockquote(doc,
        'Top features by LightGBM gain — PREV_CNT_PAYMENT_MEAN, CREDIT_TERM, EXT_SOURCE_MEAN, '
        'CREDIT_GOODS_RATIO, INST_PAY_RATIO, POS_UTIL_MEAN, EMPLOYED_YEARS, BUR_DEBT_RATIO, '
        'PREV_APPROVE_RATE, ANNUITY_INCOME_RATIO.')
    section_label(doc, 'Say this:')
    body(doc,
        '"The ten strongest features by LightGBM gain:\n\n'
        'First, PREV_CNT_PAYMENT_MEAN — the average number of instalments in the customer\'s repayment '
        'history, our single strongest signal. Second, CREDIT_TERM, the loan term. Third, EXT_SOURCE_MEAN, the '
        'average of the three external bureau scores. Then come CREDIT_GOODS_RATIO (loan relative to goods '
        'value), INST_PAY_RATIO and INST_LATE_MEAN (repayment ratio and average lateness), POS_UTIL_MEAN (POS '
        'utilisation), EMPLOYED_YEARS, BUR_DEBT_RATIO and PREV_APPROVE_RATE with ANNUITY_INCOME_RATIO.\n\n'
        'The important observation is what is absent from that list: age and gender rank very low. The model '
        'relies predominantly on financial behaviour rather than raw demographics — which is a reassuring '
        'signal from a fairness standpoint."')

    # ── SLIDE 12 ─────────────────────────────────────────────────────────────
    h1(doc, 'SLIDE 12  —  SCORECARD AND RISK BANDS  (~75 sec)')
    section_label(doc, 'On the slide:')
    blockquote(doc,
        'score = 712.88 − 28.8539 x ln( PD / (1 − PD) )  ·  five bands A to E with empirical default rates '
        '1.92%, 5.02%, 8.70%, 14.84%, 30.04%  ·  rates rise monotonically across bands.')
    section_label(doc, 'Say this:')
    body(doc,
        '"This is the core product of the project — converting a probability of default into a FICO-style '
        'credit score.\n\n'
        'The formula is score = 712.88 − 28.85 x ln(odds), with a base of 600, a PDO of 20 — that is, twenty '
        'points for every doubling of the odds — and base odds of 50 to 1, following the Siddiqi convention. '
        'We derive factor = PDO / ln 2 = 28.85 and offset = 600 + factor x ln 50 = 712.88.\n\n'
        'We then split applicants into five risk bands, A to E, using PD thresholds of 0.03, 0.06, 0.10 and '
        '0.20 rather than fixed score cuts. The reason is empirical: the realised score range on the test fold '
        'is only 401 to 799, not the textbook 300 to 850, so a fixed cut at 640 and 760 would push nearly the '
        'entire test set into a single middle band.\n\n'
        'The empirical default rates rise monotonically: Band A, PD below 3%, 1.92% across 2,185 applicants. '
        'Band B, 3 to 6%, 5.02% across 2,372. Band C, 6 to 10%, 8.70% across 1,241. Band D, 10 to 20%, '
        '14.84% across 1,166. Band E, 20% and above, 30.04% across 536.\n\n'
        'Average predicted PD and observed default rate agree to within 1.5 percentage points in every band. '
        'The scorecard works."')

    # ── SLIDE 13 ─────────────────────────────────────────────────────────────
    h1(doc, 'SLIDE 13  —  BUSINESS IMPACT  (~75 sec)')
    section_label(doc, 'On the slide:')
    blockquote(doc,
        'At tau = 0.05 on 7,500 test customers with 603 defaulters, the model flags about 520 defaulters '
        'for manual review  ·  capture rate and lift by band: A 7.0% / 0.24x  ·  B 19.7% / 0.62x  ·  '
        'C 17.9% / 1.08x  ·  D 28.7% / 1.85x  ·  E 26.7% / 3.74x.')
    section_label(doc, 'Say this:')
    body(doc,
        '"At our operating point tau = 0.05 — chosen on the validation fold to protect recall above 80% — '
        'we can quantify the business impact on the test set.\n\n'
        'In aggregate, there are 603 defaulters. The model catches 86.2% of them, so 520 customers are routed '
        'to manual review. A precision of 12.8% means roughly one in eight flagged applicants is a true '
        'defaulter; against an 8% base rate that is a lift of about 1.6 times — good enough to justify the '
        'review workload.\n\n'
        'By band: Band A contains 30% of applicants but only 7% of defaulters, a lift of just 0.24x — the '
        'natural candidate for streamlined approval. Bands D and E together hold only 22.7% of applicants yet '
        'contain 55.4% of all defaulters — that is where manual review should concentrate. Bands B through E '
        'cover 70% of applicants while capturing 93% of defaulters. Band E carries a lift of 3.74x — nearly '
        'four times the base rate — and clearly warrants scrutiny.\n\n'
        'The conclusion is that this model should not be used to auto-decline anyone. Its role is triage: '
        'auto-approve band A, standard review for B and C, and manual review for D and E. That is exactly how '
        'Basel expects an internal model to be used."')

    # ── SLIDE 14 ─────────────────────────────────────────────────────────────
    h1(doc, 'SLIDE 14  —  CONCLUSION, LIMITATIONS, FUTURE WORK  (~75 sec)')
    section_label(doc, 'On the slide:')
    blockquote(doc,
        'Summary table of three models  ·  limitations: reject inference, deep tabular models, time series, '
        'calibration refresh  ·  future work: sample size, recall-versus-precision policy, drift monitoring, '
        'fairness audit.')
    section_label(doc, 'Say this:')
    body(doc,
        '"To conclude the project as a whole.\n\n'
        'The pipeline runs end to end: from seven raw tables to a calibrated PD model, a FICO-style scorecard, '
        'five risk bands and a Streamlit front-end — with every step reproducible from one notebook.\n\n'
        'Three numbers to remember: an AUC of 0.7582, a KS of 0.3751, and 86.2% recall at tau = 0.05 — strong '
        'performance for a problem with an 8% positive rate and genuinely noisy alternative-data signals.\n\n'
        'Two limitations I want to state plainly.\n\n'
        'First, the LightGBM-versus-Logistic gap of about 0.014 AUC lies inside a 95% bootstrap confidence '
        'interval that contains zero when we resample the test predictions 1,000 times. Put bluntly: on this '
        'test fold we cannot statistically claim LightGBM beats logistic regression. That is genuine sampling '
        'uncertainty, and we report it rather than overstate it.\n\n'
        'Second, our logistic benchmark is a default scikit-learn configuration — no Weight-of-Evidence '
        'binning, no outlier treatment, no regularisation sweep. The 0.014 AUC gap should therefore be read as '
        'an upper bound on LightGBM\'s true advantage, not a point estimate.\n\n'
        'Future work falls into three groups. Modelling: reject inference to address approved-only training '
        'data, deep tabular architectures such as TabNet and FT-Transformer, and sequence models over '
        'instalment history. Operations: quarterly re-fitting of the isotonic regression as the portfolio mix '
        'drifts, and PSI and KS drift monitoring on the external scores and amount variables. And governance: '
        'a fairness audit disaggregated by gender and age band before any production rollout.\n\n'
        'Thank you. I am happy to take any questions."')

    # ── SLIDE 15 ─────────────────────────────────────────────────────────────
    h1(doc, 'SLIDE 15  —  THANK YOU / Q&A  (~30 sec)')
    section_label(doc, 'On the slide:')
    blockquote(doc,
        'THANK YOU  ·  Questions, feedback, collaboration — always welcome  ·  '
        'https://sh-home-credit-ml-pipeline.streamlit.app')
    section_label(doc, 'Say this:')
    body(doc,
        '"Thank you to our professors and to all of you for listening. The demo application is live at the '
        'address on the slide — you are welcome to try it. I am happy to take questions, feedback, and ideas '
        'for collaboration. Thank you."')

    page_break(doc)

    # ── APPENDIX A ───────────────────────────────────────────────────────────
    h1(doc, 'APPENDIX A  —  ANTICIPATED Q&A')

    qas = [
        ('Q1. "Why 50,000 rows instead of the full 307,000?"',
         'Memory and runtime. Fifty thousand rows is enough for 301 engineered features to fit comfortably on '
         'a laptop, while still allowing a 1,000-resample bootstrap in seconds. The report states the '
         'deployment condition explicitly: the model must be retrained on the full dataset before any '
         'production rollout.'),
        ('Q2. "The bootstrap CI contains zero — so is LightGBM actually better than logistic regression?"',
         'Possibly, possibly not — at this sample size we cannot distinguish them. On published benchmarks and '
         'at full scale, LightGBM is usually clearly ahead. The +0.014 point estimate on this test fold has '
         'the right sign but is not strong enough to reject the null hypothesis that the two models are '
         'equivalent.'),
        ('Q3. "Why isotonic regression rather than Platt scaling?"',
         'Both are standard. Platt scaling assumes a sigmoid shape and has fewer parameters, which makes it the '
         'safer choice on a small validation fold. Isotonic regression assumes nothing about shape but needs a '
         'reasonably large sample to remain reliable. Our validation fold has 7,500 rows — comfortably large '
         'enough for isotonic. Section 3.5 cites Niculescu-Mizil and Caruana (2005) on exactly this trade-off.'),
        ('Q4. "The realised score range is 401 to 799 — are fixed cut-points at 760 even sensible?"',
         'That is why we switched to PD thresholds of 0.03, 0.06, 0.10 and 0.20. Because the realised score '
         'range does not span the textbook 300 to 850, fixed cuts at 640 and 760 collapse nearly the whole '
         'test set into a single middle band. PD thresholds are invariant to the score scale, so they remain '
         'meaningful.'),
        ('Q5. "Where does the PSI above 0.25 alert threshold come from?"',
         'It is an industry convention, cited from Sidlo (2003): PSI below 0.10 indicates a stable population, '
         '0.10 to 0.25 warrants monitoring, and above 0.25 signals a material shift requiring recalibration.'),
        ('Q6. "Band E carries a 30% default rate — can we auto-decline on that basis?"',
         'No. The report is explicit that the model is a decision-support tool, not a standalone decline rule. '
         'Every D and E decision requires an underwriter sign-off. This also matches the Basel expectation for '
         'internal ratings-based models. Auto-declining at 30% observed default would discard roughly seven in '
         'ten good applicants.'),
        ('Q7. "How do you justify the 80% recall floor?"',
         'It encodes assumption A5: the cost of a missed defaulter is at least ten times the cost of a false '
         'alarm. The threshold sweep in Section 5.2 quantifies the trade-off directly — moving the threshold '
         'from 0.05 to 0.03 buys 6.8 percentage points of recall but costs 16.8 percentage points of review '
         'workload. An operator with a tighter review budget should simply re-tune the threshold on their own '
         'validation fold.'),
        ('Q8. "How did you guard against data leakage?"',
         'Three ways. The ColumnTransformer — including imputers and the scaler — is fitted only on the training '
         'fold and applied unchanged to validation and test. All median imputations therefore derive from '
         'training statistics alone. The isotonic calibration layer is fitted on validation, never on test. '
         'And the test fold is untouched until every modelling decision has been made, so the reported metrics '
         'reflect data that played no part in any decision.'),
    ]
    for q, a in qas:
        p = doc.add_paragraph()
        r1 = p.add_run(q)
        set_font(r1, bold=True, size=12, color=(0x2E, 0x5C, 0x8A))
        para_spacing(p, before=10, after=3)
        body(doc, 'Answer:  ' + a, after=8)

    page_break(doc)

    # ── APPENDIX B ───────────────────────────────────────────────────────────
    h1(doc, 'APPENDIX B  —  DELIVERY NOTES')

    h2(doc, 'Pacing')
    pace_rows = [
        ['Opening and problem', '1–3', '2 min 45 s'],
        ['Data and features', '4–7', '4 min 15 s'],
        ['Method and results', '8–11', '4 min 00 s'],
        ['Scorecard and impact', '12–13', '2 min 30 s'],
        ['Conclusion and Q&A', '14–15', '1 min 45 s'],
        ['Total', '15', 'about 15 min'],
    ]
    make_table(doc, ['Segment', 'Slides', 'Target time'], pace_rows,
               col_widths=[2.5, 1.0, 1.5])
    doc.add_paragraph()

    h2(doc, 'Where to compress if you run long')
    bullet(doc, 'Slide 5 — state the two findings, skip the age-cohort detail.')
    bullet(doc, 'Slide 6 — keep the EXT_SOURCE observation, drop the AMT_CREDIT comparison.')
    bullet(doc, 'Slide 10 — lead with the KS benchmark, summarise the other three plots in one sentence.')
    bullet(doc, 'Slide 12 — read only band A and band E aloud; the table carries the middle bands.')
    body(doc, '')
    body(doc, 'Never compress slides 9, 13 or 14 — they carry the results, the business case and the honest '
              'limitations, which is what the panel will be examining.', after=8)

    h2(doc, 'Pre-presentation checklist')
    bullet(doc, 'Open the slide PDF in presentation mode; verify fonts, images and table alignment render correctly.')
    bullet(doc, 'Open https://sh-home-credit-ml-pipeline.streamlit.app in a separate browser tab, pre-loaded.')
    bullet(doc, 'Keep model/predictions_test.csv and model/sensitivity_results.json accessible in case of a '
                'technical question.')
    bullet(doc, 'Have the final report PDF open and accessible so the panel can cross-reference a table.')
    bullet(doc, 'Rehearse once with a timer. The common failure mode is spending 90 seconds on slides 5 to 7 '
                'and then rushing the limitations.')

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f'Saved: {OUT}')

if __name__ == '__main__':
    build()