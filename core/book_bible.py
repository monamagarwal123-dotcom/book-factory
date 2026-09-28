
import json
from pathlib import Path

try:
    from core.filenames import format_book_bible_path
    def get_bible_path(project_id=None):
        return format_book_bible_path(project_id)
except:
    def get_bible_path(project_id=None):
        return Path("book_data/book_bible.json")

DEFAULT_BIBLE = {
    "title": "Untitled Book",
    "author": "Monam Agarwal",
    "audience": "general",
    "art_style": "soft watercolor, children's book illustration, warm light",
    "characters": {
        "sarah": {
            "description": "8-year-old girl, curly brown hair, blue dress",
            "face_refs": [],
            "outfit": "blue dress"
        }
    },
    "style_guide": {
        "tone": "warm, curious",
        "sentence_length": "short"
    }
}

class BookBible:
    def __init__(self, path=None, project_id=None):
        if path:
            self.path = Path(path)
        else:
            self.path = get_bible_path(project_id)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text())
            except:
                self.data = DEFAULT_BIBLE.copy()
                self.save()
        else:
            self.data = DEFAULT_BIBLE.copy()
            self.save()
    
    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2))
    
    def get_prompt_context(self, character_name=None):
        ctx = f"STYLE: {self.data['art_style']}"
        if character_name and character_name in self.data['characters']:
            c = self.data['characters'][character_name]
            ctx += f", CHARACTER: {c['description']}"
        return ctx
