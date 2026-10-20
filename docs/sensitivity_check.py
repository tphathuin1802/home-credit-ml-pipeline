"""Sensitivity checks: bootstrap CI + threshold sweep.
Uses ONLY predictions_test.csv (LGB-CAL column y_proba).
For comparison, also loads fixed AUC of LR (0.7452) and LGB raw (0.7594) from notebook metrics."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score

PROJ = Path('c:/Dev/home-credit-default-risk')
df   = pd.read_csv(PROJ / 'model' / 'predictions_test.csv')
print('Test rows:', len(df))
print('Default rate:', df['y_true'].mean())

y_true  = df['y_true'].values
y_proba = df['y_proba'].values  # LGB-CAL

# ──────────────────────────────────────────────────────────────────────────────
# 1.  BOOTSTRAP 1,000 ITERATIONS: CI 95% of AUC
# ──────────────────────────────────────────────────────────────────────────────
rng = np.random.default_rng(42)
B   = 1000
n   = len(y_true)
boot_auc_lgbc = np.empty(B)

# baseline AUCs reported by notebook (no per-row predictions stored for them,
# so we cannot bootstrap them — we use the published point estimate).
AUC_LR  = 0.7452
AUC_LGB = 0.7594
AUC_LGB_CAL_POINT = roc_auc_score(y_true, y_proba)
print(f'\nPoint estimate LGB-CAL AUC = {AUC_LGB_CAL_POINT:.4f}')

for b in range(B):
    idx = rng.integers(0, n, n)
    boot_auc_lgbc[b] = roc_auc_score(y_true[idx], y_proba[idx])

ci_low, ci_high = np.percentile(boot_auc_lgbc, [2.5, 97.5])
print(f'Bootstrap 95% CI for LGB-CAL AUC: [{ci_low:.4f}, {ci_high:.4f}]')

# CI of the LGB-CAL − LR gap (sampling-uncertainty only)
# resample LR under H0: LR AUC has same variance as LGB-CAL under bootstrap
# (approximation: resample LGB-CAL AUC and subtract the LR point estimate ± SE)
se = boot_auc_lgbc.std()
gap_diff = float(AUC_LGB_CAL_POINT - AUC_LR)
gap_low  = gap_diff - 1.96*se
gap_high = gap_diff + 1.96*se
print(f'Gap LGB-CAL − LR = {gap_diff:+.4f},  95% CI ≈ [{gap_low:+.4f}, {gap_high:+.4f}]')

gap_diff2 = float(AUC_LGB - AUC_LR)
gap_low2  = gap_diff2 - 1.96*se
gap_high2 = gap_diff2 + 1.96*se
print(f'Gap LGB    − LR = {gap_diff2:+.4f},  95% CI ≈ [{gap_low2:+.4f}, {gap_high2:+.4f}]')

# ──────────────────────────────────────────────────────────────────────────────
# 2.  THRESHOLD SENSITIVITY
# ──────────────────────────────────────────────────────────────────────────────
print('\nThreshold sensitivity (LGB-CAL, test fold):')
print(f'{"τ":>5}  {"Recall":>8}  {"Prec":>8}  {"F1":>8}  {"Flag%":>8}  {"TN":>5}  {"FP":>5}  {"FN":>5}  {"TP":>5}')

rows = []
for tau in [0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]:
    yp = (y_proba >= tau).astype(int)
    rec = recall_score(y_true, yp)
    pre = precision_score(y_true, yp)
    f1  = f1_score(y_true, yp)
    pct = 100 * yp.mean()
    tn, fp, fn, tp = (y_true==0)&(yp==0), (y_true==0)&(yp==1), (y_true==1)&(yp==0), (y_true==1)&(yp==1)
    n_tn, n_fp, n_fn, n_tp = tn.sum(), fp.sum(), fn.sum(), tp.sum()
    rows.append((tau, rec, pre, f1, pct, n_tn, n_fp, n_fn, n_tp))
    print(f'{tau:>5.2f}  {rec:>8.3f}  {pre:>8.3f}  {f1:>8.3f}  {pct:>8.1f}  {n_tn:>5d}  {n_fp:>5d}  {n_fn:>5d}  {n_tp:>5d}')

# ──────────────────────────────────────────────────────────────────────────────
# 3.  BAND-CUT ROBUSTNESS: switch fixed (640/760) cuts to tertile cuts
# ──────────────────────────────────────────────────────────────────────────────
# Score formula from notebook config
import importlib.util
spec = importlib.util.spec_from_file_location('cfg', PROJ / 'src' / 'config.py')
cfg  = importlib.util.module_from_spec(spec); spec.loader.exec_module(cfg)
score = cfg.SCORE_BASE - (cfg.SCORE_PDO/np.log(2)) * np.log(y_proba / (1 - y_proba))
print(f'\nScore range: [{score.min():.0f}, {score.max():.0f}]')

def band_fixed(s):
    if s >= 760: return 'Thấp'
    if s >= 640: return 'Trung bình'
    return 'Cao'

# tertile cut on observed score distribution
q1, q2 = np.percentile(score, [100/3, 200/3])
def band_tert(s):
    if s >= q2: return 'Thấp'
    if s >= q1: return 'Trung bình'
    return 'Cao'

bands_fix   = pd.Series([band_fixed(s) for s in score])
bands_tert  = pd.Series([band_tert(s)  for s in score])

print(f'\nFixed cuts (640 / 760):')
print(bands_fix.value_counts().reindex(['Thấp','Trung bình','Cao']))

print(f'\nTertile cuts (q1={q1:.0f}, q2={q2:.0f}):')
print(bands_tert.value_counts().reindex(['Thấp','Trung bình','Cao']))

print('\nDefault rate by band — fixed:')
print(pd.DataFrame({'band': bands_fix, 'default': y_true}).groupby('band')['default'].agg(['mean','count']))

print('\nDefault rate by band — tertile:')
print(pd.DataFrame({'band': bands_tert, 'default': y_true}).groupby('band')['default'].agg(['mean','count']))

# save results
out = PROJ / 'model' / 'sensitivity_results.json'
result = {
    'bootstrap': {
        'B': B,
        'lgbc_point_auc': AUC_LGB_CAL_POINT,
        'lgbc_ci_low': float(ci_low),
        'lgbc_ci_high': float(ci_high),
        'gap_lgbc_minus_lr': float(gap_diff),
        'gap_lgb_minus_lr': float(gap_diff2),
        'gap_lgbc_ci_low': float(gap_low),
        'gap_lgbc_ci_high': float(gap_high),
        'gap_lgb_ci_low': float(gap_low2),
        'gap_lgb_ci_high': float(gap_high2),
    },
    'threshold': [
        {'tau': float(t), 'recall': float(r), 'precision': float(p), 'f1': float(f), 'flag_pct': float(pct),
         'TN': int(tn), 'FP': int(fp), 'FN': int(fn), 'TP': int(tp)}
        for (t,r,p,f,pct,tn,fp,fn,tp) in rows
    ],
    'band_cut': {
        'fixed_thr': [640, 760],
        'tertile_q1': float(q1),
        'tertile_q2': float(q2),
    }
}
out.write_text(json.dumps(result, indent=2))
print(f'\nSaved: {out}')