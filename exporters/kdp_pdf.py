from pathlib import Path
import json
import textwrap
import html
import re

def calculate_margins(page_count):
    inside = 0.375 + (page_count / 1000) * 0.125
    return {"inside": inside, "outside": 0.5, "top": 0.5, "bottom": 0.5, "bleed": 0.125}

def _safe_text(t):
    if not t:
        return ""
    t = html.escape(t)
    t = t.replace('\n', '<br/>')
    return t

def _safe_title(t):
    if not t:
        return "Chapter"
    t = t.strip()
    t = t.lstrip('# ').strip()
    t = html.escape(t)[:200]
    return t or "Chapter"

def _clean_chapter_content(raw):
    if not raw:
        return ""
    lines = raw.splitlines()
    cleaned = []
    for line in lines:
        l = line.strip()
        if l.startswith("Write chapter ch") or l.startswith("Chapter prompt:") or l.startswith("Previous chapters for continuity:") or l.startswith("--- ch"):
            continue
        if l.startswith("[Placeholder") or l.startswith("[Story would be generated"):
            continue
        if "Previous chapters" in l and len(l) < 100:
            continue
        if len(l) > 300 and ("Write chapter" in l or "Chapter prompt" in l):
            continue
        cleaned.append(line)
    result = "\n".join(cleaned).strip()
    if result.startswith("Write chapter"):
        parts = result.split("\n\n")
        for p in parts:
            if len(p) > 100 and "Write chapter" not in p[:100] and "Chapter prompt" not in p[:100]:
                idx = result.find(p)
                if idx > 0:
                    result = result[idx:]
                    break
    return result.strip() or raw.strip()

