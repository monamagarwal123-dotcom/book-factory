
import argparse
from pathlib import Path
from agents.image_director import ImageDirector
from core.image_catalog import ImageCatalog
from core.book_bible import BookBible
from core.filenames import format_chapter_id, format_chapter_filename, format_image_id

def cmd_init(args):
    from core.project_manager import project_manager
    # If --book provided, init that book
    if args.book:
        pid, path = project_manager.create_project(title=args.title, topic=args.title, exist_ok=True)
        bible = BookBible(project_id=pid)
        bible.data["title"] = args.title
        if args.audience:
            bible.data["audience"] = args.audience
        bible.save()
        ch01_path = path / "chapters" / "ch01.txt"
        if not ch01_path.exists():
            ch01_path.write_text(f"# {args.title}\n\nChapter 1 content here...")
        print(f"[OK] Initialized book {pid}: {args.title} in {path}")
    else:
        Path("book_data/chapters").mkdir(parents=True, exist_ok=True)
        Path("book_data/images").mkdir(parents=True, exist_ok=True)
        Path("book_data/output").mkdir(parents=True, exist_ok=True)
        bible = BookBible()
        bible.data["title"] = args.title
        if args.audience:
            bible.data["audience"] = args.audience
        bible.save()
        ch01_path = format_chapter_filename("ch01")
        if not ch01_path.exists():
            ch01_path.write_text(f"# {args.title}\n\nChapter 1 content here...")
        print(f"[OK] Initialized book: {args.title} in book_data/")

def cmd_write(args):
    from agents.story_writer import StoryWriter
    from core.project_manager import project_manager
    proj = args.book or project_manager.get_current()
    writer = StoryWriter(project_id=proj)
    if args.outline:
        outline = writer.write_outline(num_chapters=args.chapters, premise=args.prompt)
        print(f"[OK] Outline:\n{outline[:500]}...")
    else:
        story, path = writer.write_chapter(args.chapter_id, args.prompt, word_count=args.words, age_group=args.age)
        print(f"[OK] Wrote {args.chapter_id} -> {path}")

def cmd_gen(args):
    from core.project_manager import project_manager
    proj = getattr(args, 'book', None) or project_manager.get_current()
    director = ImageDirector(project_id=proj)
    entry = director.generate(args.img_id, args.prompt, args.character, args.seed)
    print(f"[OK] Generated {args.img_id} -> {entry['file']}")

def cmd_fix(args):
    from core.project_manager import project_manager
    proj = getattr(args, 'book', None) or project_manager.get_current()
    director = ImageDirector(project_id=proj)
    result = director.fix(args.img_id, args.instruction)
    if result:
        print(f"[OK] Fixed {args.img_id}: {args.instruction}")

def cmd_lock(args):
    from core.project_manager import project_manager
    proj = getattr(args, 'book', None) or project_manager.get_current()
    cat = ImageCatalog(project_id=proj)
    formatted = format_image_id(args.img_id)
    if cat.lock(formatted) or cat.lock(args.img_id):
        print(f"[OK] Locked {formatted}")
    else:
        print(f"[ERR] {args.img_id} not found")

def cmd_unlock(args):
    from core.project_manager import project_manager
    proj = getattr(args, 'book', None) or project_manager.get_current()
    cat = ImageCatalog(project_id=proj)
    formatted = format_image_id(args.img_id)
    if cat.unlock(formatted) or cat.unlock(args.img_id):
        print(f"[OK] Unlocked {formatted}")

def cmd_alt(args):
    from core.project_manager import project_manager
    proj = getattr(args, 'book', None) or project_manager.get_current()
    cat = ImageCatalog(project_id=proj)
    formatted = format_image_id(args.img_id)
    if cat.set_alt(formatted, args.text) or cat.set_alt(args.img_id, args.text):
        print(f"[OK] Alt set for {formatted}")

