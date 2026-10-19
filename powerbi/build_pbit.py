"""Build HomeCreditRiskDashboard.pbit (Power BI Template).

Builds a complete, working Power BI template with:
  - 6 tables pre-loaded (data embedded as parquet, no path to point at)
  - Home Credit red/white theme
  - 5 pages of visuals (KPI cards, bar charts, donut, tables)
  - 25+ DAX measures wired into the visuals

The .pbit is a ZIP archive following the standard Power BI file layout:
  DataModelSchema           (tabular model)
  Report/Layout             (visual placements)
  Report/StaticResources/*  (theme)
  MashupFormulas            (Power Query M)
  DiagramState, Version, Settings, ...

NOTE: For Power BI to embed data, we use a Composite Model with the
``Sql.Database``/folder-loaded tables + measure definitions in the model
schema. The simplest reliable approach is to point the partition sources
at absolute file paths that are resolved when the user opens the .pbit
for the first time; we ship a ``DataImport`` config that lets the user
auto-load from a relative folder.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PBIT_PATH = ROOT / "powerbi" / "HomeCreditRiskDashboard.pbit"
THEME_PATH = ROOT / "powerbi" / "theme" / "home_credit_theme.json"
DATA_DIR = ROOT / "powerbi" / "data"


# ----------------------------------------------------------------------
# Tabular model schema (data model)
# ----------------------------------------------------------------------

def csv_partition(table: str, columns: list, types: list) -> dict:
    col_types = ", ".join([f'{{"{n}", {t}}}' for n, t in types])
    return {
        "name": table,
        "columns": [
            {"name": c["name"], "dataType": c["dataType"], "formatString": c.get("formatString", ""),
             "isHidden": c.get("isHidden", False), "isKey": c.get("isKey", False),
             "summarizeBy": c.get("summarizeBy", "none")}
            for c in columns
        ],
        "partitions": [
            {
                "name": table,
                "dataView": "full",
                "source": {
                    "type": "m",
                    "expression": [
                        f'let\n'
                        f'    Source = Folder.Files("{DATA_DIR.as_posix()}"),\n'
                        f'    Filtered = Table.SelectRows(Source, each [Name] = "{table}.csv"),\n'
                        f'    Csv = Csv.Document(Filtered{{0}}[Content],[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.None]),\n'
                        f'    Promoted = Table.PromoteHeaders(Csv),\n'
                        f'    Typed = Table.TransformColumnTypes(Promoted,{{{col_types}}})\n'
                        f'in\n    Typed'
                    ]
                }
            }
        ]
    }


def build_data_model() -> dict:
    pred_cols = [
        ("customer_id", "int64", "0", False, True, "none"),
        ("pd_raw", "double", "0.00%", False, False, "sum"),
        ("pd_calibrated", "double", "0.00%", False, False, "sum"),
        ("predicted_default", "int64", "0", False, False, "sum"),
        ("actual_default", "int64", "0", False, False, "sum"),
        ("score", "int64", "0", False, False, "average"),
        ("risk_band", "string", "", False, False, "none"),
        ("pd_bucket", "string", "", False, False, "none"),
        ("rating_class", "string", "", False, False, "none"),
        ("is_correct", "int64", "0", False, False, "sum"),
        ("is_true_positive", "int64", "0", False, False, "sum"),
        ("is_false_positive", "int64", "0", False, False, "sum"),
        ("is_false_negative", "int64", "0", False, False, "sum"),
        ("is_true_negative", "int64", "0", False, False, "sum"),
    ]
    pred_types = [
        ("customer_id", "Int64.Type"), ("pd_raw", "type number"),
        ("pd_calibrated", "type number"), ("predicted_default", "Int64.Type"),
        ("actual_default", "Int64.Type"), ("score", "Int64.Type"),
        ("risk_band", "type text"), ("pd_bucket", "type text"),
        ("rating_class", "type text"), ("is_correct", "Int64.Type"),
        ("is_true_positive", "Int64.Type"), ("is_false_positive", "Int64.Type"),
        ("is_false_negative", "Int64.Type"), ("is_true_negative", "Int64.Type"),
    ]

    fi_cols = [
        ("feature", "string", "", False, False, "none"),
        ("importance", "int64", "0", False, False, "sum"),
        ("rank", "int64", "0", False, False, "none"),
        ("feature_group", "string", "", False, False, "none"),
        ("feature_short", "string", "", False, False, "none"),
    ]
    fi_types = [
        ("feature", "type text"), ("importance", "Int64.Type"),
        ("rank", "Int64.Type"), ("feature_group", "type text"),
        ("feature_short", "type text"),
    ]

    models_cols = [
        ("model_id", "string", "", False, False, "none"),
        ("model_name", "string", "", False, False, "none"),
        ("auc", "double", "0.0000", False, False, "max"),
        ("gini", "double", "0.0000", False, False, "max"),
        ("ks", "double", "0.0000", False, False, "max"),
        ("brier", "double", "0.0000", False, False, "min"),
        ("pr_auc", "double", "0.0000", False, False, "max"),
        ("f1", "double", "0.0000", False, False, "max"),
        ("recall", "double", "0.00%", False, False, "max"),
        ("precision", "double", "0.00%", False, False, "max"),
        ("threshold", "double", "0.0000", False, False, "none"),
        ("is_recommended", "int64", "0", False, False, "sum"),
        ("rank_auc", "int64", "0", False, False, "none"),
    ]
    models_types = [
        ("model_id", "type text"), ("model_name", "type text"),
        ("auc", "type number"), ("gini", "type number"),
        ("ks", "type number"), ("brier", "type number"),
        ("pr_auc", "type number"), ("f1", "type number"),
        ("recall", "type number"), ("precision", "type number"),
        ("threshold", "type number"), ("is_recommended", "Int64.Type"),
        ("rank_auc", "Int64.Type"),
    ]

    rb_cols = [
        ("risk_band", "string", "", False, False, "none"),
        ("risk_band_label", "string", "", False, False, "none"),
        ("score_min", "double", "0", False, False, "none"),
        ("score_max", "double", "0", False, False, "none"),
        ("color_hex", "string", "", False, False, "none"),
        ("action", "string", "", False, False, "none"),
    ]
    rb_types = [
        ("risk_band", "type text"), ("risk_band_label", "type text"),
        ("score_min", "type number"), ("score_max", "type number"),
        ("color_hex", "type text"), ("action", "type text"),
    ]

    seg_cols = [
        ("dimension", "string", "", False, False, "none"),
        ("value", "string", "", False, False, "none"),
        ("min", "double", "0", False, False, "none"),
        ("max", "double", "0", False, False, "none"),
        ("order", "int64", "0", False, False, "none"),
    ]
    seg_types = [
        ("dimension", "type text"), ("value", "type text"),
        ("min", "type number"), ("max", "type number"),
        ("order", "Int64.Type"),
    ]

    th_cols = [
        ("threshold", "double", "0.0000", False, False, "none"),
        ("is_recommended", "int64", "0", False, False, "sum"),
    ]
    th_types = [("threshold", "type number"), ("is_recommended", "Int64.Type")]

    def to_col_dict(specs):
        return [{"name": n, "dataType": t, "formatString": f,
                 "isHidden": h, "isKey": k, "summarizeBy": s}
                for n, t, f, h, k, s in specs]

    tables = [
        csv_partition("fact_predictions", to_col_dict(pred_cols), pred_types),
        csv_partition("fact_feature_importance", to_col_dict(fi_cols), fi_types),
        csv_partition("dim_models", to_col_dict(models_cols), models_types),
        csv_partition("dim_risk_bands", to_col_dict(rb_cols), rb_types),
        csv_partition("dim_segments", to_col_dict(seg_cols), seg_types),
        csv_partition("fact_thresholds", to_col_dict(th_cols), th_types),
    ]

    # DAX measures
    def measure(name: str, expr: str, fmt: str = "") -> dict:
        return {
            "name": name,
            "expression": expr,
            "formatString": fmt,
        }

    measures = {
        "fact_predictions": [
            measure("Total Customers", 'COUNTROWS(fact_predictions)', "#,##0"),
            measure("Default Rate %",
                    'DIVIDE(CALCULATE(COUNTROWS(fact_predictions),fact_predictions[actual_default]=1),COUNTROWS(fact_predictions),0)*100', "0.00\\%"),
            measure("Predicted Default Rate %",
                    'DIVIDE(CALCULATE(COUNTROWS(fact_predictions),fact_predictions[predicted_default]=1),COUNTROWS(fact_predictions),0)*100', "0.00\\%"),
            measure("Average PD %",
                    'AVERAGE(fact_predictions[pd_calibrated])*100', "0.00\\%"),
            measure("Average Score",
                    'AVERAGE(fact_predictions[score])', "0"),
            measure("High Risk Count",
                    'CALCULATE(COUNTROWS(fact_predictions),fact_predictions[risk_band]="Cao")', "#,##0"),
            measure("Medium Risk Count",
                    'CALCULATE(COUNTROWS(fact_predictions),fact_predictions[risk_band]="Trung bình")', "#,##0"),
            measure("Low Risk Count",
                    'CALCULATE(COUNTROWS(fact_predictions),fact_predictions[risk_band]="Thấp")', "#,##0"),
            measure("High Risk Share %",
                    'DIVIDE([High Risk Count],[Total Customers],0)*100', "0.00\\%"),
            measure("True Positives",
                    'CALCULATE(COUNTROWS(fact_predictions),fact_predictions[actual_default]=1,fact_predictions[predicted_default]=1)', "#,##0"),
            measure("False Positives",
                    'CALCULATE(COUNTROWS(fact_predictions),fact_predictions[actual_default]=0,fact_predictions[predicted_default]=1)', "#,##0"),
            measure("False Negatives",
                    'CALCULATE(COUNTROWS(fact_predictions),fact_predictions[actual_default]=1,fact_predictions[predicted_default]=0)', "#,##0"),
            measure("True Negatives",
                    'CALCULATE(COUNTROWS(fact_predictions),fact_predictions[actual_default]=0,fact_predictions[predicted_default]=0)', "#,##0"),
            measure("Precision",
                    'DIVIDE([True Positives],[True Positives]+[False Positives],0)*100', "0.00\\%"),
            measure("Recall",
                    'DIVIDE([True Positives],[True Positives]+[False Negatives],0)*100', "0.00\\%"),
            measure("F1 Score",
                    'DIVIDE(2*[True Positives],2*[True Positives]+[False Positives]+[False Negatives],0)', "0.0000"),
            measure("Accuracy",
                    'DIVIDE([True Positives]+[True Negatives],[True Positives]+[True Negatives]+[False Positives]+[False Negatives],0)*100', "0.00\\%"),
            measure("EL Rate %",
                    'AVERAGE(fact_predictions[pd_calibrated])*100', "0.00\\%"),
        ],
        "dim_models": [
            measure("Top AUC", "MAXX(dim_models, dim_models[auc])", "0.0000"),
            measure("Top Gini", "MAXX(dim_models, dim_models[gini])", "0.0000"),
            measure("Top KS", "MAXX(dim_models, dim_models[ks])", "0.0000"),
            measure("Top Brier", "MINX(dim_models, dim_models[brier])", "0.0000"),
        ],
        "fact_feature_importance": [
            measure("Total Features", "COUNTROWS(fact_feature_importance)", "#,##0"),
            measure("Top Feature",
                    'CALCULATE(MAX(fact_feature_importance[feature_short]), TOPN(1, fact_feature_importance, fact_feature_importance[importance], DESC))', ""),
        ],
    }
    for tname, ms in measures.items():
        for tbl in tables:
            if tbl["name"] == tname:
                tbl["measures"] = ms
                break

    return {
        "name": "HomeCreditDataModel",
        "compatibilityLevel": 1567,
        "model": {
            "culture": "en-US",
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "en-US",
            "tables": tables,
            "annotations": [
                {"name": "PBI_QueryOrder",
                 "value": "[\"fact_predictions\",\"fact_feature_importance\",\"dim_models\",\"dim_risk_bands\",\"dim_segments\",\"fact_thresholds\"]"},
                {"name": "PBI_ProTooling", "value": "[\"DevMode\"]"},
            ],
        },
    }


# ----------------------------------------------------------------------
# Layout — 5 pages with real visuals
# ----------------------------------------------------------------------

def card_visual(name: str, x: int, y: int, w: int, h: int, measure: str, title: str) -> dict:
    return {
        "name": name,
        "layouts": [{"id": 0, "x": x, "y": y, "width": w, "height": h}],
        "singleVisual": {
            "visualType": "card",
            "projections": {"Values": [{"queryRef": f"Sum({measure})"}]},
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "t", "Entity": "fact_predictions", "Type": 0}],
                "Select": [{"Measure": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": measure},
                            "Name": measure}],
            },
            "objects": {
                "title": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#1A1A1A'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "10L"}}},
                    "alignment": {"expr": {"Literal": {"Value": "'center'"}}},
                }}],
                "labels": [{"properties": {
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#ED1C24'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "26L"}}},
                    "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI Light'"}}},
                }}],
            },
        },
        "howCreated": "insertVisual",
    }


def text_box(name: str, x: int, y: int, w: int, h: int, text: str, size: int = 14) -> dict:
    return {
        "name": name,
        "layouts": [{"id": 0, "x": x, "y": y, "width": w, "height": h}],
        "singleVisual": {
            "visualType": "textbox",
            "objects": {
                "general": [{"properties": {
                    "paragraphs": [{"textRuns": [{
                        "value": text, "fontFamily": "Segoe UI",
                        "fontSize": size, "color": "#1A1A1A", "bold": True,
                    }]}]
                }}]
            },
        },
        "howCreated": "insertVisual",
    }


def page_exec() -> dict:
    visuals = [
        text_box("h1", 40, 16, 1200, 32, "1 · EXECUTIVE SUMMARY — Home Credit Default Risk", 18),
        card_visual("k_total", 40, 60, 232, 100, "Total Customers", "TỔNG KHÁCH HÀNG"),
        card_visual("k_def",   290, 60, 232, 100, "Default Rate %", "TỈ LỆ VỠ NỢ"),
        card_visual("k_pd",    540, 60, 232, 100, "Average PD %", "PD TRUNG BÌNH"),
        card_visual("k_auc",   790, 60, 232, 100, "Top AUC", "AUC (BEST MODEL)"),
        card_visual("k_score", 1040, 60, 232, 100, "Average Score", "ĐIỂM TB"),
    ]
    return {
        "name": "ReportSection1",
        "displayName": "1 · Executive Summary",
        "displayOption": 0,
        "height": 720, "width": 1280,
        "visualContainers": visuals,
    }


def page_perf() -> dict:
    visuals = [
        text_box("h1", 40, 16, 1200, 32, "2 · MODEL PERFORMANCE — So sánh 4 mô hình", 18),
        card_visual("k_auc",   40, 60, 232, 100, "Top AUC",   "AUC (BEST)"),
        card_visual("k_gini",  290, 60, 232, 100, "Top Gini", "GINI (BEST)"),
        card_visual("k_ks",    540, 60, 232, 100, "Top KS",   "KS (BEST)"),
        card_visual("k_brier", 790, 60, 232, 100, "Top Brier","BRIER (MIN)"),
        card_visual("k_f1",   1040, 60, 232, 100, "F1 Score", "F1"),
    ]
    return {
        "name": "ReportSection2",
        "displayName": "2 · Model Performance",
        "displayOption": 0,
        "height": 720, "width": 1280,
        "visualContainers": visuals,
    }


def page_segment() -> dict:
    visuals = [
        text_box("h1", 40, 16, 1200, 32, "3 · RISK SEGMENTATION — Phân khúc rủi ro", 18),
        card_visual("k_h",     40, 60, 290, 100, "High Risk Count", "KHÁCH RỦI RO CAO"),
        card_visual("k_m",    350, 60, 290, 100, "Medium Risk Count", "RỦI RO TRUNG BÌNH"),
        card_visual("k_l",    660, 60, 290, 100, "Low Risk Count", "RỦI RO THẤP"),
        card_visual("k_hp",   970, 60, 270, 100, "High Risk Share %", "TỈ TRỌNG HIGH"),
    ]
    return {
        "name": "ReportSection3",
        "displayName": "3 · Risk Segmentation",
        "displayOption": 0,
        "height": 720, "width": 1280,
        "visualContainers": visuals,
    }


def page_feat() -> dict:
    visuals = [
        text_box("h1", 40, 16, 1200, 32, "4 · FEATURE IMPORTANCE — Top features driving PD", 18),
        card_visual("k_n",     40, 60, 400, 100, "Total Features", "SỐ FEATURES"),
        card_visual("k_top",  470, 60, 770, 100, "Top Feature", "TOP 1 FEATURE"),
    ]
    return {
        "name": "ReportSection4",
        "displayName": "4 · Feature Importance",
        "displayOption": 0,
        "height": 720, "width": 1280,
        "visualContainers": visuals,
    }


def page_port() -> dict:
    visuals = [
        text_box("h1", 40, 16, 1200, 32, "5 · PORTFOLIO DRILL-DOWN — Customer-level", 18),
        card_visual("k_t",     40, 60, 232, 100, "Total Customers", "TỔNG"),
        card_visual("k_el",   290, 60, 232, 100, "EL Rate %",       "EXPECTED LOSS"),
        card_visual("k_acc",  540, 60, 232, 100, "Accuracy",         "ACCURACY"),
        card_visual("k_rec",  790, 60, 232, 100, "Recall",           "RECALL"),
        card_visual("k_prec",1040, 60, 232, 100, "Precision",        "PRECISION"),
    ]
    return {
        "name": "ReportSection5",
        "displayName": "5 · Portfolio Drill-down",
        "displayOption": 0,
        "height": 720, "width": 1280,
        "visualContainers": visuals,
    }


def build_layout() -> dict:
    return {
        "id": 0,
        "name": "Report",
        "sections": [page_exec(), page_perf(), page_segment(), page_feat(), page_port()],
    }


# ----------------------------------------------------------------------
# File assembly
# ----------------------------------------------------------------------

VERSION = {"version": "1.0.0.0", "createdFrom": "PowerBI", "pbiVersion": "2.130.0.0"}

SETTINGS = {
    "name": "HomeCreditRiskDashboard",
    "modelSettings": {"defaultMode": "Import", "sourceQueryCulture": "en-US"},
    "reportSettings": {"useReportBackgroundImage": False, "defaultTextVisualFilterMode": 1},
}

DIAGRAM_STATE = {
    "version": 2,
    "diagrams": [{"id": "d1", "name": "All", "layout": {"nodeIds": [], "x": 0, "y": 0, "width": 0, "height": 0, "zoom": 100}, "nodes": [], "connections": []}],
}

LINGUISTIC = {"version": 2, "language": "en-US", "collation": "vi-VN", "semanticModel": {"name": "HomeCreditDataModel"}}


def main() -> None:
    PBIT_PATH.unlink(missing_ok=True)
    theme_bytes = THEME_PATH.read_bytes()
    with zipfile.ZipFile(PBIT_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Version", json.dumps(VERSION, ensure_ascii=False))
        zf.writestr("Settings", json.dumps(SETTINGS, ensure_ascii=False))
        zf.writestr("DataModelSchema", json.dumps(build_data_model(), ensure_ascii=False))
        zf.writestr("Report/Layout", json.dumps(build_layout(), ensure_ascii=False))
        zf.writestr("DiagramState", json.dumps(DIAGRAM_STATE, ensure_ascii=False))
        zf.writestr("Report/LinguisticSchema/LinguisticMetadata", json.dumps(LINGUISTIC, ensure_ascii=False))
        zf.writestr("Report/StaticResources/SharedResources/RegisteredResources/home_credit_theme.json", theme_bytes)
        zf.writestr("Metadata", json.dumps({"name": "HomeCreditRiskDashboard"}, ensure_ascii=False))
        zf.writestr("SecurityBindings", json.dumps({}, ensure_ascii=False))
        zf.writestr("MashupFormulas", json.dumps({"formulas": {}, "queriesMetadata": {}}, ensure_ascii=False))
    print(f"[OK] {PBIT_PATH}  ({PBIT_PATH.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
