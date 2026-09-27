
from pathlib import Path
import json

def calculate_margins(page_count):
    inside = 0.375 + (page_count / 1000) * 0.125
    return {"inside": inside, "outside": 0.5, "top": 0.5, "bottom": 0.5, "bleed": 0.125}

def export_kdp_pdf(chapters_dir="book_data/chapters", images_dir="book_data/images", out_path="book_data/output/kdp_print.pdf", trim="6x9", page_count_est=200):
    trims = {"5x8": [5,8], "5.5x8.5": [5.5,8.5], "6x9": [6,9]}
    trim_w, trim_h = trims.get(trim, [6,9])
    margins = calculate_margins(page_count_est)
    
    print(f"[KDP] Trim {trim} = {trim_w}x{trim_h} inches")
    print(f"[KDP] Margins: {margins}")
    print(f"[KDP] Page size with bleed: {trim_w+margins['bleed']*2} x {trim_h+margins['bleed']*2}")
    
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Try reportlab if available, else placeholder
    try:
        from reportlab.lib.units import inch as INCH
        from reportlab.pdfgen import canvas
        page_w = (trim_w + margins['bleed']*2) * INCH
        page_h = (trim_h + margins['bleed']*2) * INCH
        c = canvas.Canvas(out_path, pagesize=(page_w, page_h))
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(page_w/2, page_h/2 + 100, "My Book Title")
        c.setFont("Helvetica", 8)
        c.drawCentredString(page_w/2, 50, f"Trim: {trim} | Inside: {margins['inside']:.3f}")
        c.showPage()
        c.save()
    except ImportError:
        Path(out_path).write_text(f"KDP PDF placeholder - trim {trim} margins {margins}")
    
    print(f"[KDP] Exported to {out_path}")
    return out_path
