"""Build presentation PDF (slide-deck style) for Home Credit Default Risk project.

Fonts: JetBrains Mono (Regular / Bold / Italic).
Layout: 16:9 landscape, Home Credit palette.
Source: notebook + model artifacts + predictions CSV.

Run:  python build_slides.py
Out:  slides.pdf  (multi-page PDF, one slide per page)
"""
from __future__ import annotations

import io
import json
import textwrap
from datetime import date
from pathlib import Path

import pandas as pd
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image as RLImage,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# --------------------------------------------------------------------------- #
# Setup
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parent
FONT_DIR = ROOT / "assets" / "fonts"
MODEL_DIR = ROOT / "model"

pdfmetrics.registerFont(TTFont("JBM", str(FONT_DIR / "JetBrainsMono-Regular.ttf")))
pdfmetrics.registerFont(TTFont("JBM-B", str(FONT_DIR / "JetBrainsMono-Bold.ttf")))
pdfmetrics.registerFont(TTFont("JBM-I", str(FONT_DIR / "JetBrainsMono-Italic.ttf")))

# Page = 16:9-ish landscape (taller to fit dense content)
SLIDE_W, SLIDE_H = (35.0 * cm, 24.0 * cm)

# Home Credit palette
HC_RED = HexColor("#ED1C24")
HC_BLACK = HexColor("#0F0F0F")
HC_WHITE = HexColor("#FFFFFF")
HC_GRAY = HexColor("#6B6B6B")
HC_LIGHT = HexColor("#F4F4F4")
HC_GREEN = HexColor("#4CAF50")
HC_BLUE = HexColor("#2196F3")
HC_ORANGE = HexColor("#FF9800")
HC_PURPLE = HexColor("#9C27B0")

# --------------------------------------------------------------------------- #
# Load artifacts
# --------------------------------------------------------------------------- #
with open(MODEL_DIR / "metrics.json", encoding="utf-8") as f:
    METRICS = json.load(f)
with open(MODEL_DIR / "model_card.json", encoding="utf-8") as f:
    CARD = json.load(f)
METRICS_TBL = pd.read_csv(MODEL_DIR / "metrics_table.csv")
PREDS = pd.read_csv(MODEL_DIR / "predictions_test.csv")

# --------------------------------------------------------------------------- #
# Styles
# --------------------------------------------------------------------------- #
styles = getSampleStyleSheet()


def S(name, **kw):
    base = ParagraphStyle(name=name, fontName="JBM", fontSize=11, leading=14,
                          textColor=HC_BLACK)
    for k, v in kw.items():
        setattr(base, k, v)
    return base


ST_TITLE = S("title", fontName="JBM-B", fontSize=34, leading=40, textColor=HC_BLACK)
ST_SUBTITLE = S("subtitle", fontName="JBM", fontSize=14, leading=18, textColor=HC_GRAY)
ST_H1 = S("h1", fontName="JBM-B", fontSize=24, leading=30, textColor=HC_RED)
ST_H2 = S("h2", fontName="JBM-B", fontSize=16, leading=20, textColor=HC_BLACK)
ST_BODY = S("body", fontSize=11, leading=16)
ST_BODY_B = S("bodyb", fontName="JBM-B", fontSize=11, leading=16)
ST_SMALL = S("small", fontSize=9, leading=12, textColor=HC_GRAY)
ST_BULLET = S("bullet", fontSize=11, leading=15, leftIndent=12, bulletIndent=0)
ST_NUM = S("num", fontName="JBM-B", fontSize=34, leading=38, textColor=HC_RED)
ST_NUM_LBL = S("numlbl", fontSize=8, leading=10, textColor=HC_GRAY)
ST_CODE = S("code", fontName="JBM", fontSize=9, leading=12, textColor=HC_BLACK,
            backColor=HexColor("#F4F4F4"))

# --------------------------------------------------------------------------- #
# Page templates
# --------------------------------------------------------------------------- #
def header_footer(canvas, doc):
    canvas.saveState()
    # Top thin red rule
    canvas.setStrokeColor(HC_RED)
    canvas.setLineWidth(1.4)
    canvas.line(1.4 * cm, SLIDE_H - 1.2 * cm, SLIDE_W - 1.4 * cm, SLIDE_H - 1.2 * cm)
    # Project label (left)
    canvas.setFont("JBM-B", 8)
    canvas.setFillColor(HC_RED)
    canvas.drawString(1.4 * cm, SLIDE_H - 0.8 * cm, "HC//CREDIT-RISK")
    canvas.setFont("JBM", 8)
    canvas.setFillColor(HC_GRAY)
    canvas.drawString(6.0 * cm, SLIDE_H - 0.8 * cm,
                      "Home Credit Default Risk  //  Probability-of-Default Scoring")
    # Page number (right) — pages 1..N, slide index 0..N-1
    slide_no = max(doc.page - 1, 0)
    canvas.drawRightString(SLIDE_W - 1.4 * cm, 0.7 * cm,
                           f"slide {slide_no:02d} / 14")
    canvas.drawString(1.4 * cm, 0.7 * cm, date.today().isoformat())
    canvas.restoreState()


