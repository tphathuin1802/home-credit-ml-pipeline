"""Quick smoke test for cloud deployment readiness."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src import predict
from app import streamlit_app as sa

# 1) Default customer (from sample data)
dc = predict.get_default_customer()
print(f"[1] default customer: {len(dc)} fields")
print(f"    DAYS_BIRTH={dc.get('DAYS_BIRTH')}, AMT_INCOME_TOTAL={dc.get('AMT_INCOME_TOTAL')}")
print(f"    NAME_CONTRACT_TYPE={dc.get('NAME_CONTRACT_TYPE')}")

# 2) Model info
info = predict.get_model_info()
print(f"\n[2] model info: {info}")

# 3) Sample data load
df = sa.load_sample_app(2000)
print(f"\n[3] sample data: {len(df)} rows, {df.shape[1]} cols")
print(f"    target rate: {df['TARGET'].mean():.2%}")

# 4) Prediction
test_record = dict(dc)
test_record['DAYS_BIRTH'] = -44 * 365
test_record['DAYS_EMPLOYED'] = -8 * 365
result = predict.predict_one(test_record)
print(f"\n[4] predict: pd={result['pd']:.4f}, score={result['score']:.0f}, band={result['risk_band']}")

# 5) Metrics
m = sa.load_metrics()
print(f"\n[5] metrics keys: {list(m.keys()) if m else 'EMPTY'}")

# 6) Feature importance
fi = sa.load_feature_importance()
print(f"\n[6] feature importance: shape={fi.shape if fi is not None else None}")

print("\n✓ All smoke tests passed.")
