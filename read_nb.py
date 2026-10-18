"""Read final cells of notebook."""
import json
sys_path = r'C:\Dev\home-credit-default-risk\notebooks\home_credit_pipeline.ipynb'
with open(sys_path, encoding='utf-8') as f:
    nb = json.load(f)
for i in range(35, 46):
    c = nb['cells'][i]
    src = ''.join(c['source']) if isinstance(c['source'], list) else c['source']
    print('=== %s %d ===' % (c['cell_type'].upper(), i))
    print(src[:1500])
    print()