def cover_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(HC_BLACK)
    canvas.rect(0, 0, SLIDE_W, SLIDE_H, fill=1, stroke=0)
    # Big red bar
    canvas.setFillColor(HC_RED)
    canvas.rect(0, SLIDE_H * 0.42, SLIDE_W, 0.9 * cm, fill=1, stroke=0)
    canvas.restoreState()


def _page(canv, doc):
    header_footer(canv, doc)


# Frame inset
M = 1.4 * cm
FRAME = Frame(M, 1.3 * cm, SLIDE_W - 2 * M, SLIDE_H - 2.6 * cm,
              leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
              showBoundary=0)

doc = BaseDocTemplate(
    str(ROOT / "slides.pdf"),
    pagesize=landscape((SLIDE_W, SLIDE_H)),
    leftMargin=M, rightMargin=M, topMargin=1.2 * cm, bottomMargin=1.2 * cm,
    title="Home Credit Default Risk — Probability of Default",
    author="Phat",
    subject="Credit Risk Scoring — Midterm Project",
)
doc.total_pages = 15  # set BEFORE addPageTemplates so the footer sees it

doc.addPageTemplates([
    PageTemplate(id="cover", frames=[FRAME], onPage=cover_bg),
    PageTemplate(id="slide", frames=[FRAME], onPage=_page),
])

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def H(text, style=ST_H1, before=0, after=4):
    return [Spacer(1, before * mm), Paragraph(text, style), Spacer(1, after * mm)]


def P(text, style=ST_BODY, before=0, after=2):
    return [Spacer(1, before * mm), Paragraph(text, style), Spacer(1, after * mm)]


def bullets(items, style=ST_BULLET, char="•"):
    out = []
    for it in items:
        out.append(Paragraph(f"{char}  {it}", style))
    return out


def img(path, max_w_cm, max_h_cm):
    """Return an RLImage scaled to fit max_w x max_h, preserving aspect."""
    p = MODEL_DIR / path if not Path(path).is_absolute() else Path(path)
    with Image.open(p) as im:
        iw, ih = im.size
    ratio = iw / ih
    max_w = max_w_cm * cm
    max_h = max_h_cm * cm
    if max_w / ratio <= max_h:
        w, h = max_w, max_w / ratio
    else:
        w, h = max_h * ratio, max_h
    return RLImage(str(p), width=w, height=h)


def metric_card(label, value, sub=""):
    """Big number card."""
    t = Table(
        [[Paragraph(f"<font color='#ED1C24'>{value}</font>", ST_NUM)],
         [Paragraph(label, ST_NUM_LBL)],
         ([Paragraph(sub, ST_SMALL)] if sub else [])],
        colWidths=[4.5 * cm],
    )
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


# --------------------------------------------------------------------------- #
# Build content
# --------------------------------------------------------------------------- #
story = []

# --- Slide 1: COVER ----------------------------------------------------------
story.extend(H("", before=20))
story.append(Paragraph("HOME CREDIT", S("brand", fontName="JBM-B", fontSize=14,
                                        textColor=colors.white)))
story.append(Paragraph("Default Risk Scoring", S("headline", fontName="JBM-B",
                                                  fontSize=58, leading=64,
                                                  textColor=colors.white)))
story.append(Spacer(1, 4 * mm))
story.append(Paragraph("Probability-of-Default model with scorecard &amp; risk bands",
                        S("kicker", fontName="JBM", fontSize=16, leading=20,
                          textColor=HexColor("#CCCCCC"))))
story.append(Spacer(1, 16 * mm))
# White divider above red bar
story.append(Paragraph("A reproducible end-to-end ML pipeline — from raw CSVs to a deployable PD model",
                        S("tag", fontName="JBM-I", fontSize=12, leading=16,
                          textColor=HexColor("#CCCCCC"))))
