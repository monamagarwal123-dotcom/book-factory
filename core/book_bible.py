import json
from pathlib import Path

BIBLE_PATH = Path("book_data/book_bible.json")

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
    def __init__(self, path=BIBLE_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            self.data = json.loads(self.path.read_text())
        else:
            self.data = DEFAULT_BIBLE.copy()
            self.save()
    
    def save(self):
        self.path.write_text(json.dumps(self.data, indent=2))
    
    def get_prompt_context(self, character_name=None):
        ctx = f"STYLE: {self.data['art_style']}"
        if character_name and character_name in self.data['characters']:
            c = self.data['characters'][character_name]
            ctx += f", CHARACTER: {c['description']}"
        return ctx
