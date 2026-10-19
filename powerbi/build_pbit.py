"""Build HomeCreditRiskDashboard.pbit (Power BI Template).

A .pbit is a ZIP archive. We emit a minimal but valid template that:
- Carries the data-model schema (tables + columns + Power Query M for the CSVs)
- Carries the Home Credit color theme (JSON)
- Carries placeholder layout files

When the user opens the .pbit in Power BI Desktop they will be prompted
once to pick the folder containing the exported CSVs (one Get Data
per file); the model + theme load automatically.

This is the safe way to ship a template: we never try to author visuals
in JSON, which is brittle and would require Microsoft internal schemas.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PBIT_PATH = ROOT / "powerbi" / "HomeCreditRiskDashboard.pbit"
THEME_PATH = ROOT / "powerbi" / "theme" / "home_credit_theme.json"
DATA_DIR = ROOT / "powerbi" / "data"


VERSION = {
    "version": "1.0.0.0",
    "createdFrom": "PowerBI",
    "pbiVersion": "2.130.0.0",
}

SETTINGS = {
    "name": "HomeCreditRiskDashboard",
    "modelSettings": {
        "defaultMode": "Import",
        "sourceQueryCulture": "en-US",
    },
    "reportSettings": {
        "useReportBackgroundImage": False,
        "defaultTextVisualFilterMode": 1,
    },
}

DIAGRAM_STATE = {
    "version": 2,
    "diagrams": [
        {
            "id": "diagram1",
            "name": "All Tables",
            "layout": {"nodeIds": [], "x": 0, "y": 0, "width": 0, "height": 0, "zoom": 100},
            "nodes": [],
            "connections": [],
        }
    ],
}

LINGUISTIC = {
    "version": 2,
    "language": "en-US",
    "collation": "vi-VN",
    "semanticModel": {"name": "HomeCreditDataModel"},
}


def build_data_model_schema() -> dict:
    """Define the 6 tables with their Power Query M sources (relative paths)."""
    def csv_table(table: str, columns: list[dict], types: list[tuple]) -> dict:
        col_types = ", ".join([f'{{"{n}", {t}}}' for n, t in types])
        headers = ", ".join([f'"{c["name"]}"' for c in columns])
        return {
            "name": table,
            "columns": columns,
            "partitions": [
                {
                    "name": table,
                    "dataView": "full",
                    "source": {
                        "type": "m",
                        "expression": [
                            (
                                f'let\n'
                                f'    Source = Csv.Document(File.Contents("{table}.csv"),'
                                f'[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.None]),\n'
                                f'    Promote = Table.PromoteHeaders(Source),\n'
                                f'    ChangedTypes = Table.TransformColumnTypes(Promote,{{{col_types}}})\n'
                                f'in\n    ChangedTypes'
                            )
                        ],
                    },
                }
            ],
        }

    fact_pred_cols = [
        {"name": c, "dataType": t, "formatString": fmt}
        for c, t, fmt in [
            ("customer_id", "int64", "0"),
            ("pd_raw", "double", "0.00%"),
            ("pd_calibrated", "double", "0.00%"),
            ("predicted_default", "int64", "0"),
            ("actual_default", "int64", "0"),
            ("score", "int64", "0"),
            ("risk_band", "string", ""),
            ("pd_bucket", "string", ""),
            ("rating_class", "string", ""),
            ("is_correct", "int64", "0"),
            ("is_true_positive", "int64", "0"),
            ("is_false_positive", "int64", "0"),
            ("is_false_negative", "int64", "0"),
            ("is_true_negative", "int64", "0"),
        ]
    ]
    fact_pred_types = [
        ("customer_id", "Int64.Type"), ("pd_raw", "type number"),
        ("pd_calibrated", "type number"), ("predicted_default", "Int64.Type"),
        ("actual_default", "Int64.Type"), ("score", "Int64.Type"),
        ("risk_band", "type text"), ("pd_bucket", "type text"),
        ("rating_class", "type text"), ("is_correct", "Int64.Type"),
        ("is_true_positive", "Int64.Type"), ("is_false_positive", "Int64.Type"),
        ("is_false_negative", "Int64.Type"), ("is_true_negative", "Int64.Type"),
    ]

    fact_fi_cols = [
        {"name": "feature", "dataType": "string", "formatString": ""},
        {"name": "importance", "dataType": "int64", "formatString": "0"},
        {"name": "rank", "dataType": "int64", "formatString": "0"},
        {"name": "feature_group", "dataType": "string", "formatString": ""},
        {"name": "feature_short", "dataType": "string", "formatString": ""},
    ]
    fact_fi_types = [
        ("feature", "type text"), ("importance", "Int64.Type"),
        ("rank", "Int64.Type"), ("feature_group", "type text"),
        ("feature_short", "type text"),
    ]

    dim_models_cols = [
        {"name": "model_id", "dataType": "string", "formatString": ""},
        {"name": "model_name", "dataType": "string", "formatString": ""},
        {"name": "auc", "dataType": "double", "formatString": "0.0000"},
        {"name": "gini", "dataType": "double", "formatString": "0.0000"},
        {"name": "ks", "dataType": "double", "formatString": "0.0000"},
        {"name": "brier", "dataType": "double", "formatString": "0.0000"},
        {"name": "pr_auc", "dataType": "double", "formatString": "0.0000"},
        {"name": "f1", "dataType": "double", "formatString": "0.0000"},
        {"name": "recall", "dataType": "double", "formatString": "0.00%"},
        {"name": "precision", "dataType": "double", "formatString": "0.00%"},
        {"name": "threshold", "dataType": "double", "formatString": "0.0000"},
        {"name": "is_recommended", "dataType": "int64", "formatString": "0"},
        {"name": "rank_auc", "dataType": "int64", "formatString": "0"},
    ]
    dim_models_types = [
        ("model_id", "type text"), ("model_name", "type text"),
        ("auc", "type number"), ("gini", "type number"),
        ("ks", "type number"), ("brier", "type number"),
        ("pr_auc", "type number"), ("f1", "type number"),
        ("recall", "type number"), ("precision", "type number"),
        ("threshold", "type number"), ("is_recommended", "Int64.Type"),
        ("rank_auc", "Int64.Type"),
    ]

    dim_rb_cols = [
        {"name": "risk_band", "dataType": "string", "formatString": ""},
        {"name": "risk_band_label", "dataType": "string", "formatString": ""},
        {"name": "score_min", "dataType": "double", "formatString": "0"},
        {"name": "score_max", "dataType": "double", "formatString": "0"},
        {"name": "color_hex", "dataType": "string", "formatString": ""},
        {"name": "action", "dataType": "string", "formatString": ""},
    ]
    dim_rb_types = [
        ("risk_band", "type text"), ("risk_band_label", "type text"),
        ("score_min", "type number"), ("score_max", "type number"),
        ("color_hex", "type text"), ("action", "type text"),
    ]

    dim_seg_cols = [
        {"name": "dimension", "dataType": "string", "formatString": ""},
        {"name": "value", "dataType": "string", "formatString": ""},
        {"name": "min", "dataType": "double", "formatString": "0"},
        {"name": "max", "dataType": "double", "formatString": "0"},
        {"name": "order", "dataType": "int64", "formatString": "0"},
    ]
    dim_seg_types = [
        ("dimension", "type text"), ("value", "type text"),
        ("min", "type number"), ("max", "type number"),
        ("order", "Int64.Type"),
    ]

    fact_th_cols = [
        {"name": "threshold", "dataType": "double", "formatString": "0.0000"},
        {"name": "is_recommended", "dataType": "int64", "formatString": "0"},
    ]
    fact_th_types = [("threshold", "type number"), ("is_recommended", "Int64.Type")]

    tables = [
        csv_table("fact_predictions", fact_pred_cols, fact_pred_types),
        csv_table("fact_feature_importance", fact_fi_cols, fact_fi_types),
        csv_table("dim_models", dim_models_cols, dim_models_types),
        csv_table("dim_risk_bands", dim_rb_cols, dim_rb_types),
        csv_table("dim_segments", dim_seg_cols, dim_seg_types),
        csv_table("fact_thresholds", fact_th_cols, fact_th_types),
    ]

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
            ],
        },
    }


# ----------------------------------------------------------------------
# Minimal layout: 1 page with a single text-box saying "open and build"
# (Power BI rejects truly empty pages)
# ----------------------------------------------------------------------

INTRO_PAGE = {
    "id": 0,
    "name": "ReportSection",
    "displayName": "Page 1",
    "displayOption": 0,
    "height": 720,
    "width": 1280,
    "visualContainers": [
        {
            "name": "TextBox1",
            "layouts": [{"id": 0, "x": 40, "y": 40, "width": 1200, "height": 200}],
            "singleVisual": {
                "visualType": "textbox",
                "objects": {
                    "general": [{"properties": {
                        "paragraphs": [
                            {
                                "textRuns": [
                                    {
                                        "value": (
                                            "HOME CREDIT DEFAULT RISK DASHBOARD\n"
                                            "Open this template in Power BI Desktop, then click "
                                            "Transform Data -> Data Source Settings to point at the "
                                            "csv files in powerbi/data/.\n"
                                            "After loading, follow the steps in powerbi/docs/build_guide.md "
                                            "to author the 5 pages described in the guide."
                                        ),
                                        "fontFamily": "Segoe UI",
                                        "fontSize": 14,
                                        "color": "#1A1A1A",
                                    }
                                ]
                            }
                        ]
                    }}]
                }
            },
            "howCreated": "insertVisual",
        }
    ],
}


def build_pbit() -> None:
    PBIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    theme_bytes = THEME_PATH.read_bytes()
    with zipfile.ZipFile(PBIT_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Version",                json.dumps(VERSION, ensure_ascii=False))
        zf.writestr("Settings",               json.dumps(SETTINGS, ensure_ascii=False))
        zf.writestr("DataModelSchema",        json.dumps(build_data_model_schema(), ensure_ascii=False))
        zf.writestr("Report/Layout",          json.dumps(INTRO_PAGE, ensure_ascii=False))
        zf.writestr("DiagramState",           json.dumps(DIAGRAM_STATE, ensure_ascii=False))
        zf.writestr("Report/LinguisticSchema/LinguisticMetadata",
                    json.dumps(LINGUISTIC, ensure_ascii=False))
        zf.writestr("Report/StaticResources/SharedResources/RegisteredResources/home_credit_theme.json",
                    theme_bytes)
        zf.writestr("Metadata",               json.dumps({"name": "HomeCreditRiskDashboard"}, ensure_ascii=False))
        zf.writestr("SecurityBindings",       json.dumps({}, ensure_ascii=False))
        zf.writestr("MashupFormulas",         json.dumps({"formulas": {}, "queriesMetadata": {}}, ensure_ascii=False))
    print(f"[OK] {PBIT_PATH}  ({PBIT_PATH.stat().st_size:,} bytes)")


if __name__ == "__main__":
    build_pbit()