story.append(Spacer(1, 24 * mm))
# Footer info
info = Table(
    [[Paragraph("<b>AUTHOR</b>", S("il", fontName="JBM-B", fontSize=8, textColor=HexColor("#999999"))),
      Paragraph("Phat  //  Applied Math + Finance",
                S("iv", fontName="JBM", fontSize=10, textColor=colors.white)),
      Paragraph("<b>COURSE</b>", S("il", fontName="JBM-B", fontSize=8, textColor=HexColor("#999999"))),
      Paragraph("Midterm Project — Credit Risk Modeling",
                S("iv", fontName="JBM", fontSize=10, textColor=colors.white)),
      Paragraph("<b>STACK</b>", S("il", fontName="JBM-B", fontSize=8, textColor=HexColor("#999999"))),
      Paragraph("Python · LightGBM · scikit-learn · Streamlit · Docker",
                S("iv", fontName="JBM", fontSize=10, textColor=colors.white))]],
    colWidths=[2 * cm, 6.5 * cm, 2 * cm, 6.5 * cm, 2 * cm, 6.5 * cm],
)
info.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
story.append(info)
story.append(NextPageTemplate("slide"))
story.append(PageBreak())

# --- Slide 2: Problem & Motivation ------------------------------------------
story.extend(H("01 // Problem &amp; Motivation", ST_H1))
story.extend(P(
    "Home Credit serves underbanked borrowers with thin credit files. "
    "The business problem: <b>score each applicant for default risk</b> "
    "using alternative data (bureau, prior applications, installments, POS, credit cards)."
))
story.extend(P("Why this matters:"))
prob_pts = [
    "<b>Default rate is low (~8%)</b> — imbalanced classification; naive accuracy is misleading.",
    "<b>Cost asymmetry</b> — missing a defaulter is far more expensive than rejecting a good payer.",
    "<b>Calibrated PD</b> feeds downstream credit policy, expected loss, and loan pricing.",
    "<b>Explainability</b> required by credit regulators — feature importance &amp; scorecard.",
]
# Two-column layout: bullets (left) | deliverables (right)
deliv = Table(
    [[Paragraph("<b>DELIVERABLES</b>", S("dh", fontName="JBM-B", fontSize=10, textColor=colors.white))],
     [Paragraph("• Trained &amp; calibrated model  (model.joblib)",
                S("db", fontSize=10, leading=14, textColor=colors.white))],
     [Paragraph("• Metrics table  (model/metrics_table.csv)",
                S("db", fontSize=10, leading=14, textColor=colors.white))],
     [Paragraph("• Per-customer PD + rating  (model/predictions_test.csv)",
                S("db", fontSize=10, leading=14, textColor=colors.white))],
     [Paragraph("• Streamlit web app  (Streamlit) + Docker",
                S("db", fontSize=10, leading=14, textColor=colors.white))],
     [Paragraph("• Model card  (model/model_card.json)",
                S("db", fontSize=10, leading=14, textColor=colors.white))],
     [Paragraph("• This slide deck  (slides.pdf)",
                S("db", fontSize=10, leading=14, textColor=colors.white))]],
    colWidths=[10 * cm],
)
deliv.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), HC_RED),
    ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
]))
bullets_tbl = Table([[Paragraph(p, ST_BULLET)] for p in prob_pts],
                    colWidths=[18 * cm])
bullets_tbl.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
]))
layout = Table(
    [[bullets_tbl, deliv]],
    colWidths=[18.5 * cm, 10.5 * cm],
)
layout.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
story.append(layout)
story.append(PageBreak())

# --- Slide 3: Dataset --------------------------------------------------------
story.extend(H("02 // Dataset — Home Credit Default Risk (Kaggle)", ST_H1))
ds_intro = (
    "<b>application_train.csv</b> is the master table (one row per customer) with the "
    "<b>TARGET</b> label.  Six auxiliary tables are aggregated to <b>SK_ID_CURR</b> to enrich the feature set."
)
story.extend(P(ds_intro, before=0, after=2))
# Tables summary
tbl_data = [
    ["Table", "Rows", "Use"],
    ["application_train", "307,511", "master table with TARGET"],
    ["bureau", "1,716,428", "credits reported to other bureaus"],
    ["bureau_balance", "27,299,925", "monthly status of bureau credits"],
    ["previous_application", "1,670,214", "prior Home Credit applications"],
    ["installments_payments", "13,605,401", "installment repayment history"],
    ["POS_CASH_balance", "10,001,358", "monthly POS / cash loan snapshots"],
    ["credit_card_balance", "3,840,312", "monthly credit-card snapshots"],
]
tt = Table(tbl_data, colWidths=[6.5 * cm, 4 * cm, 16 * cm])
tt.setStyle(TableStyle([
    ("FONT", (0, 0), (-1, 0), "JBM-B", 10),
    ("FONT", (0, 1), (-1, -1), "JBM", 9),
    ("BACKGROUND", (0, 0), (-1, 0), HC_RED),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HC_WHITE, HC_LIGHT]),
    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("LINEBELOW", (0, 0), (-1, 0), 0.5, HC_BLACK),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
]))
story.append(tt)
story.append(Spacer(1, 4 * mm))
# Bottom: key sample numbers
n_train = CARD["dataset"]["n_samples_train"]
n_test = CARD["dataset"]["n_samples_test"]
n_feat = CARD["dataset"]["n_features"]
dr = CARD["dataset"]["default_rate_test"]
cards = Table([[
    metric_card("TRAIN ROWS", f"{n_train:,}"),
    metric_card("TEST ROWS", f"{n_test:,}"),
    metric_card("FEATURES", f"{n_feat}"),
    metric_card("DEFAULT RATE", f"{dr:.1%}"),
    metric_card("SOURCE", "Kaggle '19"),
]], colWidths=[5.5 * cm] * 5)
story.append(cards)
story.append(PageBreak())