def cmd_list(args):
    from core.project_manager import project_manager
    proj = args.book or project_manager.get_current()
    if proj:
        print(f"\n=== Book: {proj} ===")
        base = project_manager.get_project_path(proj)
        chapters_dir = base / "chapters"
        images_dir = base / "images"
    else:
        print("\n=== Legacy book_data (no project) ===")
        chapters_dir = Path("book_data/chapters")
        images_dir = Path("book_data/images")
        base = Path("book_data")
    try:
        cat = ImageCatalog(project_id=proj)
        print("\n=== Image Catalog ===")
        for img in cat.list():
            lock = "🔒" if img['locked'] else "🔓"
            print(f"{lock} {img['id']} | status={img['status']} | file={img['file']}")
    except Exception as e:
        print(f"No catalog: {e}")
    print(f"\n=== Chapters in {chapters_dir} ===")
    if chapters_dir.exists():
        for f in sorted(chapters_dir.glob("ch*.txt")):
            try:
                words = len(f.read_text().split())
                print(f"📄 {f.stem} | {words} words | {f}")
            except Exception as e:
                print(f"📄 {f.stem} | error: {e}")
    else:
        print(f"No chapters dir: {chapters_dir}")
    print(f"\nTip: python cli.py books to see all books")

def cmd_resize(args):
    from core.project_manager import project_manager
    proj = getattr(args, 'book', None) or project_manager.get_current()
    director = ImageDirector(project_id=proj)
    path = director.resize_or_regen(args.img_id, args.target, args.width, args.height, args.mode)
    if path:
        print(f"[OK] Created {args.target} -> {path}")

def cmd_books(args):
    from core.project_manager import project_manager
    books = project_manager.list_books()
    current = project_manager.get_current()
    print("\n=== Your Books (each in own folder - no overwriting!) ===")
    print(f"Scanning: book_data/books/")
    if not books:
        legacy_ch = Path("book_data/chapters")
        if legacy_ch.exists() and list(legacy_ch.glob("*.txt")):
            print(f"Found legacy book in book_data/chapters/: {len(list(legacy_ch.glob('*.txt')))} chapters")
            print(f"Run: python cli.py migrate --title 'My Holi Book' to move to per-book folder")
        else:
            print("No books yet. Try: python cli.py chat \"write me a book about holi 10 pages\"")
        if Path("book_data/books").exists():
            folders = list(Path("book_data/books").iterdir())
            print(f"\nDebug: book_data/books/ contains {len(folders)} items: {[f.name for f in folders[:10]]}")
        else:
            print("\nDebug: book_data/books/ does not exist yet - will be created on first build")
        return
    for b in sorted(books, key=lambda x: x.get("created_at", ""), reverse=True):
        marker = "👉 CURRENT" if b["id"] == current else "  "
        ch_dir = Path(b["path"]) / "chapters"
        img_dir = Path(b["path"]) / "images"
        if b["id"] == "legacy":
            ch_dir = Path("book_data/chapters")
            img_dir = Path("book_data/images")
        ch_count = len(list(ch_dir.glob("ch*.txt"))) if ch_dir.exists() else 0
        img_count = len(list(img_dir.glob("*.jpg"))) if img_dir.exists() else 0
        print(f"{marker} {b['id']} | {b['title']} | {ch_count} ch | {img_count} img | {b['path']}")
    print(f"\nCurrent: {current}")
    print(f"Total: {len(books)} books")

def cmd_use(args):
    from core.project_manager import project_manager
    if not args.book_id:
        print("Usage: python cli.py use <book_id>")
        return
    project_manager.set_current(args.book_id)
    print(f"✅ Now using {args.book_id}")

def cmd_kdp(args):
    try:
        from exporters.kdp_pdf import export_kdp_pdf, calculate_margins
        from core.project_manager import project_manager
        margins = calculate_margins(args.pages)
        print(f"Margins for {args.pages} pages: {margins}")
        proj = args.book or project_manager.get_current()
        # FIXED: export_kdp_pdf now accepts project_id - ensure we call correctly
        out = export_kdp_pdf(trim=args.trim, page_count_est=args.pages, project_id=proj)
        print(f"[OK] KDP PDF ready: {out}")
    except TypeError as e:
        # Fallback if old kdp_pdf without project_id is still installed locally
        print(f"[KDP] TypeError (old kdp_pdf?): {e}")
        print(f"[KDP] Trying without project_id...")
        try:
            from exporters.kdp_pdf import export_kdp_pdf
            # Try old signature with explicit dirs
            from core.project_manager import project_manager
            proj = args.book or project_manager.get_current()
            if proj:
                base = project_manager.get_project_path(proj)
                out = export_kdp_pdf(
                    chapters_dir=str(base / "chapters"),
                    images_dir=str(base / "images"),
                    out_path=str(base / "output" / "kdp_print.pdf"),
                    trim=args.trim,
                    page_count_est=args.pages
                )
            else:
                out = export_kdp_pdf(trim=args.trim, page_count_est=args.pages)
            print(f"[OK] KDP PDF ready (fallback): {out}")
        except Exception as e2:
            print(f"[KDP] Fallback also failed: {e2}")
            import traceback
            traceback.print_exc()
    except Exception as e:
        print(f"[KDP] Error: {e}")
        import traceback
        traceback.print_exc()

