
"""
Filename formatting - Central utility for all agents
Ensures consistent, safe, KDP-friendly filenames
Now supports per-book projects to avoid overwriting!
"""
import re
from pathlib import Path

def sanitize_id(raw_id: str) -> str:
    if not raw_id:
        return "untitled"
    s = str(raw_id).strip().lower()
    s = re.sub(r'[\s/\\:]+', '_', s)
    s = re.sub(r'[^a-z0-9_-]', '', s)
    s = re.sub(r'_+', '_', s)
    s = re.sub(r'-+', '-', s)
    s = s.strip('_-')
    if not s:
        return "untitled"
    return s[:100]

def format_chapter_id(raw_id: str) -> str:
    sanitized = sanitize_id(raw_id)
    m = re.search(r'(\d+)', sanitized)
    if m:
        num = int(m.group(1))
        if 'ch' in sanitized or 'chapter' in sanitized or sanitized.isdigit():
            return f"ch{num:02d}"
        else:
            return f"{sanitized}_{num:02d}" if not sanitized.startswith('ch') else f"ch{num:02d}"
    else:
        if sanitized.startswith('ch'):
            return sanitized
        return sanitized

def format_image_id(raw_id: str, chapter_id: str = None) -> str:
    sanitized = sanitize_id(raw_id)
    if chapter_id and re.match(r'^\d+$', raw_id.strip()):
        ch_formatted = format_chapter_id(chapter_id)
        return f"{ch_formatted}_{int(raw_id.strip()):02d}"
    m = re.match(r'ch(\d+)[_\-](\d+)', sanitized)
    if m:
        ch_num = int(m.group(1))
        img_num = int(m.group(2))
        return f"ch{ch_num:02d}_{img_num:02d}"
    m = re.match(r'ch(\d+)$', sanitized)
    if m:
        return f"ch{int(m.group(1)):02d}"
    if sanitized in ('cover', 'back', 'toc', 'dedication', 'copyright'):
        return sanitized
    return sanitized

def _get_project_base(project_id=None):
    """Get base path - per book if project active, else legacy"""
    try:
        from core.project_manager import project_manager
        proj_path = project_manager.get_project_path(project_id)
        # If legacy book_data (no books subfolder), use legacy
        if proj_path == Path("book_data") and not (Path("book_data/books").exists() and any(Path("book_data/books").iterdir())):
            return Path("book_data")
        # If project exists, use it, else legacy for backward compat
        if proj_path.exists() or project_manager.get_current():
            return proj_path
    except:
        pass
    return Path("book_data")

def format_chapter_filename(chapter_id: str, project_id=None) -> Path:
    formatted = format_chapter_id(chapter_id)
    base = _get_project_base(project_id)
    return base / f"chapters/{formatted}.txt"

def format_chapter_meta_filename(chapter_id: str, project_id=None) -> Path:
    formatted = format_chapter_id(chapter_id)
    base = _get_project_base(project_id)
    return base / f"chapters/{formatted}.json"

def format_image_filename(image_id: str, ext: str = "jpg", project_id=None) -> Path:
    formatted = format_image_id(image_id)
    ext = ext.lstrip('.').lower()
    if ext not in ('jpg', 'jpeg', 'png', 'webp'):
        ext = 'jpg'
    base = _get_project_base(project_id)
    return base / f"images/{formatted}.{ext}"

def format_image_variant_filename(image_id: str, variant_name: str, ext: str = "jpg", project_id=None) -> Path:
    img_formatted = format_image_id(image_id)
    variant_sanitized = sanitize_id(variant_name)
    ext = ext.lstrip('.').lower()
    base = _get_project_base(project_id)
    return base / f"images/{img_formatted}_{variant_sanitized}.{ext}"

def format_outline_filename(project_id=None) -> Path:
    base = _get_project_base(project_id)
    return base / "outline.txt"

def format_book_bible_path(project_id=None) -> Path:
    base = _get_project_base(project_id)
    return base / "book_bible.json"

def format_catalog_path(project_id=None) -> Path:
    base = _get_project_base(project_id)
    return base / "image_catalog.json"
