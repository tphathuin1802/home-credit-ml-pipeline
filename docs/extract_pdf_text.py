"""Extract text from slide PDF and report PDF."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
import subprocess

def extract(p):
    """Try pdftotext first, fall back to pypdf."""
    try:
        r = subprocess.run(['pdftotext', '-layout', str(p), '-'], capture_output=True, timeout=30)
        if r.returncode == 0:
            return r.stdout.decode('utf-8', errors='replace')
    except FileNotFoundError:
        pass
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(p))
        out = []
        for i, page in enumerate(reader.pages):
            out.append(f'\n===== PAGE {i+1} =====\n')
            out.append(page.extract_text() or '')
        return '\n'.join(out)
    except ImportError:
        pass
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(str(p))
        out = []
        for i, page in enumerate(reader.pages):
            out.append(f'\n===== PAGE {i+1} =====\n')
            out.append(page.extract_text() or '')
        return '\n'.join(out)
    except ImportError:
        return '[no PDF library available]'

PROJ = Path('c:/Dev/home-credit-default-risk')
slide = PROJ / 'home credit slide final.pdf'
report = PROJ / '[D4] Midterm Report - K234131613 _ K234131591.pdf'

print('=== SLIDES ===')
print(extract(slide))
print('\n\n=== REPORT ===')
print(extract(report))