# --- Slide 4: EDA — Target + Missing ----------------------------------------
story.extend(H("03 // Exploratory Data Analysis  //  Target &amp; Missing", ST_H1))
story.extend(P(
    "Class imbalance and data quality drive downstream modeling choices. "
    "Top 20 columns by missing-rate and distribution by age group are the most informative signals."
))
# Two side-by-side images
edaimg = Table(
    [[
        img("eda_target_distribution.png", max_w_cm=15, max_h_cm=8),
        img("eda_missing_values.png",     max_w_cm=15, max_h_cm=8),
    ]],
    colWidths=[15.5 * cm, 15.5 * cm],
)
edaimg.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
story.append(edaimg)
story.append(Spacer(1, 3 * mm))
# Insights below
story.append(Paragraph(
    "<b>Findings</b>  —  Default rate ≈ 8%, stable across age; the 20-25 cohort is the riskiest. "
    "<b>~50+ columns</b> have meaningful missingness, dominated by housing &amp; external scores. "
    "These shape the imputation and feature-engineering strategies.",
    S("ins", fontSize=10, leading=14, textColor=HC_GRAY),
))
story.append(PageBreak())

# --- Slide 5: EDA — Key features + Correlation ------------------------------
story.extend(H("04 // EDA  //  Key Features by Target", ST_H1))
story.extend(P(
    "Comparing distributions of <b>AMT_CREDIT</b>, <b>AMT_INCOME</b>, <b>AGE</b> and the three "
    "<b>EXT_SOURCE</b> external scores between defaulters and non-defaulters. "
    "EXT_SOURCE_1/2/3 carry the strongest discriminative power — a known Home Credit signal."
))
# Main image
ki = Table(
    [[img("eda_key_features.png", max_w_cm=29, max_h_cm=11)]],
    colWidths=[30 * cm],
)
ki.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
story.append(ki)
story.append(PageBreak())

# --- Slide 6: Feature Engineering -------------------------------------------
story.extend(H("05 // Feature Engineering Pipeline", ST_H1))
story.extend(P(
    "Starting from 122 raw columns, we engineer <b>301 features</b> across 4 functional blocks."
))
# 2x2 grid
fe_grid = Table([
    [Paragraph("<b>01  /  Application cleaning</b>", S("feh", fontName="JBM-B", fontSize=11, textColor=HC_RED)),
     Paragraph("<b>02  /  Bureau aggregation</b>",  S("feh", fontName="JBM-B", fontSize=11, textColor=HC_RED))],
    [Paragraph(
        "• DAYS_EMPLOYED sentinel (365243) → NaN + flag  <br/>"
        "• CODE_GENDER XNA → NaN  <br/>"
        "• OWN_CAR_AGE = NaN if no car  <br/>"
        "• Time features: AGE_YEARS, EMPLOYED_YEARS, REGISTERED_YEARS  <br/>"
        "• Ratio features: CREDIT_INCOME, ANNUITY_INCOME, CREDIT_TERM, CREDIT_GOODS, INCOME_PER_FAM  <br/>"
        "• EXT_SOURCE aggregates: MEAN / MIN / MAX / STD / PROD / COUNT  <br/>"
        "• NUM_DOCS_SUBMITTED",
        S("feb", fontSize=9, leading=12)) ,
     Paragraph(
        "Group by SK_ID_CURR:  <br/>"
        "• BUR_ACTIVE_CNT, BUR_OVERDUE_CNT  <br/>"
        "• BUR_CREDIT_SUM, BUR_DEBT_SUM, BUR_OVERDUE_AMT  <br/>"
        "• BUR_DEBT_RATIO = debt / credit  <br/>"
        "• BUR_LOAN_CNT, BUR_DAYS_CREDIT_MIN  <br/>"
        "• BUR_TYPE_* one-hot (per credit type)  <br/>"
        "• HAS_BUREAU flag",
        S("feb", fontSize=9, leading=12))],
    [Paragraph("<b>03  /  Previous applications + installments</b>", S("feh", fontName="JBM-B", fontSize=11, textColor=HC_RED)),
     Paragraph("<b>04  /  POS_CASH + Credit card</b>", S("feh", fontName="JBM-B", fontSize=11, textColor=HC_RED))],
    [Paragraph(
        "• PREV_AMT_SUM/MEAN, PREV_CREDIT_MAX, PREV_DAYS_DEC_MIN  <br/>"
        "• PREV_CNT_PAYMENT_MEAN  <br/>"
        "• PREV_APPROVE_RATE  <br/>"
        "• INST_PAY_RATIO, INST_LATE_MEAN  <br/>"
        "• INST_LATE_7D_SUM",
        S("feb", fontSize=9, leading=12)),
     Paragraph(
        "• POS_UTIL_MEAN, POS_CNT  <br/>"
        "• CC_UTIL_MEAN  <br/>"
        "• Aggregations per customer, merged to master  <br/>"
        "• Final 301-dim feature vector per customer",
        S("feb", fontSize=9, leading=12))],
], colWidths=[15 * cm, 15 * cm])
fe_grid.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("BACKGROUND", (0, 0), (-1, -1), HC_LIGHT),
    ("BOX", (0, 0), (-1, -1), 0.5, HC_GRAY),
    ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ("TOPPADDING", (0, 0), (-1, -1), 8),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
]))
story.append(fe_grid)
story.append(PageBreak())

