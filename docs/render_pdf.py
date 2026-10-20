"""Render a DOCX to PDF via Word COM and report page count."""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
import win32com.client as win32

PROJ = Path('c:/Dev/home-credit-default-risk')

def to_pdf(name):
    src = PROJ / 'docs' / f'{name}.docx'
    pdf = PROJ / 'docs' / f'{name}.pdf'
    word = win32.Dispatch('Word.Application')
    word.Visible = False
    word.DisplayAlerts = 0
    doc = word.Documents.Open(str(src.absolute()))
    doc.ExportAsFixedFormat(str(pdf.absolute()), 17, OpenAfterExport=False)
    doc.Close(False)
    word.Quit()
    data = pdf.read_bytes()
    pages = len(re.findall(rb'/Type\s*/Page[^s]', data))
    print(f'{name}.pdf  ->  {pages} pages, {len(data):,} bytes')
    return pages

for n in ['presentation_script']:
    to_pdf(n)