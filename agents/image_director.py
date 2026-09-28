
from PIL import Image, ImageDraw
from pathlib import Path
from core.image_catalog import ImageCatalog
from core.book_bible import BookBible
from core.models import router
from core.filenames import format_image_id, format_image_filename, format_image_variant_filename, sanitize_id

class ImageDirector:
    def __init__(self, project_id=None):
        self.project_id = project_id
        self.catalog = ImageCatalog(project_id=project_id)
        self.bible = BookBible(project_id=project_id)
        try:
            from core.project_manager import project_manager
            images_dir = project_manager.get_images_dir(project_id)
            images_dir.mkdir(parents=True, exist_ok=True)
            self.images_dir = images_dir
        except:
            Path("book_data/images").mkdir(parents=True, exist_ok=True)
            self.images_dir = Path("book_data/images")
    
    def generate(self, img_id, prompt, character=None, seed=4421, width=1024, height=1024):
        formatted_id = format_image_id(img_id)
        bible_ctx = self.bible.get_prompt_context(character)
        full_prompt = f"{bible_ctx}, SCENE: {prompt}, soft watercolor children's book, no text"
        
        character_refs = []
        if character and character in self.bible.data.get('characters', {}):
            character_refs = self.bible.data['characters'][character].get('face_refs', [])
        
        img = router.image_generate(full_prompt, character_refs=character_refs, seed=seed, width=width, height=height)
        
        file_path = format_image_filename(formatted_id, ext="jpg", project_id=self.project_id)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(file_path, "JPEG", quality=95)
        
        print(f"[ImageDirector] Formatted '{img_id}' -> '{formatted_id}' -> {file_path} (project {self.project_id})")
        return self.catalog.add(formatted_id, full_prompt, file_path, character_refs=[character] if character else [], seed=seed)
    
    def fix(self, img_id, instruction):
        formatted_id = format_image_id(img_id)
        entry = self.catalog.get(formatted_id)
        if not entry:
            entry = self.catalog.get(img_id)
            if not entry:
                print(f"[ERR] {img_id} (formatted: {formatted_id}) not found")
                return None
            formatted_id = entry['id']
        
        if entry['locked']:
            print(f"[BLOCKED] Image {formatted_id} is LOCKED - cannot modify.")
            return entry
        
        src_path = Path(entry['file'])
        mask_path = src_path.parent / f"{formatted_id}_mask.png"
        mask = Image.new('L', Image.open(src_path).size, 0)
        draw = ImageDraw.Draw(mask)
        w,h = mask.size
        draw.ellipse([w*0.3, h*0.2, w*0.7, h*0.6], fill=255)
        mask.save(mask_path)
        
        fixed_img = router.image_inpaint(src_path, mask_path, instruction, seed=entry['seed'])
        fixed_img.save(src_path, "JPEG", quality=95)
        print(f"[ImageDirector] Inpainted fix on {formatted_id}: {instruction}")
        return entry
    
    def resize_or_regen(self, img_id, target_name, target_w, target_h, mode="auto"):
        formatted_id = format_image_id(img_id)
        entry = self.catalog.get(formatted_id)
        if not entry:
            entry = self.catalog.get(img_id)
            if not entry:
                print(f"[ERR] {img_id} not found")
                return None
            formatted_id = entry['id']
        
        src_path = Path(entry['file'])
        src_img = Image.open(src_path)
        src_w, src_h = src_img.size
        src_ratio = src_w / src_h
        target_ratio = target_w / target_h
        ratio_diff = abs(src_ratio - target_ratio) / max(src_ratio, target_ratio)
        
        if mode == "auto":
            if ratio_diff < 0.15:
                mode = "outpaint" if "full" in target_name or "bleed" in target_name else "upscale"
            else:
                mode = "regen_full"
        
        if mode == "upscale":
            new_img = router.image_upscale(src_path, target_w, target_h)
            method = "upscale"
        elif mode == "outpaint":
            new_img = router.image_outpaint(src_path, target_w, target_h, entry['prompt'])
            method = "outpaint"
        else:
            bible_ctx = self.bible.get_prompt_context(entry['character_refs'][0] if entry['character_refs'] else None)
            regen_prompt = f"{bible_ctx}, {entry['prompt']}, full page illustration, portrait {target_w}x{target_h}, same character"
            new_img = router.image_generate(regen_prompt, character_refs=entry['character_refs'], seed=entry['seed'], width=target_w, height=target_h)
            method = "regen"
        
        variant_path = format_image_variant_filename(formatted_id, target_name, ext="jpg", project_id=self.project_id)
        variant_path.parent.mkdir(parents=True, exist_ok=True)
        new_img.save(variant_path, "JPEG", quality=95)
        self.catalog.add_variant(formatted_id, sanitize_id(target_name), variant_path, method)
        print(f"[ImageDirector] Created variant {target_name} -> {variant_path}")
        return variant_path
