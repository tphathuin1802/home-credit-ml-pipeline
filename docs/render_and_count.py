"""Use Word COM (Windows) to open D4_report_v3.docx, convert to PDF, and report page count."""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
import win32com.client as win32
from win32com.client import constants as C

PROJ = Path('c:/Dev/home-credit-default-risk')
SRC  = PROJ / 'docs' / 'D4_report_v3.docx'
PDF  = PROJ / 'docs' / 'D4_report_v3.pdf'

# Use late binding
word = win32.Dispatch('Word.Application')
word.Visible = False
word.DisplayAlerts = 0   # wdAlertsNone

doc = word.Documents.Open(str(SRC.absolute()))
# 17 = wdExportFormatPDF
doc.ExportAsFixedFormat(str(PDF.absolute()), 17, OpenAfterExport=False)
doc.Close(False)
word.Quit()

# read page count from PDF
import re
data = PDF.read_bytes()
# look for /Type /Page (not /Pages)
pages = len(re.findall(rb'/Type\s*/Page[^s]', data))
print(f'PDF size: {len(data):,} bytes')
print(f'Pages: {pages}')
print(f'PDF: {PDF}')