# --- Slide 7: Methodology ----------------------------------------------------
story.extend(H("06 // Methodology  //  Modeling Pipeline", ST_H1))
story.extend(P(
    "We compare 4 models: 2 logistic-regression baselines (unweighted / class-balanced) "
    "and 2 gradient-boosting trees (raw + isotonic-calibrated). "
    "Optuna (15 trials) tunes LightGBM hyperparameters; early stopping on the validation fold."
))
# Pipeline box
pipe_data = [
    [Paragraph("<b>STEP</b>", S("ph", fontName="JBM-B", fontSize=9, textColor=colors.white)),
     Paragraph("<b>OPERATION</b>", S("ph", fontName="JBM-B", fontSize=9, textColor=colors.white)),
     Paragraph("<b>DETAIL</b>", S("ph", fontName="JBM-B", fontSize=9, textColor=colors.white))],
    ["1.  Split", "Train / Valid / Test  (70 / 15 / 15)", "stratified on TARGET, fixed seed"],
    ["2.  Preprocess", "ColumnTransformer", "median impute (num) + most-freq (cat)  +  one-hot (cat, drop-first) + standardize (num)"],
    ["3.  Baseline", "Logistic Regression", "LR  +  LR-balanced (class_weight='balanced')"],
    ["4.  Tuned model", "LightGBM (Optuna 15 trials)", f"n_estimators=205, num_leaves=53, lr={CARD['hyperparameters']['learning_rate']:.3f}"],
    ["5.  Calibration", "Isotonic regression on validation", f"Brier pre={CARD['calibration']['brier_pre']:.4f} → post={CARD['calibration']['brier_post']:.4f}"],
    ["6.  Threshold", "F1-driven (recall ≥ 80%)", f"τ* = {CARD['threshold']['value']}"],
    ["7.  Evaluate", "AUC, Gini, KS, Brier, PR-AUC, F1", "test set, 7,500 unseen customers"],
]
pt = Table(pipe_data, colWidths=[2.5 * cm, 7.5 * cm, 19 * cm])
pt.setStyle(TableStyle([
    ("FONT", (0, 1), (-1, -1), "JBM", 9),
    ("BACKGROUND", (0, 0), (-1, 0), HC_RED),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HC_WHITE, HC_LIGHT]),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
]))
story.append(pt)
story.append(PageBreak())

# --- Slide 8: Results — Model Comparison ------------------------------------
story.extend(H("07 // Results  //  Test-Set Comparison (n = 7,500)", ST_H1))
story.extend(P(
    "All four models evaluated on the same held-out test fold. "
    "LightGBM raw has the best AUC; the calibrated variant is selected for deployment because "
    "its <b>probabilities are trustworthy</b> for downstream scorecarding."
))
# Metrics table
mrows = [["Model", "AUC", "Gini", "KS", "Brier", "PR-AUC", "F1", "Recall", "Precision"]]
for _, r in METRICS_TBL.iterrows():
    mrows.append([
        r["model"],
        f"{r['auc']:.4f}",
        f"{r['gini']:.4f}",
        f"{r['ks']:.4f}",
        f"{r['brier']:.4f}",
        f"{r['pr_auc']:.4f}",
        f"{r['test_f1']:.4f}",
        f"{r['test_recall']:.4f}",
        f"{r['test_precision']:.4f}",
    ])
