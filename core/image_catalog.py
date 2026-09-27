import json, os
from pathlib import Path
from datetime import datetime

CATALOG_PATH = Path("book_data/image_catalog.json")

class ImageCatalog:
    def __init__(self, path=CATALOG_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            self.data = json.loads(self.path.read_text())
        else:
            self.data = {"images": {}}
    
    def save(self):
        self.path.write_text(json.dumps(self.data, indent=2))
    
    def add(self, img_id, prompt, file_path, character_refs=None, seed=None):
        self.data["images"][img_id] = {
            "id": img_id,
            "prompt": prompt,
            "file": str(file_path),
            "character_refs": character_refs or [],
            "seed": seed or 4421,
            "locked": False,
            "alt_text": "",
            "variants": {},
            "created_at": datetime.now().isoformat(),
            "status": "candidate"
        }
        self.save()
        return self.data["images"][img_id]
    
    def lock(self, img_id):
        if img_id in self.data["images"]:
            self.data["images"][img_id]["locked"] = True
            self.data["images"][img_id]["status"] = "approved"
            self.save()
            return True
        return False
    
    def unlock(self, img_id):
        if img_id in self.data["images"]:
            self.data["images"][img_id]["locked"] = False
            self.data["images"][img_id]["status"] = "candidate"
            self.save()
            return True
        return False
    
    def set_alt(self, img_id, alt_text):
        if img_id in self.data["images"]:
            self.data["images"][img_id]["alt_text"] = alt_text
            self.save()
            return True
        return False
    
    def get(self, img_id):
        return self.data["images"].get(img_id)
    
    def list(self):
        return list(self.data["images"].values())
    
    def add_variant(self, img_id, variant_type, file_path, method):
        if img_id in self.data["images"]:
            self.data["images"][img_id]["variants"][variant_type] = {
                "file": str(file_path),
                "method": method,
                "created_at": datetime.now().isoformat()
            }
            self.save()
