"""Execute full workflow notebook end-to-end, appending to log file."""
import json, sys, time
from pathlib import Path
from io import StringIO
import contextlib

PROJ = Path(r'C:\Dev\home-credit-default-risk')
sys.path.insert(0, str(PROJ))

# Non-interactive matplotlib for headless run
import matplotlib
matplotlib.use('Agg')

# Clean artifacts (not .broken)
for p in (PROJ / 'model').iterdir():
    if p.is_file() and not p.name.endswith('.broken'):
        p.unlink()

nb = json.load(open(PROJ / 'notebooks' / 'home_credit_pipeline.ipynb', encoding='utf-8'))
g = {'__name__': '__main__', '__builtins__': __builtins__}

# Patch plt.show to be non-blocking
import matplotlib.pyplot as _plt
_orig_show = _plt.show
def _patched_show(*a, **kw):
    kw['block'] = False
    return _orig_show(*a, **kw)
_plt.show = _patched_show
g['_plt_show_patched'] = True
# Also ensure plt in cell uses patched
g['plt_show_original'] = _orig_show

LOG = open(PROJ / 'nb_run.log', 'w', encoding='utf-8')
def logp(*args):
    msg = ' '.join(str(a) for a in args)
    print(msg)
    LOG.write(msg + '\n')
    LOG.flush()

t_total = time.time()
errors = 0
code_cells = [c for c in nb['cells'] if c['cell_type'] == 'code']
logp(f'Total code cells: {len(code_cells)}')

for i, cell in enumerate(code_cells):
    src = ''.join(cell['source'])
    if not src.strip():
        continue
    idx = i + 1
    logp(f'\n[Cell {idx}] executing...')
    t = time.time()
    try:
        buf = StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            exec(compile(src, f'<cell-{idx}>', 'exec'), g)
        dt = time.time() - t
        out = buf.getvalue()
        lines = out.strip().splitlines()
        status = 'OK'
        if 'Traceback' in out or 'FAIL' in out:
            status = 'CHECK'
        logp(f'  [{status}] {dt:.1f}s, {len(lines)} lines')
        if lines:
            preview = '\n'.join(lines[-8:])
            if len(preview) > 300: preview = preview[:300] + '...'
            logp(preview)
    except Exception as e:
        dt = time.time() - t
        errors += 1
        logp(f'  [FAIL] {dt:.1f}s: {type(e).__name__}: {e}')
        import traceback
        tb = traceback.format_exc()
        logp(tb)
        break

logp(f'\n{"="*60}\nTotal: {time.time()-t_total:.1f}s, errors={errors}')
LOG.close()
sys.exit(1 if errors else 0)
