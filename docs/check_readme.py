from pathlib import Path
import sys
sys.stdout.reconfigure(encoding='utf-8')
p = Path('c:/Dev/home-credit-default-risk/powerbi/README.md')
text = p.read_text(encoding='utf-8')
print('Size :', len(text.encode('utf-8')), 'bytes')
print('Lines:', text.count(chr(10)))
print()
print('--- Headings ---')
import re
for line in text.splitlines():
    if line.startswith('#'):
        print(line)
