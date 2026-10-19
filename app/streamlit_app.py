"""Streamlit Web App for Home Credit Default Risk.

Contains 4 pages (large tabs):
1. Overview — Home Credit introduction + dataset + model summary.
2. EDA — Data exploration with matplotlib.
3. Predict — Form PD + Score + Risk band.
4. Performance — Metrics table + ROC/PR/KS/Calibration + Feature importance.

Run: streamlit run app/streamlit_app.py
Requirements: model must be trained (`model/model.joblib` or `model/model.pkl`).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add project root to sys.path so we can import src.*
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from src import config
from src import data_loader
from src import predict
from src.data_loader import get_sample_df
from src.predict import (
    get_default_customer,
    get_model_info,
    predict_from_record,
    predict_one,
)
from src import features as _features

# 
# JetBrains Mono font (Google Fonts)
# 
JETBRAINS_MONO_FONT = "JetBrains Mono"

st.set_page_config(
    page_title="Home Credit — Default Risk",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
""",
    unsafe_allow_html=True,
)

# 
# Home Credit logo (inline SVG — no external file needed)
# 
HOME_CREDIT_LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 64" width="220" height="50">
  <g>
    <!-- Icon: letter H in red circle -->
    <circle cx="32" cy="32" r="28" fill="#ED1C24"/>
    <rect x="20" y="14" width="6" height="36" fill="#FFFFFF"/>
    <rect x="38" y="14" width="6" height="36" fill="#FFFFFF"/>
    <rect x="20" y="29" width="24" height="6" fill="#FFFFFF"/>
    <!-- Wordmark -->
    <text x="74" y="28" font-family="Arial, Helvetica, sans-serif" font-size="22" font-weight="800" fill="#1A1A1A">HOME</text>
    <text x="74" y="54" font-family="Arial, Helvetica, sans-serif" font-size="22" font-weight="800" fill="#ED1C24">CREDIT</text>
  </g>
</svg>
"""

# 
# Global theme + CSS — JetBrains Mono, Home Credit palette (red #ED1C24, black, white)
# 
st.markdown(
    f"""