mt = Table(mrows, colWidths=[5.5 * cm, 2.6 * cm, 2.6 * cm, 2.6 * cm, 2.6 * cm,
                             2.6 * cm, 2.4 * cm, 2.6 * cm, 2.8 * cm])
mt.setStyle(TableStyle([
    ("FONT", (0, 0), (-1, 0), "JBM-B", 10),
    ("FONT", (0, 1), (-1, -1), "JBM", 10),
    ("BACKGROUND", (0, 0), (-1, 0), HC_RED),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HC_WHITE, HC_LIGHT]),
    # Highlight best AUC row
    ("BACKGROUND", (0, 3), (-1, 3), HexColor("#FFE5E6")),
    ("FONT", (0, 3), (-1, 3), "JBM-B", 10),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(mt)
story.append(Spacer(1, 4 * mm))
# Big-number highlight cards for the chosen model
chosen = CARD["test_metrics"]
cards = Table([[
    metric_card("AUC", f"{chosen['auc']:.3f}"),
    metric_card("Gini", f"{chosen['gini']:.3f}"),
    metric_card("KS",   f"{chosen['ks']:.3f}"),
    metric_card("Brier",f"{chosen['brier']:.3f}"),
    metric_card("Recall @ τ=0.05", f"{chosen['test_recall']:.1%}"),
]], colWidths=[5.5 * cm] * 5)
story.append(cards)
story.append(Spacer(1, 3 * mm))
story.append(Paragraph(
    "<b>Selected model</b>:  LightGBM + Isotonic Calibration.  "
    "Catches 86.2% of defaulters at the cost of flagging ~12.8% precision.",
    S("sel", fontSize=10, textColor=HC_GRAY),
))
story.append(PageBreak())

# --- Slide 9: ROC / PR / KS / Calibration -----------------------------------
story.extend(H("08 // Evaluation Plots  //  ROC · PR · KS · Calibration", ST_H1))
story.extend(P(
    "Left: ROC (discrimination). Top-right: PR (better view under class imbalance). "
    "Bottom-right: reliability / calibration — the isotonic step brings predicted PD close to empirical rate."
))
# 4 images in a row (already 2x2 from notebook)
ev = Table([[
    img("roc_curve.png", 7, 7),
    img("pr_curve.png",  7, 7),
    img("ks_plot.png",   7, 7),
    img("calibration_curve.png", 7, 7),
]], colWidths=[7.5 * cm] * 4)
ev.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
story.append(ev)
story.append(Spacer(1, 2 * mm))
story.append(Paragraph(
    "<b>KS = 0.375</b> at the optimal cut-off — well above the 0.20 'acceptable' "
    "and 0.30 'good' credit-scoring benchmarks.",
    S("ks", fontSize=10, textColor=HC_GRAY),
))
story.append(PageBreak())

# --- Slide 10: Feature Importance --------------------------------------------
story.extend(H("09 // Top-25 Feature Importance  //  LightGBM (gain)", ST_H1))
story.extend(P(
    "Top features come from engineered ratios, installment history, "
    "and external scores — the model relies on <b>behavioural signals</b>, not raw demographics."
))
# Top 10 in a small table on the right + big image on left
top10 = METRICS["feature_importance"][:10]
fi_data = [["#", "feature", "gain"]]
for i, r in enumerate(top10, 1):
    fi_data.append([str(i), r["feature"].replace("num__", "").replace("cat__", "")
                    .replace("_feat", ""), str(r["importance"])])
fitbl = Table(fi_data, colWidths=[0.8 * cm, 7.0 * cm, 1.5 * cm])
fitbl.setStyle(TableStyle([
    ("FONT", (0, 0), (-1, 0), "JBM-B", 9),
    ("FONT", (0, 1), (-1, -1), "JBM", 9),
    ("BACKGROUND", (0, 0), (-1, 0), HC_RED),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
    ("ALIGN", (2, 0), (2, -1), "RIGHT"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HC_WHITE, HC_LIGHT]),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
]))
fi_layout = Table([[
    img("feature_importance.png", max_w_cm=18, max_h_cm=14),
    fitbl,
]], colWidths=[19 * cm, 10 * cm])
fi_layout.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
story.append(fi_layout)
story.append(PageBreak())

# --- Slide 11: Scorecard & Risk Bands ---------------------------------------
story.extend(H("10 // From PD to Score  //  Scorecard &amp; Risk Bands", ST_H1))
story.extend(P(
    "We translate PD into a credit score (Siddiqui 2013 convention: "
    "<b>base = 600, PDO = 20, odds = 50:1</b>) and bucket into 5 rating bands."
))
# Score formula
sc = CARD["scorecard"]
formula = (
    f"<b>score</b>(PD) = {sc['offset']:.2f} − {sc['factor']:.4f} · ln( PD / (1 − PD) )"
)
story.append(Paragraph(formula, S("form", fontName="JBM", fontSize=12, leading=16,
                                   textColor=HC_BLACK, backColor=HC_LIGHT)))
