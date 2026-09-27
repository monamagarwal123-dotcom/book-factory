from PIL import Image, ImageDraw
from pathlib import Path
from core.image_catalog import ImageCatalog
from core.book_bible import BookBible
from core.models import router

class ImageDirector:
    def __init__(self):
        self.catalog = ImageCatalog()
        self.bible = BookBible()
        Path("book_data/images").mkdir(parents=True, exist_ok=True)
    
    def generate(self, img_id, prompt, character=None, seed=4421, width=1024, height=1024):
        bible_ctx = self.bible.get_prompt_context(character)
        full_prompt = f"{bible_ctx}, SCENE: {prompt}, soft watercolor children's book, no text"
        
        character_refs = []
        if character and character in self.bible.data.get('characters', {}):
            character_refs = self.bible.data['characters'][character].get('face_refs', [])
        
        # Use router - real Flux if token, else placeholder
        img = router.image_generate(full_prompt, character_refs=character_refs, seed=seed, width=width, height=height)
        
        file_path = Path(f"book_data/images/{img_id}.jpg")
        img.save(file_path, "JPEG", quality=95)
        
        return self.catalog.add(img_id, full_prompt, file_path, character_refs=[character] if character else [], seed=seed)
    
    def fix(self, img_id, instruction):
        """Inpaint fix - respects lock"""
        entry = self.catalog.get(img_id)
        if not entry:
            print(f"[ERR] {img_id} not found")
            return None
        if entry['locked']:
            print(f"[BLOCKED] Image {img_id} is LOCKED 🔒 - cannot modify. Unlock first or create variant.")
            return entry
        
        src_path = Path(entry['file'])
        # Create dummy mask for face area (in real: use SAM to segment face)
        mask_path = Path(f"book_data/images/{img_id}_mask.png")
        mask = Image.new('L', Image.open(src_path).size, 0)
        # Simulate face mask in center
        draw = ImageDraw.Draw(mask)
        w,h = mask.size
        draw.ellipse([w*0.3, h*0.2, w*0.7, h*0.6], fill=255)
        mask.save(mask_path)
        
        # Router inpaint
        fixed_img = router.image_inpaint(src_path, mask_path, instruction, seed=entry['seed'])
        fixed_img.save(src_path, "JPEG", quality=95)
        print(f"[ImageDirector] Inpainted fix on {img_id}: {instruction} (identity preserved via mask + seed {entry['seed']})")
        return entry
    
    def resize_or_regen(self, img_id, target_name, target_w, target_h, mode="auto"):
        entry = self.catalog.get(img_id)
        if not entry:
            return None
        
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
        
        print(f"[ImageDirector] {img_id} {src_w}x{src_h} ({src_ratio:.2f}) -> {target_w}x{target_h} ({target_ratio:.2f}) diff {ratio_diff:.2f} -> {mode}")
        
        if mode == "upscale":
            new_img = router.image_upscale(src_path, target_w, target_h)
            method = "upscale_real_esrgan" if router.use_real else "upscale_lanczos"
        elif mode == "outpaint":
            new_img = router.image_outpaint(src_path, target_w, target_h, entry['prompt'])
            method = "outpaint_sdxl" if router.use_real else "outpaint_extend"
        else:  # regen_full - same identity, new composition
            bible_ctx = self.bible.get_prompt_context(entry['character_refs'][0] if entry['character_refs'] else None)
            regen_prompt = f"{bible_ctx}, {entry['prompt']}, full page illustration, portrait {target_w}x{target_h}, same character"
            new_img = router.image_generate(regen_prompt, character_refs=entry['character_refs'], seed=entry['seed'], width=target_w, height=target_h)
            method = "regen_with_refs_ip_adapter" if router.use_real else "regen_with_refs_placeholder"
        
        variant_path = Path(f"book_data/images/{img_id}_{target_name}.jpg")
        new_img.save(variant_path, "JPEG", quality=95)
        self.catalog.add_variant(img_id, target_name, variant_path, method)
        print(f"[ImageDirector] Created variant {target_name} -> {variant_path} via {method} (no stretch)")
        return variant_path