def cmd_build(args):
    from agents.book_builder import BookBuilder
    builder = BookBuilder()
    builder.build(
        topic=args.topic,
        pages=args.pages,
        title=args.title,
        audience=args.audience,
        character=args.character,
        word_count_per_page=args.words,
        style=args.style
    )

def cmd_chat(args):
    from agents.chat_agent import ChatAgent
    agent = ChatAgent()
    if args.message:
        agent.chat(args.message)
    else:
        print("\n🤖 Book Factory Chat - Just say what you want!")
        print("Examples:")
        print("  'write me a book about holi 10 pages with images'")
        print("  'make a diwali book for kids 5 pages'")
        print("Type 'quit' to exit\n")
        while True:
            try:
                msg = input("You: ").strip()
                if not msg:
                    continue
                if msg.lower() in ('quit', 'exit', 'q'):
                    print("Bye! 📚")
                    break
                agent.chat(msg)
                print("\n--- Ready for next book! ---\n")
            except KeyboardInterrupt:
                print("\nBye! 📚")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def cmd_models(args):
    from core.config import config
    text_key, text_cfg = config.get_text_model()
    image_key, image_cfg = config.get_image_model()
    print("\n=== Current Models (from config.yaml) ===")
    print(f"Text:  {text_key} -> {text_cfg}")
    print(f"Image: {image_key} -> {image_cfg}")
    print("\nTo switch: Edit config.yaml models.text.default or models.image.default")

def cmd_migrate(args):
    from core.project_manager import project_manager
    import shutil, json
    legacy_ch = Path("book_data/chapters")
    legacy_img = Path("book_data/images")
    legacy_bible = Path("book_data/book_bible.json")
    if not legacy_ch.exists() or not any(legacy_ch.glob("*.txt")):
        print("No legacy chapters found in book_data/chapters/")
        print(f"Current books: {project_manager.list_books()}")
        return
    title = args.title or "Migrated Book"
    if legacy_bible.exists():
        try:
            data = json.loads(legacy_bible.read_text())
            title = data.get("title", title)
        except:
            pass
    pid, proj_path = project_manager.create_project(title=title, topic=title, exist_ok=True)
    print(f"Migrating legacy -> {pid} at {proj_path}")
    for f in legacy_ch.glob("*"):
        if f.is_file():
            dest = proj_path / "chapters" / f.name
            if not dest.exists():
                shutil.copy2(f, dest)
                print(f"  Copied chapter {f.name}")
    if legacy_img.exists():
        for f in legacy_img.glob("*.jpg"):
            dest = proj_path / "images" / f.name
            if not dest.exists():
                shutil.copy2(f, dest)
                print(f"  Copied image {f.name}")
    if legacy_bible.exists():
        shutil.copy2(legacy_bible, proj_path / "book_bible.json")
    legacy_catalog = Path("book_data/image_catalog.json")
    if legacy_catalog.exists():
        shutil.copy2(legacy_catalog, proj_path / "image_catalog.json")
    print(f"\n✅ Migrated legacy -> {pid}")
    print(f"   Now run: python cli.py use {pid} && python cli.py kdp")