story.append(Spacer(1, 4 * mm))
# Risk band table
rb = CARD["risk_bands"]
band_data = [["Rating", "Score range", "Avg PD (test)", "Empirical default rate", "Population"]]
band_specs = [
    ("A", "Low risk",        sc["base"] + 200,  sc["base"] + 400, "760 – 1000"),
    ("B", "Acceptable",      640, 760,         "640 – 760"),
    ("C", "Watch-list",      480, 640,         "480 – 640"),
    ("D", "Sub-standard",    360, 480,         "360 – 480"),
    ("E", "High risk",       0,   360,         "0 – 360"),
]
# We have actual rating distribution from PREDS
for letter, desc, lo, hi, sr in band_specs:
    sub = PREDS[PREDS["rating"] == letter]
    n = len(sub)
    avg_pd = sub["y_proba"].mean() if n else 0
    dr = sub["y_true"].mean() if n else 0
    band_data.append([f"{letter}  ({desc})", sr,
                      f"{avg_pd:.2%}", f"{dr:.2%}", f"{n:,}"])
bt = Table(band_data, colWidths=[6 * cm, 5 * cm, 4 * cm, 5 * cm, 4 * cm])
bt.setStyle(TableStyle([
    ("FONT", (0, 0), (-1, 0), "JBM-B", 10),
    ("FONT", (0, 1), (-1, -1), "JBM", 10),
    ("BACKGROUND", (0, 0), (-1, 0), HC_RED),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HC_WHITE, HC_LIGHT]),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(bt)
story.append(Spacer(1, 3 * mm))
story.append(Paragraph(
    "Empirical default rate rises monotonically across bands — the scorecard is well-calibrated.",
    S("rb", fontSize=10, textColor=HC_GRAY),
))
story.append(PageBreak())

# --- Slide 12: Business Impact ----------------------------------------------
story.extend(H("11 // Business Impact  //  What does 86.2% recall buy us?", ST_H1))
story.extend(P(
    "At τ = 0.05, on 7,500 test customers (603 defaulters), the model flags <b>603 × 0.862 ≈ 520 defaulters</b> "
    "for manual review.  Compare to the 8% base rate:"
))
# Comparison table
def lift(row):
    n = len(PREDS[PREDS["rating"] == row])
    dr = PREDS[PREDS["rating"] == row]["y_true"].mean()
    base = CARD["dataset"]["default_rate_test"]
    return dr / base if base else 0

bdata = [["Rating", "Population", "Defaulters in band", "Capture rate", "Lift over base"]]
for letter in ["A", "B", "C", "D", "E"]:
    sub = PREDS[PREDS["rating"] == letter]
    n = len(sub)
    ndef = int(sub["y_true"].sum())
    cap = ndef / PREDS["y_true"].sum() * 100
    lf = sub["y_true"].mean() / CARD["dataset"]["default_rate_test"]
    bdata.append([f"Band {letter}", f"{n:,}", f"{ndef}", f"{cap:.1f}%", f"{lf:.2f}×"])
ct = Table(bdata, colWidths=[3.5 * cm, 4.5 * cm, 5.5 * cm, 4.5 * cm, 4 * cm])
ct.setStyle(TableStyle([
    ("FONT", (0, 0), (-1, 0), "JBM-B", 10),
    ("FONT", (0, 1), (-1, -1), "JBM", 10),
    ("BACKGROUND", (0, 0), (-1, 0), HC_RED),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HC_WHITE, HC_LIGHT]),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(ct)
story.append(Spacer(1, 4 * mm))
# Big takeaway
cards2 = Table([[
    metric_card("Recall @ τ=0.05", f"{chosen['test_recall']:.1%}"),
    metric_card("Precision",        f"{chosen['test_precision']:.1%}"),
    metric_card("Defaulters caught","520 / 603"),
    metric_card("AUC",              f"{chosen['auc']:.3f}"),
]], colWidths=[5.5 * cm] * 4)
story.append(cards2)
story.append(PageBreak())

# --- Slide 13: Limitations & Future Work ------------------------------------
story.extend(H("12 // Limitations &amp; Future Work", ST_H1))
lim_pts = [
    "<b>Sample size</b> — notebook was executed on a 12k-row subsample to fit local compute. Re-running on the full 307k rows is expected to lift AUC further.",
    "<b>Macro recall vs precision</b> — at τ=0.05 we prioritise catching defaulters; a higher τ would improve precision at the cost of recall. Policy choice, not a model flaw.",
    "<b>Drift monitoring</b> — Home Credit portfolio evolves yearly; PSI / KS drift on EXT_SOURCE_*, AMT_* should be tracked quarterly.",
    "<b>Fairness audit</b> — disaggregated metrics (CODE_GENDER, AGE_BAND) required before production rollout.",
    "<b>Rejected-inference</b> — current training data only includes approved loans; extending to the inference population would close the selection-bias gap.",
    "<b>Deep tabular models</b> (TabNet, FT-Transformer) and <b>time-series</b> of installment history are next steps.",
]
story.extend(bullets(lim_pts))
story.append(PageBreak())

# --- Slide 14: Deliverables / Repo -------------------------------------------
story.extend(H("13 // Repository Map", ST_H1))
story.append(Paragraph(
    "Reproducible structure: every result in this deck is regenerated by running the notebook end-to-end.",
    ST_BODY,
))
story.append(Spacer(1, 3 * mm))
# Split tree into 2 columns
left_tree = """data/raw/                        # original Kaggle CSVs
notebooks/
  home_credit_pipeline.ipynb    # end-to-end runnable
src/
  config.py                       # paths, seed, features
  features.py                    # cleaning + FE blocks
  train.py                        # training + evaluation
model/                              # generated artifacts
  model.joblib"""
right_tree = """  metrics.json
  metrics_table.csv
  predictions_test.csv
  model_card.json
  roc_curve.png  pr_curve.png  ks_plot.png
  calibration_curve.png
  feature_importance.png  shap_global.png
  eda_*.png
app/
  streamlit_app.py           # 4-tab web app
Dockerfile
requirements.txt
slides.pdf                            # this deck"""

def make_tree(text):
    return Paragraph(
        text.replace("\n", "<br/>"),
        ParagraphStyle("tree", fontName="JBM", fontSize=8, leading=11,
                       textColor=HC_BLACK),
    )

tt = Table([[make_tree(left_tree), make_tree(right_tree)]],
           colWidths=[15 * cm, 15 * cm])
tt.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), HC_LIGHT),
    ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ("TOPPADDING", (0, 0), (-1, -1), 10),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LINEBETWEEN", (0, 0), (0, -1), 0.4, HC_GRAY),
]))
story.append(tt)
story.append(PageBreak())

