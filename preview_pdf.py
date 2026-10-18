"""Render each PDF page to PNG for preview."""
import fitz
from pathlib import Path
pdf = fitz.open(r"C:\Dev\home-credit-default-risk\slides.pdf")
out = Path(r"C:\Dev\home-credit-default-risk\preview")
out.mkdir(exist_ok=True)
for i, page in enumerate(pdf, 1):
    pix = page.get_pixmap(dpi=110)
    pix.save(str(out / f"slide_{i:02d}.png"))
print(f"Rendered {len(pdf)} pages to {out}")
pdf.close()