def cmd_clean(args):
    from core.filenames import format_chapter_id, format_image_id
    from pathlib import Path
    chapters_dir = Path("book_data/chapters")
    images_dir = Path("book_data/images")
    print("=== Cleaning old filename formats ===")
    migrated = 0
    if chapters_dir.exists():
        for f in chapters_dir.glob("*.txt"):
            formatted_id = format_chapter_id(f.stem)
            formatted_path = chapters_dir / f"{formatted_id}.txt"
            if f.stem != formatted_id and not formatted_path.exists():
                print(f"  Renaming {f.name} -> {formatted_path.name}")
                if not args.dry_run:
                    f.rename(formatted_path)
                migrated += 1
    print(f"\n[OK] Cleaned {migrated} files.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Book Factory CLI v0.2 - Easy model switching!")
    sub = parser.add_subparsers(dest="cmd")
    
    p = sub.add_parser("init")
    p.add_argument("--title", default="My Book")
    p.add_argument("--audience", default="children ages 4-8")
    p.add_argument("--book", default=None, help="Book id, creates per-book folder if set")
    p.set_defaults(func=cmd_init)
    
    p = sub.add_parser("write")
    p.add_argument("chapter_id", nargs="?", default="ch1")
    p.add_argument("prompt", nargs="?", default="Sarah finds magic seed")
    p.add_argument("--words", type=int, default=300)
    p.add_argument("--age", default="4-8")
    p.add_argument("--outline", action="store_true")
    p.add_argument("--chapters", type=int, default=5)
    p.add_argument("--book", default=None)
    p.set_defaults(func=cmd_write)
    
    p = sub.add_parser("gen")
    p.add_argument("img_id")
    p.add_argument("prompt")
    p.add_argument("--character", default="sarah")
    p.add_argument("--seed", type=int, default=4421)
    p.add_argument("--book", default=None)
    p.set_defaults(func=cmd_gen)
    
    p = sub.add_parser("fix")
    p.add_argument("img_id")
    p.add_argument("instruction")
    p.add_argument("--book", default=None)
    p.set_defaults(func=cmd_fix)
    
    p = sub.add_parser("lock")
    p.add_argument("img_id")
    p.add_argument("--book", default=None)
    p.set_defaults(func=cmd_lock)
    
    p = sub.add_parser("unlock")
    p.add_argument("img_id")
    p.add_argument("--book", default=None)
    p.set_defaults(func=cmd_unlock)
    
    p = sub.add_parser("alt")
    p.add_argument("img_id")
    p.add_argument("text")
    p.add_argument("--book", default=None)
    p.set_defaults(func=cmd_alt)
    
    p = sub.add_parser("list")
    p.add_argument("--book", default=None, help="Book id, defaults to current")
    p.set_defaults(func=cmd_list)
    
    p = sub.add_parser("resize")
    p.add_argument("img_id")
    p.add_argument("--target", default="full_bleed_6x9")
    p.add_argument("--width", type=int, default=1875)
    p.add_argument("--height", type=int, default=2775)
    p.add_argument("--mode", default="auto")
    p.add_argument("--book", default=None)
    p.set_defaults(func=cmd_resize)
    
    p = sub.add_parser("kdp")
    p.add_argument("--trim", default="6x9")
    p.add_argument("--pages", type=int, default=200)
    p.add_argument("--book", default=None, help="Book id, defaults to current")
    p.set_defaults(func=cmd_kdp)
    
    p = sub.add_parser("chat")
    p.add_argument("message", nargs="*", help="Natural language request")
    p.set_defaults(func=lambda args: cmd_chat(type("obj", (), {"message": " ".join(args.message) if args.message else None})()))
    
    p = sub.add_parser("build")
    p.add_argument("--topic", default="Holi festival")
    p.add_argument("--pages", type=int, default=10)
    p.add_argument("--title", default=None)
    p.add_argument("--audience", default="children ages 4-8")
    p.add_argument("--character", default="sarah")
    p.add_argument("--words", type=int, default=120)
    p.add_argument("--style", default="watercolor")
    p.set_defaults(func=cmd_build)
    
    p = sub.add_parser("books")
    p.set_defaults(func=cmd_books)
    
    p = sub.add_parser("use")
    p.add_argument("book_id", help="Book id from books list")
    p.set_defaults(func=cmd_use)
    
    p = sub.add_parser("migrate")
    p.add_argument("--title", default=None, help="Title for migrated book")
    p.set_defaults(func=cmd_migrate)
    
    p = sub.add_parser("models")
    p.set_defaults(func=cmd_models)
    
    p = sub.add_parser("clean")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_clean)
    
    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
