
import json
from pathlib import Path
from datetime import datetime
from core.filenames import sanitize_id

BOOKS_ROOT = Path("book_data/books")
CURRENT_PROJECT_FILE = Path("book_data/current_project.txt")
BOOKS_INDEX_FILE = Path("book_data/books_index.json")

class ProjectManager:
    def __init__(self):
        BOOKS_ROOT.mkdir(parents=True, exist_ok=True)
        self._current = None
        if CURRENT_PROJECT_FILE.exists():
            try:
                self._current = CURRENT_PROJECT_FILE.read_text().strip()
            except:
                pass
    
    def create_project(self, title, topic=None, exist_ok=True):
        project_id = sanitize_id(title or topic or "untitled_book")[:50]
        base_id = project_id
        counter = 2
        while (BOOKS_ROOT / project_id).exists() and not exist_ok:
            project_id = f"{base_id}_{counter}"
            counter += 1
        project_path = BOOKS_ROOT / project_id
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / "chapters").mkdir(exist_ok=True)
        (project_path / "images").mkdir(exist_ok=True)
        (project_path / "output").mkdir(exist_ok=True)
        self.set_current(project_id)
        self._update_index(project_id, title, topic)
        print(f"[Project] Created {project_id} -> {project_path}")
        return project_id, project_path
    
    def set_current(self, project_id):
        self._current = project_id
        CURRENT_PROJECT_FILE.parent.mkdir(parents=True, exist_ok=True)
        CURRENT_PROJECT_FILE.write_text(project_id)
        print(f"[Project] Current -> {project_id}")
    
    def get_current(self):
        if self._current and (BOOKS_ROOT / self._current).exists():
            return self._current
        if CURRENT_PROJECT_FILE.exists():
            try:
                cid = CURRENT_PROJECT_FILE.read_text().strip()
                if cid and (BOOKS_ROOT / cid).exists():
                    self._current = cid
                    return cid
            except:
                pass
        if BOOKS_INDEX_FILE.exists():
            try:
                data = json.loads(BOOKS_INDEX_FILE.read_text())
                if data.get("books"):
                    last = sorted(data["books"], key=lambda x: x.get("created_at",""), reverse=True)[0]
                    pid = last["id"]
                    if (BOOKS_ROOT / pid).exists():
                        return pid
            except:
                pass
        try:
            books = [d for d in BOOKS_ROOT.iterdir() if d.is_dir()]
            if books:
                newest = sorted(books, key=lambda d: d.stat().st_mtime, reverse=True)[0]
                return newest.name
        except:
            pass
        return None
    
    def get_project_path(self, project_id=None):
        pid = project_id or self.get_current()
        if not pid:
            return Path("book_data")
        return BOOKS_ROOT / pid
    
    def get_chapters_dir(self, project_id=None):
        return self.get_project_path(project_id) / "chapters"
    
    def get_images_dir(self, project_id=None):
        return self.get_project_path(project_id) / "images"
    
    def get_output_dir(self, project_id=None):
        return self.get_project_path(project_id) / "output"
    
    def list_books(self):
        books_by_id = {}
        if BOOKS_ROOT.exists():
            for folder in BOOKS_ROOT.iterdir():
                if not folder.is_dir():
                    continue
                pid = folder.name
                title = pid.replace('_',' ').title()
                topic = title
                created_at = datetime.fromtimestamp(folder.stat().st_mtime).isoformat()
                manifest_path = folder / "manifest.json"
                if manifest_path.exists():
                    try:
                        mdata = json.loads(manifest_path.read_text())
                        title = mdata.get("title", title)
                        topic = mdata.get("topic", topic)
                        created_at = mdata.get("created_at", created_at)
                    except:
                        pass
                else:
                    bible_path = folder / "book_bible.json"
                    if bible_path.exists():
                        try:
                            bdata = json.loads(bible_path.read_text())
                            title = bdata.get("title", title)
                        except:
                            pass
                books_by_id[pid] = {
                    "id": pid,
                    "title": title,
                    "topic": topic,
                    "created_at": created_at,
                    "path": str(folder),
                    "chapters": len(list((folder / "chapters").glob("*.txt"))) if (folder / "chapters").exists() else 0
                }
        legacy_ch = Path("book_data/chapters")
        if legacy_ch.exists() and any(legacy_ch.glob("*.txt")) and not books_by_id:
            books_by_id["legacy"] = {
                "id": "legacy",
                "title": "Legacy Book (book_data/)",
                "topic": "legacy",
                "created_at": datetime.fromtimestamp(legacy_ch.stat().st_mtime).isoformat(),
                "path": str(Path("book_data")),
                "chapters": len(list(legacy_ch.glob("*.txt")))
            }
        return list(books_by_id.values())
    
    def _update_index(self, project_id, title, topic):
        books = self.list_books()
        # Ensure not duplicate
        books = [b for b in books if b["id"] != project_id]
        books.append({
            "id": project_id,
            "title": title or project_id,
            "topic": topic or title or project_id,
            "created_at": datetime.now().isoformat(),
            "path": str(self.get_project_path(project_id))
        })
        BOOKS_ROOT.mkdir(parents=True, exist_ok=True)
        try:
            BOOKS_INDEX_FILE.write_text(json.dumps({"books": books}, indent=2))
        except:
            pass

project_manager = ProjectManager()
