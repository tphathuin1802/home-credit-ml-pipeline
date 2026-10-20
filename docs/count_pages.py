"""Count pages of DOCX by:
   1) counting explicit page breaks (<w:br w:type="page"/>)
   2) estimating by paragraphs/tables if Word/LibreOffice absent."""
import sys, zipfile, re
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path

p = Path('c:/Dev/home-credit-default-risk/docs/D4_report_v3.docx')

with zipfile.ZipFile(p) as z:
    body = z.read('word/document.xml').decode('utf-8')

# explicit page breaks
explicit_pb = body.count('w:br w:type="page"') + body.count('w:type="page"')

# estimate: paragraph + table rows / 40 lines per page (TNR 12pt, 1.0 spacing)
n_para  = body.count('<w:p ') + body.count('<w:p>')
n_table = body.count('<w:tbl>')
print(f'Explicit page breaks: {explicit_pb}')
print(f'Total paragraphs:      {n_para}')
print(f'Total tables:          {n_table}')

# heuristic: ~35 lines per page with current formatting
lines_estimate = (n_para * 1.2) + (n_table * 5)
pages_estimate = explicit_pb + max(1, int(lines_estimate / 30))
print(f'Estimated pages (rough, based on paragraph count + explicit breaks): {pages_estimate}')
print(f'Expected explicit page count: {explicit_pb + 1}')

# Use python-docx to get exact sectPr count and re-count
from docx import Document
doc = Document(p)
total_paras = len(doc.paragraphs)
total_tables = len(doc.tables)
print(f'\npython-docx verified: paragraphs={total_paras}, tables={total_tables}')
print(f'Explicit page breaks via python-docx: {sum(1 for p in doc.paragraphs for r in p.runs if any(b.type for b in r._element.iter() if b.tag.endswith("}br")))}')