def export_kdp_pdf(chapters_dir="book_data/chapters", images_dir="book_data/images", out_path="book_data/output/kdp_print.pdf", trim="8.5x11", page_count_est=20, project_id=None):
    trims = {"5x8": [5,8], "5.5x8.5": [5.5,8.5], "6x9": [6,9], "8.5x11": [8.5,11]}
    trim_w, trim_h = trims.get(trim, [8.5,11])
    margins = calculate_margins(page_count_est)
    
    base_path = None
    if project_id:
        try:
            from core.project_manager import project_manager
            base = project_manager.get_project_path(project_id)
            if base.exists():
                chapters_dir = str(base / "chapters")
                images_dir = str(base / "images")
                if out_path == "book_data/output/kdp_print.pdf":
                    out_path = str(base / "output" / "kdp_print.pdf")
                base_path = base
            print(f"[KDP] Using project {project_id} -> base {base}")
        except Exception as e:
            print(f"[KDP] Project resolve failed for {project_id}: {e}")
            import traceback
            traceback.print_exc()
    else:
        try:
            from core.project_manager import project_manager
            curr = project_manager.get_current()
            if curr:
                base = project_manager.get_project_path()
                if Path(base).exists() and (base / "chapters").exists():
                    chapters_dir = str(base / "chapters")
                    images_dir = str(base / "images")
                    if out_path == "book_data/output/kdp_print.pdf":
                        out_path = str(base / "output" / "kdp_print.pdf")
                    base_path = base
                    project_id = curr
                    print(f"[KDP] Using current project {curr} -> {base}")
        except Exception as e:
            print(f"[KDP] Current project resolve failed: {e}")

    print(f"[KDP] Trim {trim} = {trim_w}x{trim_h} inches")
    print(f"[KDP] Chapters dir: {chapters_dir} (exists={Path(chapters_dir).exists()})")
    print(f"[KDP] Images dir: {images_dir} (exists={Path(images_dir).exists()})")
    print(f"[KDP] Out: {out_path}")
    
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    
    chapters_path = Path(chapters_dir)
    images_path = Path(images_dir)
    
    chapter_files = []
    if chapters_path.exists():
        all_txt = list(chapters_path.glob("*.txt"))
        print(f"[KDP] All .txt in {chapters_path}: {[p.name for p in all_txt]}")
        for p in sorted(all_txt):
            stem = p.stem.lower()
            if stem.startswith("ch") or "chapter" in stem or (stem and stem[0].isdigit()):
                chapter_files.append(p)
            elif p.stat().st_size > 10:
                chapter_files.append(p)
        
        def ch_sort_key(p):
            nums = re.findall(r'\d+', p.stem)
            return int(nums[0]) if nums else 999
        chapter_files = sorted(chapter_files, key=ch_sort_key)
    else:
        print(f"[KDP] Chapters path does not exist: {chapters_path}")
    
    print(f"[KDP] Found {len(chapter_files)} chapters: {[p.name for p in chapter_files]}")
    
    if not chapter_files:
        print(f"[KDP] No chapters found - checking legacy locations...")
        for fallback in [Path("book_data/chapters"), Path("book_data/books")]:
            if fallback.exists():
                found = list(fallback.rglob("ch*.txt"))[:5]
                if found:
                    print(f"[KDP] Found in fallback {fallback}: {found}")
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import inch as INCH
            page_w = (trim_w + 0.25) * INCH
            page_h = (trim_h + 0.25) * INCH
            c = canvas.Canvas(out_path, pagesize=(page_w, page_h))
            c.setFont("Helvetica-Bold", 16)
            c.drawString(1*INCH, page_h - 1*INCH, f"No chapters found!")
            c.setFont("Helvetica", 12)
            c.drawString(1*INCH, page_h - 1.5*INCH, f"Checked: {chapters_dir}")
            c.drawString(1*INCH, page_h - 2*INCH, f"Project: {project_id or 'none'}")
            c.drawString(1*INCH, page_h - 2.5*INCH, f"Exists: {chapters_path.exists()}")
            if chapters_path.exists():
                c.drawString(1*INCH, page_h - 3*INCH, f"Files: {list(chapters_path.glob('*'))[:10]}")
            c.save()
            print(f"[KDP] Diagnostic PDF created -> {out_path}")
        except Exception as e:
            Path(out_path).write_text(f"No chapters - checked {chapters_dir}")
        return out_path
    
    try:
        from reportlab.lib.units import inch as INCH
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib.utils import ImageReader
        
        page_w = (trim_w + margins['bleed']*2) * INCH
        page_h = (trim_h + margins['bleed']*2) * INCH
        
        doc = SimpleDocTemplate(
            out_path,
            pagesize=(page_w, page_h),
            leftMargin=margins['outside']*INCH,
            rightMargin=margins['inside']*INCH,
            topMargin=margins['top']*INCH,
            bottomMargin=margins['bottom']*INCH
        )
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=28, alignment=TA_CENTER, spaceAfter=20, leading=32)
        heading_style = ParagraphStyle('Head', parent=styles['Heading2'], fontSize=18, alignment=TA_LEFT, spaceAfter=12, spaceBefore=12, leading=22)
        body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=11, leading=15, alignment=TA_LEFT, spaceAfter=6)
        small_style = ParagraphStyle('Small', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor='#666666')
        
        story = []
        
        title_text = "My Book"
        if base_path:
            bible_path = base_path / "book_bible.json"
            if bible_path.exists():
                try:
                    title_text = json.loads(bible_path.read_text()).get("title", title_text)
                except:
                    pass
        else:
            bible_path = chapters_path.parent / "book_bible.json"
            if bible_path.exists():
                try:
                    title_text = json.loads(bible_path.read_text()).get("title", title_text)
                except:
                    pass
        
        story.append(Spacer(1, 2*INCH))
        story.append(Paragraph(_safe_title(title_text), title_style))
        story.append(Spacer(1, 0.2*INCH))
        story.append(Paragraph(f"{len(chapter_files)} chapters - {trim} - {project_id or 'book'}", body_style))
        story.append(Spacer(1, 0.3*INCH))
        story.append(Paragraph(f"Generated: {len(chapter_files)} pages with images", small_style))
        story.append(PageBreak())
        
        for idx, ch_file in enumerate(chapter_files):
            try:
                raw = ch_file.read_text(encoding='utf-8', errors='ignore')
                cleaned_raw = _clean_chapter_content(raw)
            except Exception as e:
                print(f"[KDP] Failed to read {ch_file}: {e}")
                cleaned_raw = f"Error reading {ch_file.name}: {e}"
                raw = cleaned_raw
            
            lines = cleaned_raw.splitlines()
            first_line = lines[0] if lines else ch_file.stem
            chapter_title = _safe_title(first_line)
            
            body_lines = [l for l in lines[1:] if l.strip()] if len(lines) > 1 else lines
            body_text = "\n\n".join(body_lines) if body_lines else cleaned_raw
            if not body_text.strip():
                body_text = cleaned_raw
            
            print(f"[KDP] Chapter {idx+1}/{len(chapter_files)}: {ch_file.name} - title '{chapter_title}' - {len(body_text)} chars")
            
            story.append(Paragraph(chapter_title, heading_style))
            story.append(Spacer(1, 0.1*INCH))
            
            img_file = None
            for cand in [
                images_path / f"{ch_file.stem}_01.jpg",
                images_path / f"{ch_file.stem}.jpg",
                images_path / f"{ch_file.stem}_01.png",
                images_path / f"{ch_file.stem}.png",
                images_path / f"{ch_file.stem}_01.jpeg",
            ]:
                if cand.exists():
                    img_file = cand
                    break
            if not img_file:
                matches = list(images_path.glob(f"{ch_file.stem}*.*")) if images_path.exists() else []
                if matches:
                    for m in matches:
                        if m.suffix.lower() in ['.jpg','.jpeg','.png']:
                            img_file = m
                            break
                    if not img_file and matches:
                        img_file = matches[0]
            
            if img_file and img_file.exists():
                try:
                    img_reader = ImageReader(str(img_file))
                    iw, ih = img_reader.getSize()
                    max_w = (trim_w - margins['inside'] - margins['outside'] - 0.3) * INCH
                    max_h = 4 * INCH
                    scale = min(max_w / iw, max_h / ih, 1.0)
                    rl_img = RLImage(str(img_file), width=iw*scale, height=ih*scale)
                    rl_img.hAlign = 'CENTER'
                    story.append(rl_img)
                    story.append(Spacer(1, 0.15*INCH))
                    print(f"[KDP] Added image {img_file.name}")
                except Exception as e:
                    print(f"[KDP] Image failed {img_file}: {e}")
                    story.append(Paragraph(f"[Image: {img_file.name} - failed to load]", small_style))
            
            paras = [p.strip() for p in body_text.split('\n\n') if p.strip()]
            if not paras:
                paras = [body_text]
            
            for para in paras[:20]:
                if len(para) > 2000:
                    para = para[:2000] + "..."
                try:
                    story.append(Paragraph(_safe_text(para), body_style))
                except Exception as e:
                    print(f"[KDP] Para failed: {e}")
                    try:
                        safe = html.escape(para[:500])
                        story.append(Paragraph(safe, body_style))
                    except:
                        pass
            
            story.append(Spacer(1, 0.15*INCH))
            story.append(Paragraph(f"{ch_file.stem} - Page {idx+1}/{len(chapter_files)}", small_style))
            
            if idx < len(chapter_files) - 1:
                story.append(PageBreak())
        
        doc.build(story)
        print(f"[KDP] SUCCESS: PDF with {len(chapter_files)} chapters -> {out_path}")
        return out_path
        
    except Exception as e:
        print(f"[KDP] Platypus failed: {e}")
        import traceback
        traceback.print_exc()
        print("[KDP] Falling back to simple canvas PDF...")
        try:
            from reportlab.lib.units import inch as INCH
            from reportlab.pdfgen import canvas
            page_w = (trim_w + margins['bleed']*2) * INCH
            page_h = (trim_h + margins['bleed']*2) * INCH
            c = canvas.Canvas(out_path, pagesize=(page_w, page_h))
            
            c.setFont("Helvetica-Bold", 24)
            title = "My Book"
            if base_path:
                bp = base_path / "book_bible.json"
                if bp.exists():
                    try:
                        title = json.loads(bp.read_text()).get("title", title)
                    except:
                        pass
            c.drawCentredString(page_w/2, page_h/2 + 80, title[:80])
            c.setFont("Helvetica", 12)
            c.drawCentredString(page_w/2, page_h/2 + 50, f"{len(chapter_files)} chapters - {trim}")
            c.setFont("Helvetica", 8)
            c.drawCentredString(page_w/2, page_h/2 + 30, f"Project: {project_id}")
            c.showPage()
            
            for ch_file in chapter_files:
                try:
                    raw = ch_file.read_text(encoding='utf-8', errors='ignore')
                    raw = _clean_chapter_content(raw)
                except:
                    raw = f"[Error reading {ch_file.name}]"
                
                c.setFont("Helvetica-Bold", 14)
                c.drawString(margins['outside']*INCH, page_h - 0.8*INCH, _safe_title(raw.splitlines()[0] if raw else ch_file.stem)[:60])
                c.setFont("Helvetica", 10)
                y = page_h - 1.2*INCH
                
                img_file = images_path / f"{ch_file.stem}_01.jpg"
                if not img_file.exists():
                    img_file = images_path / f"{ch_file.stem}.jpg"
                if img_file.exists():
                    try:
                        img_w = (trim_w - margins['inside'] - margins['outside'] - 0.5) * INCH
                        img_h = 2.5 * INCH
                        c.drawImage(str(img_file), margins['outside']*INCH, y - img_h, width=img_w, height=img_h, preserveAspectRatio=True)
                        y -= img_h + 0.3*INCH
                    except:
                        pass
                
                for line in raw.splitlines()[1:]:
                    if not line.strip():
                        y -= 12
                        continue
                    wrapped = textwrap.wrap(line, width=85)
                    for wline in wrapped:
                        if y < 1*INCH:
                            c.showPage()
                            y = page_h - 1*INCH
                            c.setFont("Helvetica", 10)
                        c.drawString(margins['outside']*INCH, y, wline[:90])
                        y -= 12
                
                c.showPage()
            
            c.save()
            print(f"[KDP] Fallback canvas PDF -> {out_path}")
            return out_path
        except ImportError as ie:
            Path(out_path).write_text(f"Install reportlab: pip install reportlab\nChapters: {[p.name for p in chapter_files]}")
            return out_path
        except Exception as e2:
            print(f"[KDP] Fallback also failed: {e2}")
            import traceback
            traceback.print_exc()
            Path(out_path).write_text(f"Error: {e2}")
            return out_path