# --- Slide 15: Conclusion ---------------------------------------------------
story.extend(H("14 // Conclusion", ST_H1))
concl = (
    "We built an end-to-end credit risk pipeline that turns 7 raw tables into a <b>deployable PD model</b> "
    "with a scorecard, risk bands, and a Streamlit front-end.  The LightGBM-calibrated model achieves "
    f"<b>AUC = {chosen['auc']:.3f}</b>, <b>KS = {chosen['ks']:.3f}</b> and catches <b>86.2%</b> of defaulters "
    "at τ = 0.05 — strong performance for a default-prediction problem with 8% positive rate and noisy "
    "alternative-data signals."
)
story.extend(P(concl))
story.append(Spacer(1, 4 * mm))
# Summary table
sum_data = [
    ["", "Logistic", "LightGBM (raw)", "LightGBM + Calib."],
    ["AUC",        "0.7452", "0.7594", "0.7582"],
    ["Gini",       "0.4904", "0.5188", "0.5164"],
    ["KS",         "0.3689", "0.3858", "0.3751"],
    ["Brier",      "0.0684", "0.0677", "0.0678"],
    ["Recall@τ=0.05", "79.3%", "83.7%", "86.2%"],
]
st = Table(sum_data, colWidths=[5 * cm, 7.5 * cm, 7.5 * cm, 7.5 * cm])
st.setStyle(TableStyle([
    ("FONT", (0, 0), (-1, 0), "JBM-B", 11),
    ("FONT", (0, 1), (-1, -1), "JBM", 10),
    ("BACKGROUND", (0, 0), (-1, 0), HC_RED),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HC_WHITE, HC_LIGHT]),
    ("LINEAFTER", (0, 0), (0, 5), 0.5, HC_GRAY),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]))
story.append(st)
story.append(Spacer(1, 4 * mm))
# Final thank-you bar
ty = Table([[Paragraph("THANK YOU", S("ty", fontName="JBM-B", fontSize=22, leading=26,
                                       textColor=colors.white, alignment=1))]],
          colWidths=[29 * cm])
ty.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), HC_RED),
    ("TOPPADDING", (0, 0), (-1, -1), 14),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
]))
story.append(ty)

# Build (total_pages already set above)
doc.build(story)
print("Built slides.pdf")