<style>
    /* Nền tổng thể */
    .stApp {{
        background-color: #FFFFFF;
        font-family: '{JETBRAINS_MONO_FONT}', ui-monospace, SFMono-Regular, Menlo, monospace !important;
    }}
    html, body, [class*="css"], p, div, span, label, input, button, textarea, select {{
        font-family: '{JETBRAINS_MONO_FONT}', ui-monospace, SFMono-Regular, Menlo, monospace !important;
    }}

    /* Compact header */
    header[data-testid="stHeader"] {{ background-color: transparent; }}

    /* Large TABS (pages) — big, rounded, centered */
    .block-container {{
        padding-top: 3.5rem; /* push tabs up, away from header */
    }}
    /* Container of tab-list: flex centered */
    .stTabs [data-baseweb="tab-list"] {{
        position: relative;
        z-index: 10;
        gap: 8px;
        background-color: transparent;
        padding: 6px 6px;
        border: none;
        border-radius: 14px;
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 0 auto 24px auto;
        width: fit-content;
        box-shadow: 0 4px 18px rgba(15, 15, 15, 0.08);
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 64px;
        padding: 0 36px;
        font-size: 18px;
        font-weight: 700;
        letter-spacing: 1.5px;
        color: #0F0F0F;
        background-color: #FFFFFF;
        border: 1px solid #E5E5E5;
        border-radius: 10px;
        transition: all 0.15s ease;
        text-transform: uppercase;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        color: #ED1C24;
        border-color: #ED1C24;
        background-color: #FFF5F5;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: #ED1C24 !important;
        color: #FFFFFF !important;
        border-color: #ED1C24 !important;
        box-shadow: 0 6px 18px rgba(237, 28, 36, 0.28);
    }}
    .stTabs [data-baseweb="tab-highlight"] {{ background-color: transparent; }}
    .stTabs [data-baseweb="tab-border"] {{ display: none; }}
    .stTabs [data-baseweb="tab-panel"] {{
        padding-top: 12px;
        border: none;
        background-color: transparent;
    }}

    /* Typography */
    h1, h2, h3, h4, h5, h6 {{
        font-family: '{JETBRAINS_MONO_FONT}', monospace !important;
        color: #0F0F0F;
        font-weight: 700;
        letter-spacing: -0.5px;
    }}
    h1 {{ font-size: 36px; }}
    h2 {{ font-size: 26px; border-left: 4px solid #ED1C24; padding-left: 12px; }}
    h3 {{ font-size: 18px; color: #ED1C24; text-transform: uppercase; letter-spacing: 1.5px; }}

    /* Hide spinner arrows of number_input */
    /* Chrome / Edge / Safari */
    input[type="number"]::-webkit-outer-spin-button,
    input[type="number"]::-webkit-inner-spin-button {{
        -webkit-appearance: none;
        margin: 0;
        display: none;
    }}
    /* Firefox */
    input[type="number"] {{
        -moz-appearance: textfield;
    }}
    /* Hide step buttons in other browsers */
    [data-baseweb="input"] button[aria-label*="crement"],
    [data-baseweb="input"] button[aria-label*="up"],
    [data-baseweb="input"] button[aria-label*="down"] {{
        display: none !important;
    }}
    /* Push input content so it is not covered by the default spinner */
    [data-baseweb="input"] input {{
        padding-right: 8px !important;
    }}

    /* Form labels — fix so arrow icons don't overlap text */
    .stNumberInput label, .stTextInput label, .stSelectbox label {{
        margin-bottom: 6px !important;
        padding-right: 28px !important; /* leave room on the right */
    }}
    .stNumberInput > div > div {{
        position: relative;
    }}

    /* Hide chevron icon of st.expander */
    /* Default SVG of expander summary hide completely */
    details summary > svg,
    details summary > *:not(.streamlit-expanderContent) {{
        display: none !important;
    }}
    /* Or replace with a simple custom chevron */
    details summary {{
        list-style: none;
        position: relative;
    }}
    details summary::-webkit-details-marker {{
        display: none;
    }}
    details summary::before {{
        content: "";
        position: absolute;
        left: 10px;
        top: 50%;
        transform: translateY(-50%);
        color: #ED1C24;
        font-size: 14px;
        font-weight: 700;
    }}
    details[open] summary::before {{
        content: "";
    }}
    details summary > * {{
        margin-left: 28px !important; /* push text away from chevron */
    }}

    /* Metric cards */
    div[data-testid="stMetric"] {{
        background-color: #FFFFFF;
        border: 1px solid #E5E5E5;
        border-top: 3px solid #ED1C24;
        padding: 16px 20px;
        border-radius: 4px;
    }}
    div[data-testid="stMetric"] label {{
        color: #6B6B6B !important;
        font-size: 12px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
        font-size: 30px !important;
        font-weight: 800 !important;
        color: #0F0F0F !important;
    }}

    /* Buttons */
    .stButton > button, .stFormSubmitButton > button {{
        background-color: #ED1C24;
        color: #FFFFFF;
        font-weight: 700;
        font-size: 14px;
        letter-spacing: 1px;
        text-transform: uppercase;
        border: none;
        border-radius: 3px;
        padding: 12px 28px;
    }}
    .stButton > button:hover, .stFormSubmitButton > button:hover {{
        background-color: #C8161D;
        color: #FFFFFF;
    }}

    /* Inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {{
        background-color: #FFFFFF;
        border: 1px solid #D5D5D5;
        border-radius: 3px;
        font-size: 13px;
    }}
    .stSelectbox div[data-baseweb="select"] > div:hover {{
        border-color: #ED1C24;
    }}

    /* DataFrames */
    .stDataFrame {{
        border: 1px solid #E5E5E5;
        border-radius: 4px;
    }}

    /* Cards / containers */
    .hc-card {{
        background-color: #FFFFFF;
        border: 1px solid #E5E5E5;
        border-left: 4px solid #ED1C24;
        padding: 20px 24px;
        border-radius: 4px;
        margin-bottom: 16px;
    }}
    .hc-card-dark {{
        background-color: #0F0F0F;
        color: #FFFFFF;
        padding: 24px 28px;
        border-radius: 4px;
        margin-bottom: 16px;
    }}
    .hc-card-dark h3 {{ color: #ED1C24; }}

    .hc-pill {{
        display: inline-block;
        padding: 4px 10px;
        border-radius: 3px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
    }}
    .hc-pill-red {{ background:#ED1C24; color:#FFFFFF; }}
    .hc-pill-green {{ background:#16A34A; color:#FFFFFF; }}
    .hc-pill-amber {{ background:#F59E0B; color:#0F0F0F; }}
    .hc-pill-gray {{ background:#E5E5E5; color:#0F0F0F; }}

    .risk-low {{ color:#16A34A; font-weight: 800; }}
    .risk-mid {{ color:#F59E0B; font-weight: 800; }}
    .risk-hi {{ color:#ED1C24; font-weight: 800; }}

    hr {{ border-color: #E5E5E5; }}
</style>
""",
    unsafe_allow_html=True,
)

# 
# Matplotlib defaults (JetBrains Mono)
# 
plt.rcParams.update({
    "font.family": "monospace",
    "font.monospace": ["JetBrains Mono", "DejaVu Sans Mono", "Courier New"],
    "axes.titlesize": 14,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.facecolor": "#FFFFFF",
    "axes.facecolor": "#FFFFFF",
    "axes.edgecolor": "#0F0F0F",
    "axes.linewidth": 1.0,
    "axes.grid": True,
    "grid.color": "#E5E5E5",
    "grid.linewidth": 0.6,
})


# 
# Cached loaders
# 
@st.cache_data(show_spinner="Loading metrics...")
def load_metrics() -> dict:
    p = config.MODEL_DIR / "metrics.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


@st.cache_data(show_spinner="Loading sample data...")
def load_sample_app(n: int = 5000) -> pd.DataFrame:
    """Lazy-load application_train_sample.csv (5K rows, 2.7MB).

    If the file isn't on disk (e.g. on Streamlit Cloud), it's downloaded
    from the GitHub raw URL the first time and cached locally in
    ``data/raw/``. See ``src.data_loader`` for the downloader.
    """
    try:
        return get_sample_df(nrows=n)
    except FileNotFoundError as e:
        st.error(str(e))
        return pd.DataFrame()


@st.cache_data
def load_eda_stats() -> dict:
    df = load_sample_app(10_000)
    if df.empty:
        return {}
    return {
        "n_rows": len(df),
        "n_cols": df.shape[1],
        "target_rate": float(df["TARGET"].mean()),
        "missing_pct": (df.isna().mean() * 100).round(2).to_dict(),
        "dtypes": {str(k): int(v) for k, v in df.dtypes.value_counts().items()},
    }


@st.cache_data(show_spinner="Loading feature importance...")
def load_feature_importance() -> pd.DataFrame:
    """Get feature importance from artifact (LightGBM.feature_importances_)."""
    # Priority: read directly from the model pickle/joblib
    _, artifact = load_pickle_model()
    if artifact is None:
        return pd.DataFrame()

    # New schema: pipeline = (prep, clf) — clf is LightGBM
    clf = None
    if "pipeline" in artifact and hasattr(artifact["pipeline"], "steps"):
        clf = artifact["pipeline"].steps[-1][1]
    elif "lgb_booster" in artifact:
        clf = artifact["lgb_booster"]

    if clf is None or not hasattr(clf, "feature_importances_"):
        # Fallback: metrics.json (legacy schema)
        info = get_model_info()
        if "metrics" in info and info["metrics"].get("feature_importance"):
            return pd.DataFrame(info["metrics"]["feature_importance"])
        return pd.DataFrame()

    importances = np.asarray(clf.feature_importances_)

    # Get feature names from the preprocessor if available
    feature_names: list[str] = []
    if "pipeline" in artifact and hasattr(artifact["pipeline"], "steps"):
        prep = artifact["pipeline"].steps[0][1]
        feature_names = _safe_get_feature_names(prep, artifact) or []
    if not feature_names:
        feature_names = list(artifact.get("feature_columns") or
                              artifact.get("feature_names") or
                              [f"f_{i}" for i in range(len(importances))])

    n = min(len(importances), len(feature_names))
    df = pd.DataFrame({
        "feature": feature_names[:n],
        "importance": importances[:n].astype(float),
    })
    return df.sort_values("importance", ascending=False).reset_index(drop=True)


def _safe_get_feature_names(prep, artifact) -> list[str] | None:
    """Get feature names from ColumnTransformer, handling steps that do not
    support get_feature_names_out (e.g. _ClipTransformer)."""
    # 1) Try the standard sklearn API first
    try:
        return list(prep.get_feature_names_out())
    except Exception:
        pass

    # 2) Manual fallback: based on prep.transformers_ + artifact num_cols/cat_cols
    if not hasattr(prep, "transformers_"):
        return None
    num_cols = artifact.get("num_cols", [])
    cat_cols = artifact.get("cat_cols", [])
    out: list[str] = []

    for name, trans, cols in prep.transformers_:
        if trans == "drop" or trans is None:
            continue
        cols_list = list(cols) if cols is not None else []
        if name == "num":
            # Numeric pipeline starts with ClipTransformer (does not rename)
            out.extend(cols_list)
        elif name == "cat":
            # Find OneHotEncoder inside the pipeline
            ohe = None
            if hasattr(trans, "named_steps"):
                ohe = trans.named_steps.get("ohe")
            if ohe is not None and hasattr(ohe, "categories_"):
                for i, c in enumerate(cols_list):
                    if i < len(ohe.categories_):
                        for v in ohe.categories_[i]:
                            out.append(f"{c}_{v}")
                    else:
                        out.append(c)
            else:
                out.extend(cols_list)
        else:
            out.extend(cols_list)
    return out

    # Trim to the shorter length
    n = min(len(importances), len(feature_names))
    df = pd.DataFrame({
        "feature": feature_names[:n],
        "importance": importances[:n].astype(float),
    })
    return df.sort_values("importance", ascending=False).reset_index(drop=True)


@st.cache_resource(show_spinner="Loading model artifact (.pkl / .joblib)...")
def load_pickle_model():
    """Load model pickle, cached at resource level (no re-pickle on every rerun)."""
    candidates = [config.MODEL_PATH, config.MODEL_PATH.with_suffix(".pkl")]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        return None, None
    return path, joblib.load(path)


# 
# Page 1: OVERVIEW
# 
def page_overview():
    # Hero
    col_logo, col_text = st.columns([1, 4], vertical_alignment="center")
    with col_logo:
        st.markdown(HOME_CREDIT_LOGO_SVG, unsafe_allow_html=True)
    with col_text:
        st.markdown(
            """
            <div style="padding-top: 6px;">
                <div style="font-size: 13px; color: #6B6B6B; letter-spacing: 2px;
                            text-transform: uppercase; margin-bottom: 4px;">
                    Credit Risk Intelligence Platform
                </div>
                <div style="font-size: 30px; font-weight: 800; color: #0F0F0F;
                            line-height: 1.1;">
                    Home Credit Default Risk
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # KPI cards
    try:
        info = get_model_info()
        metrics = info.get("metrics", {})
        chosen = (
            metrics.get("LightGBM_calibrated")
            or metrics.get("LightGBM")
            or metrics.get("Logistic")
            or {}
        )
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("AUC-ROC", f"{chosen.get('auc', 0):.4f}")
        c2.metric("KS Statistic", f"{chosen.get('ks', 0):.4f}")
        c3.metric("Brier Score", f"{chosen.get('brier', 0):.4f}")
        c4.metric("Recall @ best", f"{chosen.get('recall_at_best', 0):.1%}")
        c5.metric("Threshold", f"{info.get('threshold', 0):.3f}")
    except FileNotFoundError:
        st.warning("Model has not been trained yet. Run the notebook first.")

    st.markdown("")

    # About Home Credit 
    st.markdown("## About Home Credit")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
            <div class="hc-card">
                <h3 style="margin-top:0;">Who we are</h3>
                <p style="font-size: 13px; color: #2A2A2A; line-height: 1.7;">
                <b>Home Credit Group</b> is a leading international consumer finance
                provider founded in <b>1997</b> in the Czech Republic and headquartered
                in the Netherlands. The group operates in <b>9 countries</b>
                across Central & Eastern Europe, Asia and the United States, serving
                more than <b>30 million active customers</b>.</p>
                <p style="font-size: 13px; color: #2A2A2A; line-height: 1.7;">
                Our mission is to <b>promote responsible lending</b> to customers
                who have little or no credit history. By combining alternative
                data sources — telco, retail, and transaction records — we
                enable millions of underbanked households to access fair
                financing.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class="hc-card">
                <h3 style="margin-top:0;">Key facts</h3>
                <table style="width: 100%; font-size: 12px; color: #2A2A2A;
                              border-collapse: collapse;">
                  <tr><td style="padding:6px 0;color:#6B6B6B;">Founded</td>
                          <td style="padding:6px 0;text-align:right;font-weight:700;">1997</td></tr>
                  <tr><td style="padding:6px 0;color:#6B6B6B;">Headquarters</td>
                          <td style="padding:6px 0;text-align:right;font-weight:700;">Eindhoven, NL</td></tr>
                  <tr><td style="padding:6px 0;color:#6B6B6B;">Countries</td>
                          <td style="padding:6px 0;text-align:right;font-weight:700;">9</td></tr>
                  <tr><td style="padding:6px 0;color:#6B6B6B;">Active customers</td>
                          <td style="padding:6px 0;text-align:right;font-weight:700;">30 M+</td></tr>
                  <tr><td style="padding:6px 0;color:#6B6B6B;">POS network</td>
                          <td style="padding:6px 0;text-align:right;font-weight:700;">390 000+</td></tr>
                  <tr><td style="padding:6px 0;color:#6B6B6B;">Listed</td>
                          <td style="padding:6px 0;text-align:right;font-weight:700;">Prague Stock Exchange</td></tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # The problem 
    st.markdown("## The problem we solve")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div class="hc-card-dark">
                <h3 style="margin-top:0;">Challenge</h3>
                <p style="font-size: 13px; color: #D5D5D5; line-height: 1.6;">
                Millions of credit applicants <b style="color:#FFF;">lack a formal
                credit history</b>. Traditional scorecards reject them outright,
                pushing them toward unregulated lenders.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class="hc-card-dark">
                <h3 style="margin-top:0;">Approach</h3>
                <p style="font-size: 13px; color: #D5D5D5; line-height: 1.6;">
                We harness <b style="color:#FFF;">alternative data</b> — bureau,
                previous applications, installment & credit-card statements — to
                build a fair, ML-driven credit score.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
            <div class="hc-card-dark">
                <h3 style="margin-top:0;">Impact</h3>
                <p style="font-size: 13px; color: #D5D5D5; line-height: 1.6;">
                Lower default rates, higher approval for the underbanked, and a
                fully auditable model card aligned with <b style="color:#FFF;">
                EU AI Act</b> & Basel guidelines.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("## Dataset & Pipeline")
    eda = load_eda_stats()
    if eda:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sample rows", f"{eda['n_rows']:,}")
        c2.metric("Columns", eda["n_cols"])
        c3.metric("Default rate", f"{eda['target_rate']:.2%}")
        c4.metric("Numeric cols", eda["dtypes"].get("int64", 0) + eda["dtypes"].get("float64", 0))

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
            <div class="hc-card">
                <h3 style="margin-top:0;">Data sources</h3>
                <ul style="font-size: 12px; color: #2A2A2A; line-height: 1.9;">
                  <li><b>application_train.csv</b> — 307 511 customers × 122 features</li>
                  <li><b>bureau.csv</b> — previous credits at other institutions</li>
                  <li><b>previous_application.csv</b> — prior Home Credit loans</li>
                  <li><b>installments_payments.csv</b> — repayment history</li>
                  <li><b>POS_CASH_balance.csv</b> — POS consumer loans</li>
                  <li><b>credit_card_balance.csv</b> — credit-card statements</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class="hc-card">
                <h3 style="margin-top:0;">Modeling pipeline</h3>
                <ol style="font-size: 12px; color: #2A2A2A; line-height: 1.9;">
                  <li><b>Feature engineering</b> — DTI, credit/income ratio, EXT_SOURCE aggregates, time-based features.</li>
                  <li><b>Preprocessing</b> — median impute + StandardScaler (numeric), OneHot (categorical).</li>
                  <li><b>Model</b> — LightGBM tuned with Optuna (10 trials, AUC maximised).</li>
                  <li><b>Calibration</b> — Isotonic regression on validation split.</li>
                  <li><b>Scorecard</b> — PD FICO-like score (300–850) + 5 risk bands.</li>
                </ol>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Footer
    st.markdown(
        """
        <div style="margin-top: 40px; padding: 16px 0; border-top: 1px solid #E5E5E5;
                    font-size: 11px; color: #6B6B6B; letter-spacing: 1px;
                    text-transform: uppercase;">
            Demo build · Streamlit + LightGBM · © 2026 Home Credit Group
        </div>
        """,
        unsafe_allow_html=True,
    )


# 
# Page 2: EDA (matplotlib only)
# 
def page_eda():
    st.title("Exploratory Data Analysis")
    st.caption("Sample of 10,000 rows from application_train.csv — Matplotlib charts")

    df = load_sample_app(10_000)
    if df.empty:
        st.warning("application_train.csv not found in data/raw/")
        return

    # 1. Target distribution
    st.markdown("### 1. Target Distribution")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6, 2.1))
    target_counts = df["TARGET"].value_counts().sort_index()
    labels = ["Non-default (0)", "Default (1)"]
    colors = ["#16A34A", "#ED1C24"]
    ax1.bar(labels, target_counts.values, color=colors, edgecolor="#0F0F0F", linewidth=0.8)
    for i, v in enumerate(target_counts.values):
        ax1.text(i, v + 200, f"{v:,}", ha="center", fontsize=10, fontweight="bold")
    ax1.set_ylabel("Number of customers")
    ax1.set_title("Counts")
    ax2.pie(
        target_counts.values, labels=labels, colors=colors,
        autopct="%1.2f%%", startangle=90,
        wedgeprops={"edgecolor": "#0F0F0F", "linewidth": 0.8},
        textprops={"fontsize": 10},
    )
    ax2.set_title("Proportion")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # 2. Age distribution
    st.markdown("### 2. Age Distribution by Default Status")
    df["AGE_YEARS"] = -df["DAYS_BIRTH"] / 365.25
    fig, ax = plt.subplots(figsize=(6, 2.1))
    for label, tgt, c in [("Non-default", 0, "#16A34A"), ("Default", 1, "#ED1C24")]:
        sub = df[df["TARGET"] == tgt]["AGE_YEARS"].dropna()
        ax.hist(sub, bins=35, alpha=0.7, label=label, color=c, edgecolor="#0F0F0F", linewidth=0.4)
    ax.set_xlabel("Age (years)")
    ax.set_ylabel("Number of customers")
    ax.set_title("Age histogram by default status")
    ax.legend(frameon=False)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # 3. Default rate by category
    st.markdown("### 3. Default Rate by Gender & Contract Type")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6, 2.1))
    for ax, col, ttl in [(ax1, "CODE_GENDER", "Gender"),
                         (ax2, "NAME_CONTRACT_TYPE", "Contract type")]:
        grp = df.groupby(col)["TARGET"].mean().sort_values(ascending=False)
        bars = ax.barh(grp.index.astype(str), grp.values * 100,
                       color="#ED1C24", edgecolor="#0F0F0F", linewidth=0.8)
        for bar, v in zip(bars, grp.values):
            ax.text(v + 0.3, bar.get_y() + bar.get_height() / 2,
                    f"{v:.1%}", va="center", fontsize=9, fontweight="bold")
        ax.set_xlabel("Default rate (%)")
        ax.set_title(ttl)
        ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # 4. Missing values
    st.markdown("### 4. Top 15 Features with Most Missing Values")
    miss = df.isna().mean().sort_values(ascending=False).head(15) * 100
    fig, ax = plt.subplots(figsize=(5.2, 2.6))
    bars = ax.barh(miss.index, miss.values, color="#ED1C24",
                   edgecolor="#0F0F0F", linewidth=0.8)
    for bar, v in zip(bars, miss.values):
        ax.text(v + 0.4, bar.get_y() + bar.get_height() / 2,
                f"{v:.1f}%", va="center", fontsize=9)
    ax.set_xlabel("% Missing")
    ax.set_xlim(0, 105)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # 5. Interactive explorer
    st.markdown("### 5. Interactive Explorer (Numeric feature × Default)")
    num_cols = [
        "AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY", "DAYS_EMPLOYED",
        "AGE_YEARS", "EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3",
    ]
    num_cols = [c for c in num_cols if c in df.columns]
    sel = st.selectbox("Choose a feature", num_cols)
    if sel:
        c1, c2 = st.columns([2, 1])
        with c1:
            fig, ax = plt.subplots(figsize=(4.2, 2.4))
            data0 = df[df["TARGET"] == 0][sel].dropna()
            data1 = df[df["TARGET"] == 1][sel].dropna()
            # NOTE: matplotlib >=3.9 deprecates `labels=` in boxplot; use
            # `tick_labels=` instead. Cloud runs matplotlib 3.14 which
            # REMOVED the deprecated kwarg, so passing it raises TypeError.
            boxplot_kwargs = dict(
                patch_artist=True,
                boxprops={"facecolor": "#FFFFFF", "edgecolor": "#0F0F0F"},
                medianprops={"color": "#ED1C24", "linewidth": 2},
                whiskerprops={"color": "#0F0F0F"},
                capprops={"color": "#0F0F0F"},
                flierprops={"markerfacecolor": "#ED1C24", "markeredgecolor": "#0F0F0F",
                            "markersize": 3, "alpha": 0.4},
            )
            import matplotlib as mpl
            if mpl.__version__ >= "3.9":
                ax.boxplot([data0, data1], tick_labels=["Non-default (0)", "Default (1)"],
                           **boxplot_kwargs)
            else:
                ax.boxplot([data0, data1], labels=["Non-default (0)", "Default (1)"],
                           **boxplot_kwargs)
            ax.set_ylabel(sel)
            ax.set_title(f"Boxplot: {sel}")
            fig.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        with c2:
            stats = df.groupby("TARGET")[sel].describe()[["mean", "50%", "std"]]
            stats.columns = ["Mean", "Median", "Std"]
            st.dataframe(stats.style.format("{:.2f}"), use_container_width=True)


# 
# Page 3: PREDICT (form + pickle mapping)
# 
def page_predict():
    st.title("Default Risk Prediction")
    st.caption("Fill in customer information Model returns PD, Score, Risk band")

    # Load model pickle (cache_resource) 
    model_path, artifact = load_pickle_model()
    if artifact is None:
        st.error(
            "Model pickle (.pkl / .joblib) not found. "
            "Please run `notebooks/home_credit_pipeline.ipynb` to generate it."
        )
        return

    col_meta, _ = st.columns([1, 3])
    with col_meta:
        st.markdown(
            f"""<span class="hc-pill hc-pill-gray">PKL LOADED</span>
&nbsp;<code style="font-size: 11px;">{model_path.name}</code> · """
            f"""{model_path.stat().st_size / 1024 / 1024:.1f} MB""",
            unsafe_allow_html=True,
        )

    try:
        info = get_model_info()
    except FileNotFoundError as e:
        st.error(str(e))
        return

    defaults = get_default_customer()
    if not defaults:
        st.warning("Could not load a sample customer (application_train.csv is missing).")
        return

    # Form 
    left, right = st.columns([3, 2])

    with left:
        st.markdown("### Customer Information")
        with st.form("predict_form"):
            with st.expander("Personal Information", expanded=True):
                c1, c2 = st.columns(2)
                with c1:
                    age_years = st.number_input(
                        "Age (years)",
                        min_value=18, max_value=100,
                        value=int(abs(defaults.get("DAYS_BIRTH", -16000) / 365.25)),
                        step=1,
                    )
                    gender = st.selectbox(
                        "Gender", ["M", "F", "XNA"],
                        index=["M", "F", "XNA"].index(defaults.get("CODE_GENDER", "F"))
                        if defaults.get("CODE_GENDER") in ["M", "F", "XNA"] else 1,
                    )
                    own_car = st.selectbox(
                        "Owns a car", ["Y", "N"],
                        index=0 if defaults.get("FLAG_OWN_CAR") == "Y" else 1,
                    )
                    own_realty = st.selectbox(
                        "Owns real estate", ["Y", "N"],
                        index=0 if defaults.get("FLAG_OWN_REALTY") == "Y" else 1,
                    )
                with c2:
                    emp_years = st.number_input(
                        "Employment (years)",
                        min_value=0, max_value=80,
                        value=int(abs(defaults.get("DAYS_EMPLOYED", -2000) / 365.25)),
                        step=1,
                    )
                    education = st.selectbox(
                        "Education", [
                            "Secondary / secondary special", "Higher education",
                            "Incomplete higher", "Lower secondary", "Academic degree",
                        ],
                        index=0,
                    )
                    fam_members = st.number_input(
                        "Family members",
                        min_value=1, max_value=20,
                        value=int(defaults.get("CNT_FAM_MEMBERS", 2)),
                    )
                    children = st.number_input(
                        "Number of children", min_value=0, max_value=20,
                        value=int(defaults.get("CNT_CHILDREN", 0)),
                    )

            with st.expander("Financial Information", expanded=True):
                c1, c2 = st.columns(2)
                with c1:
                    income = st.number_input(
                        "Annual income",
                        min_value=0, value=int(defaults.get("AMT_INCOME_TOTAL", 150_000)),
                        step=10_000,
                    )
                    credit = st.number_input(
                        "Credit amount",
                        min_value=0, value=int(defaults.get("AMT_CREDIT", 500_000)),
                        step=10_000,
                    )
                    annuity = st.number_input(
                        "Monthly annuity",
                        min_value=0, value=int(defaults.get("AMT_ANNUITY", 25_000)),
                        step=1_000,
                    )
                with c2:
                    goods = st.number_input(
                        "Goods price",
                        min_value=0, value=int(defaults.get("AMT_GOODS_PRICE", 450_000)),
                        step=10_000,
                    )
                    contract = st.selectbox(
                        "Contract type", ["Cash loans", "Revolving loans"],
                        index=0 if defaults.get("NAME_CONTRACT_TYPE") == "Cash loans" else 1,
                    )

            with st.expander("External scores (EXT_SOURCE)", expanded=False):
                c1, c2, c3 = st.columns(3)
                with c1:
                    ext1 = st.number_input("EXT_SOURCE_1", value=float(defaults.get("EXT_SOURCE_1", 0.5)),
                                            min_value=0.0, max_value=1.0, step=0.01)
                with c2:
                    ext2 = st.number_input("EXT_SOURCE_2", value=float(defaults.get("EXT_SOURCE_2", 0.5)),
                                            min_value=0.0, max_value=1.0, step=0.01)
                with c3:
                    ext3 = st.number_input("EXT_SOURCE_3", value=float(defaults.get("EXT_SOURCE_3", 0.5)),
                                            min_value=0.0, max_value=1.0, step=0.01)

            submitted = st.form_submit_button("PREDICT", use_container_width=True)

    if submitted:
        record = dict(defaults)
        record.update({
            "DAYS_BIRTH": int(-age_years * 365.25),
            "DAYS_EMPLOYED": int(-emp_years * 365.25),
            "CODE_GENDER": gender,
            "FLAG_OWN_CAR": own_car,
            "FLAG_OWN_REALTY": own_realty,
            "NAME_EDUCATION_TYPE": education,
            "CNT_FAM_MEMBERS": fam_members,
            "CNT_CHILDREN": children,
            "AMT_INCOME_TOTAL": income,
            "AMT_CREDIT": credit,
            "AMT_ANNUITY": annuity,
            "AMT_GOODS_PRICE": goods,
            "NAME_CONTRACT_TYPE": contract,
            "EXT_SOURCE_1": ext1,
            "EXT_SOURCE_2": ext2,
            "EXT_SOURCE_3": ext3,
        })

        # Build a 1-row DataFrame with the raw record + fill missing
        # raw columns from defaults so the ColumnTransformer is happy.
        # (FE features like AGE_YEARS, EXT_SOURCE_MEAN, CREDIT_INCOME_RATIO,
        # BUR_*_feat are added inside build_features_for_one_row.)
        _row_df = pd.DataFrame([record])
        for col, val in defaults.items():
            if col not in _row_df.columns:
                _row_df[col] = val
        # Fill any remaining columns (e.g. rare raw fields) with NaN
        try:
            _csv_cols = get_sample_df(nrows=1).columns
            for c in _csv_cols:
                if c not in _row_df.columns and c != "TARGET":
                    _row_df[c] = np.nan
        except Exception:
            pass

        # Engineered features: AGE_YEARS, EXT_SOURCE_MEAN, CREDIT_INCOME_RATIO,
        # BUR_*_feat, etc. — required by the trained ColumnTransformer.
        try:
            _ct = artifact.get("ct") or artifact.get("preprocessor")
            _expected = list(_ct.feature_names_in_) if hasattr(_ct, "feature_names_in_") else None
            _fe_row = _features.build_features_for_one_row(_row_df, expected_cols=_expected)
        except Exception as _fe_err:
            st.warning(f"Feature engineering warning: {_fe_err}. Falling back to raw record.")
            _fe_row = _row_df

        # ── Predict using the SAME path as predict_batch, but read the
        #    correct column names (PD, Score, RiskBand, Decision). ──
        _fe_row = _fe_row.reset_index(drop=True)
        _batch = predict.predict_batch(_fe_row)
        if len(_batch) == 0:
            raise RuntimeError("predict_batch returned empty result")
        _r = _batch.iloc[0]
        result = {
            "pd":         float(_r["PD"]),
            "score":      float(_r["Score"]),
            "risk_band":  str(_r["RiskBand"]),
            "decision":   str(_r["Decision"]),
            "raw_prob":   float(artifact.get("raw_prob", 0.0)),
            "threshold":  float(artifact.get("best_threshold", 0.05)),
            "model_name": str(artifact.get("model_name", "LightGBM_calibrated")),
        }
        # Also get the raw prob (uncalibrated) for transparency
        try:
            _ct_local = artifact.get("ct")
            _lgb_local = artifact.get("lgb")
            if _ct_local is not None and _lgb_local is not None:
                _missing = [c for c in _ct_local.feature_names_in_ if c not in _fe_row.columns]
                if _missing:
                    for c in _missing:
                        _fe_row[c] = np.nan
                _fe_row = _fe_row[list(_ct_local.feature_names_in_)]
                _X_proc = _ct_local.transform(_fe_row)
                result["raw_prob"] = float(_lgb_local.predict_proba(_X_proc)[:, 1][0])
        except Exception:
            pass

        with right:
            st.markdown("### Prediction Result")
            pd_val = result["pd"]
            score = result["score"]
            band = result["risk_band"]
            decision = result["decision"]
            thr = info["threshold"]

            color_map = {
                "Excellent":  "#16A34A",  # green
                "Good":       "#5CB85C",  # light green
                "Fair":       "#F59E0B",  # amber
                "Medium":     "#F59E0B",  # alias
                "Poor":       "#ED1C24",  # red
                "High":       "#ED1C24",  # alias
                "Very Poor":  "#7F1D1D",  # dark red
                "Very High":  "#7F1D1D",  # alias
            }
            color = color_map.get(band, "#6B6B6B")
            pill_class = ("hc-pill-green" if band in ("Excellent", "Good")
                          else "hc-pill-amber" if band in ("Fair", "Medium")
                          else "hc-pill-red")

            st.markdown(
                f"""
                <div class="hc-card" style="border-left-color: {color};">
                    <div style="font-size: 11px; color: #6B6B6B; letter-spacing: 1.5px;
                                text-transform: uppercase;">Probability of Default</div>
                    <div style="font-size: 48px; font-weight: 800; color: {color};
                                line-height: 1.1; margin: 4px 0 12px 0;">
                        {pd_val:.2%}
                    </div>
                    <div style="display:flex; gap: 24px; flex-wrap: wrap;
                                font-size: 13px; color: #2A2A2A;">
                        <div><span style="color:#6B6B6B;">SCORE</span><br>
                            <b style="font-size: 22px;">{score:.0f}</b></div>
                        <div><span style="color:#6B6B6B;">RISK BAND</span><br>
                            <b style="font-size: 22px; color: {color};">{band}</b></div>
                        <div><span style="color:#6B6B6B;">DECISION</span><br>
                            <span class="hc-pill {pill_class}">{decision}</span></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Matplotlib gauge — large semi-circle with 3-zone gradient
            fig, ax = plt.subplots(figsize=(6.0, 3.6))
            pct = min(max(pd_val * 100, 0.0), 100.0)

            # ── 3-zone background (green / amber / red) ────────────────────
            # Effective scale: 0-30% PD fills the entire arc (default rate ≈8%)
            scale_max_pct = 30.0
            scaled_pct = min(pct / scale_max_pct * 100, 100)

            zone_boundaries = [
                (0.0,  0.6,  "#16A34A"),  # 0-60%  → green  (low risk)
                (0.6,  0.85, "#F59E0B"),  # 60-85% → amber  (medium)
                (0.85, 1.0,  "#ED1C24"),  # 85-100%→ red    (high)
            ]
            for (lo, hi, c) in zone_boundaries:
                if hi <= lo:
                    continue
                start_deg = 180 - lo * 180
                end_deg   = 180 - hi * 180
                ax.add_patch(plt.matplotlib.patches.Wedge(
                    (0.5, 0.0), 0.45, end_deg, start_deg,
                    width=0.09, facecolor=c, edgecolor="none", alpha=0.9,
                ))

            # ── Tick marks at 5/10/15/20/25/30% PD (on the arc) ─────────────
            for tick in (5, 10, 15, 20, 25, 30):
                t_pct = tick / scale_max_pct
                ang = np.deg2rad(180 - t_pct * 180)
                x0, y0 = 0.5 + 0.40 * np.cos(ang), 0.40 * np.sin(ang)
                x1, y1 = 0.5 + 0.50 * np.cos(ang), 0.50 * np.sin(ang)
                ax.plot([x0, x1], [y0, y1], color="#0F0F0F", lw=1.2)
                # Tick label sits INSIDE the arc, near the inner edge
                lx, ly = 0.5 + 0.30 * np.cos(ang), 0.30 * np.sin(ang)
                ax.text(lx, ly, f"{tick}", ha="center", va="center",
                        fontsize=8, color="#0F0F0F", fontweight="bold")

            # ── Threshold marker (small triangle + label OUTSIDE the arc) ───
            thr_pct = thr * 100
            if thr_pct <= scale_max_pct:
                thr_ang = np.deg2rad(180 - (thr_pct / scale_max_pct) * 180)
                tx = 0.5 + 0.55 * np.cos(thr_ang)
                ty = 0.55 * np.sin(thr_ang)
                ax.plot([tx], [ty], marker="v", markersize=9,
                        color="#0F0F0F", markeredgecolor="#FFFFFF",
                        markeredgewidth=1.2, zorder=8)
                # Label box — pushes label slightly further out so it doesn't
                # overlap with the arc. Place on the OUTSIDE of the marker.
                label_ang = thr_ang
                lx = 0.5 + 0.62 * np.cos(label_ang)
                ly = 0.62 * np.sin(label_ang) + 0.02
                ha = "left" if np.cos(label_ang) >= 0 else "right"
                ax.text(lx, ly, f"τ={thr_pct:.1f}%",
                        ha=ha, va="bottom", fontsize=8,
                        color="#0F0F0F", fontweight="bold",
                        bbox=dict(boxstyle="round,pad=0.25",
                                  facecolor="#FFFFFF",
                                  edgecolor="#0F0F0F", lw=0.6))

            # ── Needle pointing at PD ──────────────────────────────────────
            arrow_ang = np.deg2rad(180 - scaled_pct / 100 * 180)
            ax_x = 0.5 + 0.45 * np.cos(arrow_ang)
            ax_y = 0.45 * np.sin(arrow_ang)
            ax.annotate(
                "", xy=(ax_x, ax_y), xytext=(0.5, 0.0),
                arrowprops=dict(arrowstyle="-|>", color="#0F0F0F", lw=2.4,
                                mutation_scale=20),
            )
            # Needle hub
            ax.add_patch(plt.Circle((0.5, 0.0), 0.03,
                                    facecolor="#0F0F0F",
                                    edgecolor="#FFFFFF", lw=1.4, zorder=10))

            # ── Big PD value in the MOUTH of the gauge (below the arc) ─────
            ax.text(0.5, -0.10, f"{pct:.2f}%", ha="center", va="center",
                    fontsize=28, fontweight="bold", color=color)
            ax.text(0.5, -0.20, "PROBABILITY  OF  DEFAULT",
                    ha="center", va="center",
                    fontsize=8, color="#6B6B6B", fontweight="bold")

            ax.set_xlim(-0.20, 1.20)
            ax.set_ylim(-0.32, 0.70)
            ax.set_aspect("equal")
            ax.axis("off")
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

            st.markdown(
                f"""
                <div style="font-size: 11px; color: #6B6B6B;">
                    Threshold: <code>{thr:.3f}</code> &nbsp;|&nbsp;
                    Model: <code>{result.get('model_name', 'LightGBM_calibrated')}</code>
                    &nbsp;|&nbsp; Raw prob: <code>{result.get('raw_prob', 0):.4f}</code>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.expander("ℹ️ Explanation"):
                st.markdown(
                    f"""
- **PD (Probability of Default)**: predicted default probability from the calibrated LightGBM (isotonic).
- **Score**: log(odds) converted to a FICO-like score (300–850).
- **Risk band**: classification based on Score.
- **Decision**: compare PD with threshold ({thr:.3f}).
  - `APPROVE` if PD < threshold, otherwise `REJECT`.
- **Pipeline mapping**: record (raw fields) 
  `ColumnTransformer.transform()` `LightGBM.predict()` 
  `IsotonicRegression.predict()` `pd_to_score()` `score_to_band()`.
"""
                )
    else:
        with right:
            st.markdown("### Prediction Result")
            st.info("Fill in the form on the left and click PREDICT.")


# 
# Page 4: HIỆU NĂNG
# 
def page_performance():
    st.title("Model Performance")
    try:
        info = get_model_info()
    except FileNotFoundError as e:
        st.error(str(e))
        return
    metrics = info.get("metrics", {})
    if not metrics:
        st.warning("metrics.json not found — run training first.")
        return

    # Model comparison table 
    st.markdown("### 1. Model Comparison")
    rows = []
    for name, m in metrics.items():
        if not isinstance(m, dict) or "auc" not in m:
            continue
        rows.append({
            "Model": name,
            "AUC": m.get("auc", m.get("valid_auc", 0)),
            "KS": m.get("ks", m.get("valid_ks", 0)),
            "Brier": m.get("brier", m.get("valid_brier", 0)),
            "PR-AUC": m.get("pr_auc", m.get("valid_pr_auc", 0)),
            "Threshold": m.get("test_threshold", m.get("best_threshold", 0)),
            "Recall": m.get("test_recall", m.get("recall_at_best", 0)),
            "Precision": m.get("test_precision", m.get("precision_at_best", 0)),
        })
    df = pd.DataFrame(rows).sort_values("AUC", ascending=False)
    st.dataframe(
        df.style.format({
            "AUC": "{:.4f}", "KS": "{:.4f}", "Brier": "{:.4f}",
            "PR-AUC": "{:.4f}", "Threshold": "{:.3f}",
            "Recall": "{:.2%}", "Precision": "{:.2%}",
        }).background_gradient(subset=["AUC", "KS", "PR-AUC"], cmap="RdYlGn"),
        use_container_width=True,
    )

    # ROC / PR / KS / Calibration plots 
    st.markdown("### 2. ROC / PR / KS / Calibration")
    images = [
        ("ROC Curve", config.ROC_PNG,
         "Higher AUC is better — the curve should bow towards the top-left corner."),
        ("PR Curve", config.MODEL_DIR / "pr_curve.png",
         "Precision-Recall: trade-off between precision and recall."),
        ("KS Plot", config.MODEL_DIR / "ks_plot.png",
         "KS = max|TPR − FPR|. ≥ 0.3 is good, ≥ 0.4 is very good."),
        ("Calibration", config.CAL_PNG,
         "Predicted probabilities should sit close to the ideal y = x line."),
    ]
    cols = st.columns(2)
    for i, (title, path, desc) in enumerate(images):
        with cols[i % 2]:
            st.markdown(
                f"<b style='color:#0F0F0F;'>{title}</b><br>"
                f"<span style='font-size:11px;color:#6B6B6B;'>{desc}</span>",
                unsafe_allow_html=True,
            )
            if path.exists():
                st.image(str(path), use_container_width=True)
            else:
                st.warning(f"{path.name} not available yet")

    # Feature importance (matplotlib) 
    st.markdown("### 3. Top 20 Feature Importance")
    fi = load_feature_importance()
    if fi is not None and not fi.empty and "feature" in fi.columns and "importance" in fi.columns:
        top = fi.head(20).sort_values("importance", ascending=True)
        fig, ax = plt.subplots(figsize=(4.2, 2.5))
        ax.barh(top["feature"], top["importance"],
                color="#ED1C24", edgecolor="#0F0F0F", linewidth=0.6)
        ax.set_xlabel("Importance (gain)", fontsize=9)
        ax.tick_params(axis="both", labelsize=8)
        ax.set_title("LightGBM — Top 20 features", fontsize=10)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    else:
        st.info("No feature importance found in metrics.json.")

    # Score formula 
    st.markdown("### 4. Score Formula & Risk Bands")
    f = info["score_formula"]
    st.code(
        f"score = {f['offset']:.2f} - {f['factor']:.4f} * ln(PD / (1 - PD))\n"
        f"\n"
        f"base = {f['base']:.0f}\n"
        f"pdo = {f['pdo']:.0f} (points to double the odds)\n"
        f"odds_at_base = {f['odds_at_base']:.0f}\n"
        f"factor = {f['factor']:.4f}\n"
        f"offset = {f['offset']:.2f}",
        language="text",
    )
    st.markdown("**Risk bands:**")
    bands_df = pd.DataFrame([
        {"Band": k, "Score min": v[0], "Score max": v[1]}
        for k, v in info["risk_bands"].items()
    ])
    st.dataframe(bands_df, use_container_width=True, hide_index=True)


# 
# Main — use st.tabs with labels (no icons)
# 
def main():
    tab1, tab2, tab3, tab4 = st.tabs(
        ["OVERVIEW", "EDA", "PREDICT", "PERFORMANCE"]
    )
    with tab1:
        page_overview()
    with tab2:
        page_eda()
    with tab3:
        page_predict()
    with tab4:
        page_performance()


if __name__ == "__main__":
    main()
