"""Build a static HTML preview of the Home Credit dashboard layout.

Renders all 5 pages with Home Credit red/white theme + Segoe UI font.
Uses the actual data from ``powerbi/data/`` to populate KPIs and charts
(via vanilla SVG + Plotly fallback to inline JS).

Open the resulting file in any browser to preview the dashboard before
opening Power BI Desktop.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "powerbi" / "data"
OUT = ROOT / "powerbi" / "preview.html"

HC_RED = "#ED1C24"
HC_RED_DARK = "#B11226"
HC_RED_LIGHT = "#FFF5F5"
HC_GRAY = "#6B6B6B"
HC_DARK = "#1A1A1A"
HC_WHITE = "#FFFFFF"
HC_GREEN = "#3FAE5C"
HC_ORANGE = "#F5A623"

pd.set_option("display.float_format", lambda x: f"{x:.4f}")


def kpi_card(title: str, value: str, color: str = HC_RED, sub: str = "") -> str:
    return f"""
    <div class="kpi">
      <div class="kpi-title">{title}</div>
      <div class="kpi-value" style="color:{color}">{value}</div>
      <div class="kpi-sub">{sub}</div>
    </div>
    """


def header(page_num: int, page_name: str, sub: str) -> str:
    return f"""
    <div class="page-header">
      <div class="logo">
        <div class="logo-circle">H</div>
        <div class="logo-text">
          <div class="logo-text-top">HOME</div>
          <div class="logo-text-bot" style="color:{HC_RED}">CREDIT</div>
        </div>
      </div>
      <div class="page-title">
        <div class="page-num">{page_num:02d}</div>
        <div class="page-name">{page_name}</div>
        <div class="page-sub">{sub}</div>
      </div>
      <div class="page-meta">
        <div class="meta-line">DATA · TEST SET</div>
        <div class="meta-line">7,500 customers</div>
        <div class="meta-line">LightGBM Calibrated</div>
      </div>
    </div>
    """


# ----------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------

def load_data() -> dict:
    pred = pd.read_csv(DATA_DIR / "fact_predictions.csv")
    models = pd.read_csv(DATA_DIR / "dim_models.csv")
    fi = pd.read_csv(DATA_DIR / "fact_feature_importance.csv")
    rb = pd.read_csv(DATA_DIR / "dim_risk_bands.csv")
    return {"pred": pred, "models": models, "fi": fi, "rb": rb}


# ----------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------

def page_exec(d: dict) -> str:
    p = d["pred"]
    total = len(p)
    default_rate = (p["actual_default"].sum() / total) * 100
    avg_pd = p["pd_calibrated"].mean() * 100
    auc = d["models"]["auc"].max()
    avg_score = int(p["score"].mean())
    band_counts = p["risk_band"].value_counts()

    # Donut
    donut = f"""
    <div class="chart-block">
      <div class="chart-title">RISK BAND DISTRIBUTION</div>
      <svg viewBox="0 0 200 200" class="donut">
        {donut_svg(band_counts, total)}
      </svg>
      <div class="legend">
        <div class="leg"><span class="dot" style="background:{HC_RED}"></span>Cao · {band_counts.get('Cao', 0):,}</div>
        <div class="leg"><span class="dot" style="background:{HC_ORANGE}"></span>Trung bình · {band_counts.get('Trung bình', 0):,}</div>
        <div class="leg"><span class="dot" style="background:{HC_GREEN}"></span>Thấp · {band_counts.get('Thấp', 0):,}</div>
      </div>
    </div>
    """
    # Score histogram
    hist = f"""
    <div class="chart-block">
      <div class="chart-title">CREDIT SCORE DISTRIBUTION (300–850)</div>
      <svg viewBox="0 0 500 200" class="hist">
        {hist_svg(p["score"].values, HC_RED)}
      </svg>
    </div>
    """
    # Top 10 risk table
    top = p.nlargest(10, "pd_calibrated")[["customer_id", "score", "pd_calibrated", "risk_band", "actual_default"]]
    rows = ""
    for _, r in top.iterrows():
        color = {"Cao": HC_RED, "Trung bình": HC_ORANGE, "Thấp": HC_GREEN}[r["risk_band"]]
        rows += f"""
        <tr>
          <td>#{int(r['customer_id']):,}</td>
          <td><b>{int(r['score'])}</b></td>
          <td><div class="bar"><div class="bar-fill" style="width:{r['pd_calibrated']*100*5:.0f}%; background:{HC_RED}"></div><span>{r['pd_calibrated']*100:.1f}%</span></div></td>
          <td><span class="pill" style="background:{color}1A; color:{color}; border-color:{color}">{r['risk_band']}</span></td>
          <td>{'⚠ Vỡ nợ' if r['actual_default']==1 else '✓ Không'}</td>
        </tr>
        """
    table = f"""
    <div class="table-block">
      <div class="chart-title">TOP 10 HIGHEST-RISK CUSTOMERS</div>
      <table>
        <thead><tr><th>Customer</th><th>Score</th><th>PD</th><th>Risk</th><th>Actual</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """

    cards = "".join([
        kpi_card("TỔNG KHÁCH HÀNG",       f"{total:,}",                                 HC_DARK,  "Test set"),
        kpi_card("TỈ LỆ VỠ NỢ THỰC TẾ",    f"{default_rate:.2f}%",                        HC_RED,   "Calibrated target"),
        kpi_card("PD TRUNG BÌNH",          f"{avg_pd:.2f}%",                              HC_ORANGE,"Calibrated"),
        kpi_card("AUC (MÔ HÌNH TỐT NHẤT)", f"{auc:.4f}",                                  HC_GREEN, "LightGBM (cal)"),
        kpi_card("ĐIỂM TÍN DỤNG TB",      f"{avg_score}",                                HC_DARK,  "FICO-style 300-850"),
    ])

    return f"""
    <section class="page">
      {header(1, "EXECUTIVE SUMMARY", "Tổng quan rủi ro tín dụng")}
      <div class="kpi-row">{cards}</div>
      <div class="chart-row">{donut}{hist}</div>
      {table}
    </section>
    """


def donut_svg(counts: pd.Series, total: int) -> str:
    colors = {"Cao": HC_RED, "Trung bình": HC_ORANGE, "Thấp": HC_GREEN}
    order = ["Cao", "Trung bình", "Thấp"]
    cx, cy, r_o, r_i = 100, 100, 80, 50
    angle = -90
    parts = []
    for k in order:
        v = counts.get(k, 0)
        if v == 0:
            continue
        sweep = (v / total) * 360
        a1 = math.radians(angle)
        a2 = math.radians(angle + sweep)
        x1o, y1o = cx + r_o * math.cos(a1), cy + r_o * math.sin(a1)
        x2o, y2o = cx + r_o * math.cos(a2), cy + r_o * math.sin(a2)
        x1i, y1i = cx + r_i * math.cos(a1), cy + r_i * math.sin(a1)
        x2i, y2i = cx + r_i * math.cos(a2), cy + r_i * math.sin(a2)
        large = 1 if sweep > 180 else 0
        d = (
            f"M {x1o:.1f} {y1o:.1f} "
            f"A {r_o} {r_o} 0 {large} 1 {x2o:.1f} {y2o:.1f} "
            f"L {x2i:.1f} {y2i:.1f} "
            f"A {r_i} {r_i} 0 {large} 0 {x1i:.1f} {y1i:.1f} Z"
        )
        parts.append(f'<path d="{d}" fill="{colors[k]}" />')
        # Label
        a_mid = math.radians(angle + sweep / 2)
        lx, ly = cx + (r_o + 12) * math.cos(a_mid), cy + (r_o + 12) * math.sin(a_mid)
        parts.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="9" fill="#1A1A1A" text-anchor="middle">'
            f'{v / total * 100:.1f}%</text>'
        )
        angle += sweep
    return "\n".join(parts)


def hist_svg(values, color: str) -> str:
    import numpy as np
    bins = np.linspace(300, 850, 12)
    hist, edges = np.histogram(values, bins=bins)
    max_h = hist.max() if hist.max() > 0 else 1
    bw = 480 / len(hist)
    parts = []
    for i, h in enumerate(hist):
        x = 10 + i * bw + 4
        bh = (h / max_h) * 150
        y = 170 - bh
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw-4:.1f}" height="{bh:.1f}" '
            f'fill="{color}" opacity="{0.4 + 0.6 * h/max_h:.2f}" />'
        )
        parts.append(
            f'<text x="{x + (bw-4)/2:.1f}" y="190" font-size="9" fill="#6B6B6B" text-anchor="middle">'
            f'{int(edges[i])}</text>'
        )
    parts.append(
        f'<line x1="10" y1="170" x2="490" y2="170" stroke="#1A1A1A" stroke-width="1" />'
    )
    return "\n".join(parts)


def page_perf(d: dict) -> str:
    m = d["models"]
    best = m.iloc[0]
    cards = "".join([
        kpi_card("AUC (BEST)",  f"{m['auc'].max():.4f}",  HC_GREEN, f"Model: {best['model_name']}"),
        kpi_card("GINI (BEST)", f"{m['gini'].max():.4f}", HC_GREEN),
        kpi_card("KS (BEST)",   f"{m['ks'].max():.4f}",   HC_GREEN),
        kpi_card("BRIER (MIN)", f"{m['brier'].min():.4f}",HC_GREEN),
        kpi_card("F1 SCORE",    f"{best['f1']:.4f}",      HC_DARK,  f"@ threshold {best['threshold']}"),
    ])

    rows = ""
    for _, r in m.iterrows():
        is_rec = "★" if r["is_recommended"] else ""
        bg = HC_RED_LIGHT if r["is_recommended"] else "transparent"
        rows += f"""
        <tr style="background:{bg}">
          <td><b>{r['model_name']}</b> {is_rec}</td>
          <td><div class="bar"><div class="bar-fill" style="width:{r['auc']*100:.0f}%; background:{HC_GREEN}"></div><span>{r['auc']:.4f}</span></div></td>
          <td>{r['gini']:.4f}</td>
          <td>{r['ks']:.4f}</td>
          <td>{r['brier']:.4f}</td>
          <td>{r['pr_auc']:.4f}</td>
          <td>{r['f1']:.4f}</td>
          <td>{r['recall']*100:.1f}%</td>
          <td>{r['precision']*100:.1f}%</td>
        </tr>
        """
    table = f"""
    <div class="table-block">
      <div class="chart-title">MODEL COMPARISON (sorted by AUC) · ★ = recommended</div>
      <table>
        <thead><tr><th>Model</th><th>AUC</th><th>Gini</th><th>KS</th><th>Brier</th><th>PR-AUC</th><th>F1</th><th>Recall</th><th>Precision</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """
    bar = f"""
    <div class="chart-block">
      <div class="chart-title">AUC COMPARISON</div>
      <svg viewBox="0 0 400 200" class="hist">
        {auc_bar_svg(m)}
      </svg>
    </div>
    """
    cm = f"""
    <div class="chart-block">
      <div class="chart-title">CONFUSION MATRIX @ threshold={best['threshold']}</div>
      {cm_table(d)}
    </div>
    """
    return f"""
    <section class="page">
      {header(2, "MODEL PERFORMANCE", "So sánh 4 mô hình, calibration, KS")}
      <div class="kpi-row">{cards}</div>
      <div class="chart-row">{bar}{cm}</div>
      {table}
    </section>
    """


def auc_bar_svg(m: pd.DataFrame) -> str:
    max_v = m["auc"].max()
    parts = []
    for i, (_, r) in enumerate(m.iterrows()):
        y = 15 + i * 35
        w = (r["auc"] / 0.85) * 280
        color = HC_RED if r["is_recommended"] else HC_DARK
        parts.append(
            f'<text x="0" y="{y+15}" font-size="10" fill="#1A1A1A">{r["model_name"][:18]}</text>'
        )
        parts.append(
            f'<rect x="150" y="{y}" width="{w:.0f}" height="22" fill="{color}" />'
        )
        parts.append(
            f'<text x="{155+w:.0f}" y="{y+15}" font-size="10" fill="#1A1A1A"><b>{r["auc"]:.4f}</b></text>'
        )
    return "\n".join(parts)


def cm_table(d: dict) -> str:
    p = d["pred"]
    tp = ((p.actual_default == 1) & (p.predicted_default == 1)).sum()
    fp = ((p.actual_default == 0) & (p.predicted_default == 1)).sum()
    fn = ((p.actual_default == 1) & (p.predicted_default == 0)).sum()
    tn = ((p.actual_default == 0) & (p.predicted_default == 0)).sum()
    return f"""
    <table class="cm">
      <thead><tr><th></th><th>Pred = 0</th><th>Pred = 1</th><th>Total</th></tr></thead>
      <tbody>
        <tr><th>Actual = 0</th>
          <td class="tn">{tn:,}</td>
          <td class="fp">{fp:,}</td>
          <td>{tn+fp:,}</td></tr>
        <tr><th>Actual = 1</th>
          <td class="fn">{fn:,}</td>
          <td class="tp">{tp:,}</td>
          <td>{fn+tp:,}</td></tr>
        <tr><th>Total</th>
          <td>{tn+fn:,}</td>
          <td>{fp+tp:,}</td>
          <td><b>{tn+fp+fn+tp:,}</b></td></tr>
      </tbody>
    </table>
    """


def page_segment(d: dict) -> str:
    p = d["pred"]
    high = (p["risk_band"] == "Cao").sum()
    med = (p["risk_band"] == "Trung bình").sum()
    low = (p["risk_band"] == "Thấp").sum()
    total = len(p)
    high_pct = high / total * 100
    cards = "".join([
        kpi_card("KHÁCH HÀNG RỦI RO CAO", f"{high:,}", HC_RED,   f"{high_pct:.1f}%"),
        kpi_card("RỦI RO TRUNG BÌNH",     f"{med:,}",  HC_ORANGE, f"{med/total*100:.1f}%"),
        kpi_card("RỦI RO THẤP",           f"{low:,}",  HC_GREEN,  f"{low/total*100:.1f}%"),
        kpi_card("TỈ TRỌNG HIGH RISK",    f"{high_pct:.1f}%", HC_RED, "Share of portfolio"),
    ])

    bar = f"""
    <div class="chart-block">
      <div class="chart-title">RISK BAND DISTRIBUTION</div>
      <svg viewBox="0 0 500 200" class="hist">
        {rb_bar_svg(high, med, low)}
      </svg>
    </div>
    """
    # Bad rate by band
    bad_rates = p.groupby("risk_band")["actual_default"].mean() * 100
    bad_rates = bad_rates.reindex(["Cao", "Trung bình", "Thấp"]).fillna(0)
    br = f"""
    <div class="chart-block">
      <div class="chart-title">ACTUAL BAD RATE BY RISK BAND</div>
      <svg viewBox="0 0 400 200" class="hist">
        {bad_rate_svg(bad_rates.values)}
      </svg>
    </div>
    """
    return f"""
    <section class="page">
      {header(3, "RISK SEGMENTATION", "Phân khúc rủi ro · Bad rate · Distribution")}
      <div class="kpi-row">{cards}</div>
      <div class="chart-row">{bar}{br}</div>
    </section>
    """


def rb_bar_svg(high: int, med: int, low: int) -> str:
    total = high + med + low
    bw = 80
    parts = []
    for i, (v, c, lbl) in enumerate([(high, HC_RED, "Cao"), (med, HC_ORANGE, "Trung bình"), (low, HC_GREEN, "Thấp")]):
        x = 60 + i * 130
        bh = (v / total) * 160
        y = 170 - bh
        parts.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" fill="{c}" />')
        parts.append(f'<text x="{x + bw/2}" y="{y - 6}" font-size="14" font-weight="bold" fill="#1A1A1A" text-anchor="middle">{v:,}</text>')
        parts.append(f'<text x="{x + bw/2}" y="190" font-size="10" fill="#1A1A1A" text-anchor="middle">{lbl}</text>')
        parts.append(f'<text x="{x + bw/2}" y="205" font-size="9" fill="#6B6B6B" text-anchor="middle">{v/total*100:.1f}%</text>')
    return "\n".join(parts)


def bad_rate_svg(values) -> str:
    parts = []
    colors = [HC_RED, HC_ORANGE, HC_GREEN]
    for i, (v, c, lbl) in enumerate(zip(values, colors, ["Cao", "Trung bình", "Thấp"])):
        x = 50 + i * 110
        bh = (v / 20) * 150
        y = 170 - bh
        parts.append(f'<rect x="{x}" y="{y}" width="80" height="{bh:.0f}" fill="{c}" />')
        parts.append(f'<text x="{x+40}" y="{y-6}" font-size="13" font-weight="bold" fill="#1A1A1A" text-anchor="middle">{v:.2f}%</text>')
        parts.append(f'<text x="{x+40}" y="190" font-size="10" fill="#1A1A1A" text-anchor="middle">{lbl}</text>')
    return "\n".join(parts)


def page_feat(d: dict) -> str:
    fi = d["fi"].head(20)
    n = len(d["fi"])
    top1 = fi.iloc[0]["feature_short"] if n else "n/a"
    cards = "".join([
        kpi_card("SỐ FEATURES",   f"{n}",     HC_DARK, "Total engineered"),
        kpi_card("TOP 1 FEATURE", f"{top1}",  HC_RED,  "Highest importance"),
    ])
    bar = f"""
    <div class="chart-block" style="grid-column: span 2;">
      <div class="chart-title">TOP 20 FEATURES (by LightGBM gain)</div>
      <svg viewBox="0 0 800 480" class="hist">
        {feat_bar_svg(fi)}
      </svg>
    </div>
    """
    return f"""
    <section class="page">
      {header(4, "FEATURE IMPORTANCE", "SHAP & gain — Top features driving PD")}
      <div class="kpi-row">{cards}</div>
      <div class="chart-row">{bar}</div>
    </section>
    """


def feat_bar_svg(fi: pd.DataFrame) -> str:
    max_v = fi["importance"].max()
    parts = []
    for i, (_, r) in enumerate(fi.iterrows()):
        y = 15 + i * 22
        w = (r["importance"] / max_v) * 480
        parts.append(f'<text x="0" y="{y+12}" font-size="9" fill="#1A1A1A">{r["feature_short"][:32]}</text>')
        parts.append(f'<rect x="240" y="{y}" width="{w:.0f}" height="16" fill="{HC_RED}" />')
        parts.append(f'<text x="{245+w:.0f}" y="{y+12}" font-size="9" fill="#1A1A1A"><b>{r["importance"]}</b></text>')
    return "\n".join(parts)


def page_port(d: dict) -> str:
    p = d["pred"]
    total = len(p)
    el_rate = p["pd_calibrated"].mean() * 100
    tp = ((p.actual_default == 1) & (p.predicted_default == 1)).sum()
    fp = ((p.actual_default == 0) & (p.predicted_default == 1)).sum()
    fn = ((p.actual_default == 1) & (p.predicted_default == 0)).sum()
    tn = ((p.actual_default == 0) & (p.predicted_default == 0)).sum()
    acc = (tp + tn) / total * 100
    recall = tp / (tp + fn) * 100 if (tp + fn) else 0
    prec = tp / (tp + fp) * 100 if (tp + fp) else 0
    cards = "".join([
        kpi_card("TỔNG",          f"{total:,}",          HC_DARK),
        kpi_card("EXPECTED LOSS", f"{el_rate:.2f}%",     HC_RED,  "Sum PD / N"),
        kpi_card("ACCURACY",      f"{acc:.2f}%",         HC_DARK),
        kpi_card("RECALL",        f"{recall:.2f}%",      HC_ORANGE,"Sensitivity"),
        kpi_card("PRECISION",     f"{prec:.2f}%",        HC_GREEN),
    ])
    hist = f"""
    <div class="chart-block">
      <div class="chart-title">PD DISTRIBUTION</div>
      <svg viewBox="0 0 500 200" class="hist">
        {pd_hist_svg(p["pd_calibrated"].values)}
      </svg>
    </div>
    """
    sample = p.head(15)[["customer_id", "score", "pd_calibrated", "risk_band", "actual_default"]]
    rows = ""
    for _, r in sample.iterrows():
        color = {"Cao": HC_RED, "Trung bình": HC_ORANGE, "Thấp": HC_GREEN}[r["risk_band"]]
        rows += f"""
        <tr>
          <td>#{int(r['customer_id']):,}</td>
          <td><b>{int(r['score'])}</b></td>
          <td>{r['pd_calibrated']*100:.2f}%</td>
          <td><span class="pill" style="background:{color}1A; color:{color}; border-color:{color}">{r['risk_band']}</span></td>
          <td>{'⚠' if r['actual_default']==1 else '✓'}</td>
        </tr>
        """
    table = f"""
    <div class="table-block">
      <div class="chart-title">CUSTOMER SAMPLE (first 15) · Use slicers to filter</div>
      <table>
        <thead><tr><th>Customer</th><th>Score</th><th>PD</th><th>Risk</th><th>Actual</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """
    return f"""
    <section class="page">
      {header(5, "PORTFOLIO DRILL-DOWN", "Customer-level · PD distribution · Drill-through")}
      <div class="kpi-row">{cards}</div>
      <div class="chart-row">{hist}{table}</div>
    </section>
    """


def pd_hist_svg(values) -> str:
    import numpy as np
    bins = np.linspace(0, 0.5, 11)
    hist, edges = np.histogram(values, bins=bins)
    max_h = hist.max() if hist.max() > 0 else 1
    bw = 480 / len(hist)
    parts = []
    for i, h in enumerate(hist):
        x = 10 + i * bw + 2
        bh = (h / max_h) * 150
        y = 170 - bh
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw-3:.1f}" height="{bh:.1f}" '
            f'fill="{HC_RED}" opacity="{0.3 + 0.7 * h/max_h:.2f}" />'
        )
        parts.append(
            f'<text x="{x + (bw-3)/2:.1f}" y="190" font-size="8" fill="#6B6B6B" text-anchor="middle">'
            f'{edges[i]*100:.0f}%</text>'
        )
    parts.append('<line x1="10" y1="170" x2="490" y2="170" stroke="#1A1A1A" stroke-width="1" />')
    return "\n".join(parts)


# ----------------------------------------------------------------------
# HTML
# ----------------------------------------------------------------------

HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8" />
<title>Home Credit Default Risk — Dashboard Preview</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {{
    font-family: 'Segoe UI', 'Inter', system-ui, -apple-system, sans-serif;
    background: #F0F2F5;
    color: #1A1A1A;
    padding: 24px;
    line-height: 1.4;
  }}
  h1 {{
    text-align: center;
    font-size: 22px;
    margin-bottom: 8px;
    color: #1A1A1A;
  }}
  .subtitle {{
    text-align: center;
    color: #6B6B6B;
    margin-bottom: 24px;
    font-size: 12px;
  }}
  .page {{
    background: #FFFFFF;
    border: 1px solid #E5E5E5;
    border-radius: 8px;
    padding: 24px;
    margin-bottom: 32px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  }}
  .page-header {{
    display: flex;
    align-items: center;
    padding-bottom: 16px;
    border-bottom: 2px solid #ED1C24;
    margin-bottom: 20px;
  }}
  .logo {{ display: flex; align-items: center; gap: 8px; }}
  .logo-circle {{
    width: 40px; height: 40px; border-radius: 50%;
    background: #ED1C24; color: #FFFFFF;
    display: flex; align-items: center; justify-content: center;
    font-weight: bold; font-size: 20px;
  }}
  .logo-text-top, .logo-text-bot {{
    font-weight: 800; font-size: 14px; line-height: 1;
  }}
  .page-title {{ flex: 1; margin-left: 24px; }}
  .page-num {{
    color: #ED1C24; font-weight: 800; font-size: 22px;
  }}
  .page-name {{
    font-size: 18px; font-weight: 700; color: #1A1A1A;
    margin-top: 2px;
  }}
  .page-sub {{ color: #6B6B6B; font-size: 11px; margin-top: 2px; }}
  .page-meta {{
    text-align: right; font-size: 10px; color: #6B6B6B;
  }}
  .meta-line {{ line-height: 1.5; }}
  .kpi-row {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    margin-bottom: 20px;
  }}
  .kpi {{
    background: #FFFFFF;
    border: 2px solid #ED1C24;
    border-radius: 6px;
    padding: 14px;
    text-align: center;
  }}
  .kpi-title {{
    font-size: 9px; color: #6B6B6B; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.5px;
    margin-bottom: 6px;
  }}
  .kpi-value {{
    font-size: 24px; font-weight: 300; line-height: 1.1;
  }}
  .kpi-sub {{
    font-size: 9px; color: #6B6B6B; margin-top: 4px;
  }}
  .chart-row {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 20px;
  }}
  .chart-block, .table-block {{
    background: #FAFAFA;
    border: 1px solid #E5E5E5;
    border-radius: 6px;
    padding: 12px;
  }}
  .chart-title {{
    font-size: 10px; font-weight: 700; color: #1A1A1A;
    text-transform: uppercase; letter-spacing: 0.5px;
    margin-bottom: 10px;
    border-left: 3px solid #ED1C24;
    padding-left: 8px;
  }}
  .donut {{ width: 100%; max-width: 180px; margin: 0 auto; display: block; }}
  .hist {{ width: 100%; height: 180px; display: block; }}
  .legend {{ display: flex; gap: 12px; justify-content: center; margin-top: 8px; font-size: 11px; }}
  .leg {{ display: flex; align-items: center; gap: 4px; }}
  .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
  thead {{ background: #ED1C24; color: #FFFFFF; }}
  th {{ padding: 6px 8px; text-align: left; font-weight: 600; font-size: 10px; text-transform: uppercase; }}
  td {{ padding: 6px 8px; border-bottom: 1px solid #F0F0F0; }}
  tbody tr:nth-child(even) {{ background: #FAFAFA; }}
  tbody tr:hover {{ background: #FFF5F5; }}
  .bar {{
    display: flex; align-items: center; gap: 6px;
    background: #F0F0F0; border-radius: 3px; height: 16px;
    position: relative; min-width: 80px;
  }}
  .bar-fill {{ height: 100%; border-radius: 3px; }}
  .bar span {{
    position: absolute; right: 4px; font-size: 9px; font-weight: 600;
  }}
  .pill {{
    display: inline-block; padding: 2px 8px; border-radius: 10px;
    font-size: 9px; font-weight: 600; border: 1px solid;
  }}
  .cm th, .cm td {{ text-align: center; }}
  .cm .tn {{ background: #3FAE5C22; }}
  .cm .tp {{ background: #3FAE5C44; font-weight: 700; color: #1A1A1A; }}
  .cm .fp {{ background: #F5A62333; }}
  .cm .fn {{ background: #ED1C2422; font-weight: 700; }}
  footer {{
    text-align: center; color: #6B6B6B; font-size: 11px;
    margin-top: 24px; padding-top: 16px; border-top: 1px solid #E5E5E5;
  }}
</style>
</head>
<body>
<h1>HOME CREDIT DEFAULT RISK · DASHBOARD PREVIEW</h1>
<div class="subtitle">5 pages · Home Credit palette · Power BI ready</div>
{PAGES}
<footer>
  Generated from model/metrics.json + model/predictions_test.csv ·
  Run <code>python powerbi/export_powerbi_data.py</code> to refresh ·
  Open <code>powerbi/HomeCreditRiskDashboard.pbit</code> in Power BI Desktop
</footer>
</body>
</html>
"""


import math  # for SVG math


def main() -> None:
    d = load_data()
    pages = "\n".join([
        page_exec(d),
        page_perf(d),
        page_segment(d),
        page_feat(d),
        page_port(d),
    ])
    html = HTML.replace("{PAGES}", pages)
    OUT.write_text(html, encoding="utf-8")
    print(f"[OK] {OUT}  ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
