
"""
Book Builder - Writes ENTIRE book in one go
Now per-book: each build creates its own folder book_data/books/{title}/
"""

import json, time
from pathlib import Path
from core.book_bible import BookBible
from core.filenames import format_chapter_id, format_image_id
from core.project_manager import project_manager

class BookBuilder:
    def __init__(self, project_id=None):
        self.project_id = project_id
    
    def build(self, topic, pages=10, title=None, audience="children ages 4-8", character="sarah", word_count_per_page=120, style="watercolor", project_id=None, new_book=True):
        """
        Build entire book in its own folder
        - new_book=True: creates fresh folder book_data/books/my_first_holi/
        - new_book=False: uses existing current project
        """
        # Determine project id - each book gets its own folder
        if project_id:
            pid = project_id
            proj_path = project_manager.get_project_path(pid)
            proj_path.mkdir(parents=True, exist_ok=True)
            project_manager.set_current(pid)
        elif new_book:
            # Create new project from title/topic
            book_title = title or topic.title()
            pid, proj_path = project_manager.create_project(title=book_title, topic=topic, exist_ok=True)
        else:
            pid = project_manager.get_current() or "default_book"
            proj_path = project_manager.get_project_path(pid)
            proj_path.mkdir(parents=True, exist_ok=True)
        
        self.project_id = pid
        
        print(f"\n{'='*60}")
        print(f"📚 BUILDING BOOK: '{title or topic}' in project {pid}")
        print(f"   Path: {proj_path}")
        print(f"   {pages} pages about {topic}")
        print(f"{'='*60}\n")
        
        # Init bible for this project
        bible = BookBible(project_id=pid)
        if title:
            bible.data["title"] = title
        else:
            bible.data["title"] = topic.title()
        bible.data["audience"] = audience
        
        if "holi" in topic.lower():
            bible.data["characters"]["sarah"] = {
                "description": "curious 6-year-old with brown hair, wearing colorful kurta for Holi",
                "outfit": "bright pink kurta with white pants, colorful Holi powder on cheeks",
                "face_refs": []
            }
        bible.save()
        
        # Init writer/director for this project
        from agents.story_writer import StoryWriter
        from agents.image_director import ImageDirector
        writer = StoryWriter(project_id=pid)
        director = ImageDirector(project_id=pid)
        
        # Step 1: Outline
        print(f"\n[Step 1/4] Outline for {pid}...")
        outline = writer.write_outline(num_chapters=pages, premise=f"Children's book about {topic}, {audience}, educational and fun")
        print(f"Outline:\n{outline[:600]}...")
        
        outline_lines = [l.strip() for l in outline.split('\n') if l.strip() and any(c.isdigit() for c in l[:4])]
        if len(outline_lines) < pages:
            outline_lines = [f"Page {i+1}: {topic} - part {i+1}" for i in range(pages)]
        
        # Step 2: Chapters
        print(f"\n[Step 2/4] Writing {pages} pages into {proj_path}/chapters/...")
        chapters = []
        for i in range(pages):
            chapter_id = f"ch{i+1}"
            formatted = format_chapter_id(chapter_id)
            
            if i < len(outline_lines):
                prompt = outline_lines[i][:200]
            else:
                prompt = f"{topic} - page {i+1}"
            
            if "holi" in topic.lower():
                holi_prompts = [
                    "Sarah wakes up excited for Holi, festival of colors, sees colorful powders",
                    "Family prepares gulal - red, yellow, green, pink, mixing",
                    "Sarah wears white kurta, first colors, throwing gentle colors with family",
                    "Friends gather outside, playing Holi with pichkaris, laughter",
                    "Learning why we celebrate Holi - good winning, spring festival",
                    "Delicious Holi foods - gujiya, thandai, sharing sweets",
                    "Everyone covered in colors, no difference, all friends, dancing",
                    "Water balloons, flowers, music, dhol drums, happy songs",
                    "Evening, washing colors, happy tired, family hugs, memories",
                    "Holi teaches sharing joy, love and colors, sleepy ending"
                ]
                if i < len(holi_prompts):
                    prompt = holi_prompts[i]
            
            print(f"  Writing {formatted}: {prompt[:70]}...")
            try:
                story, path = writer.write_chapter(chapter_id, prompt, word_count=word_count_per_page, age_group=audience)
                chapters.append({"id": formatted, "prompt": prompt, "path": str(path)})
                time.sleep(1)
            except Exception as e:
                print(f"  ❌ {formatted}: {e}")
                p = proj_path / f"chapters/{formatted}.txt"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(f"# {formatted}\n\n{prompt}")
                chapters.append({"id": formatted, "prompt": prompt, "path": str(p)})
        
        # Step 3: Images
        print(f"\n[Step 3/4] Generating {pages} images into {proj_path}/images/...")
        images = []
        for i, ch in enumerate(chapters):
            img_id = f"ch{i+1}_01"
            formatted_img = format_image_id(img_id)
            img_prompt = ch["prompt"]
            if "holi" in topic.lower():
                img_prompt = f"{img_prompt}, Holi festival, Indian colors, children playing gulal, joyful"
            
            print(f"  Generating {formatted_img}: {img_prompt[:70]}...")
            try:
                entry = director.generate(formatted_img, img_prompt, character=character, seed=4421 + i)
                images.append({"id": entry["id"], "file": entry["file"]})
                time.sleep(1.5)
            except Exception as e:
                print(f"  ❌ Image {formatted_img}: {e}")
        
        # Step 4: PDF
        print(f"\n[Step 4/4] Exporting PDF...")
        try:
            from exporters.kdp_pdf import export_kdp_pdf
            out = export_kdp_pdf(
                chapters_dir=str(proj_path / "chapters"),
                images_dir=str(proj_path / "images"),
                out_path=str(proj_path / "output" / "kdp_print.pdf"),
                trim="8.5x11",
                page_count_est=pages,
                project_id=pid
            )
        except Exception as e:
            print(f"  PDF note: {e}")
            out = proj_path / "output/kdp_print.pdf"
        
        print(f"\n{'='*60}")
        print(f"✅ BOOK BUILT: {pid}")
        print(f"  Title: {bible.data['title']}")
        print(f"  Path: {proj_path}")
        print(f"  Chapters: {len(chapters)} -> {proj_path}/chapters/ (ch01.txt ...)")
        print(f"  Images: {len(images)} -> {proj_path}/images/")
        print(f"  PDF: {out}")
        print(f"  Previous books NOT overwritten - each in its own folder!")
        print(f"  List books: python cli.py books")
        print(f"{'='*60}\n")
        
        manifest = {
            "id": pid,
            "topic": topic,
            "title": bible.data["title"],
            "pages": pages,
            "audience": audience,
            "character": character,
            "chapters": [c["id"] for c in chapters],
            "images": [img["id"] for img in images],
            "path": str(proj_path),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        (proj_path / "manifest.json").write_text(json.dumps(manifest, indent=2))
        return manifest
