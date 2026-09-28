"""
Unified Model Router - Uses central config.yaml
- Change ONE line in config.yaml to switch ALL agents!
- Image: models.image.default
- Text: models.text.default

All agents (ImageDirector, StoryWriter, etc) use this router
"""
import os
from pathlib import Path
from PIL import Image

class ModelRouter:
    def __init__(self):
        from core.config import config
        self.config = config
        self.image_model_key, self.image_model_cfg = config.get_image_model()
        self.text_model_key, self.text_model_cfg = config.get_text_model()
        
        print(f"[ModelRouter] Image: {self.image_model_key} -> {self.image_model_cfg.get('provider')}")
        print(f"[ModelRouter] Text: {self.text_model_key} -> {self.text_model_cfg.get('provider')}")
        
        # Load providers
        try:
            from core.meta_provider import meta_provider
            self.meta_provider = meta_provider
        except Exception as e:
            print(f"[ModelRouter] Meta provider import failed: {e}")
            self.meta_provider = None
        
        try:
            from core.llm_router import llm_router
            self.llm_router = llm_router
        except Exception as e:
            print(f"[ModelRouter] LLM router import failed: {e}")
            self.llm_router = None

    def image_generate(self, prompt, character_refs=None, seed=4421, width=1024, height=1024):
        """Image generation - uses central config"""
        if self.meta_provider:
            img = self.meta_provider.generate(prompt, character_refs, seed, width, height)
            if isinstance(img, Image.Image):
                return img
        return self._placeholder_image(prompt, seed, width, height, character_refs)

    def text_generate(self, prompt, system=None, max_tokens=2000, temperature=0.7):
        """Text generation - uses central config - NEW for StoryWriter"""
        if self.llm_router:
            return self.llm_router.generate(prompt, system, max_tokens, temperature)
        return f"[Placeholder - {self.text_model_key}] {prompt[:200]}"

    def image_inpaint(self, image_path, mask_path, prompt, seed=4421):
        img = Image.open(image_path)
        return img

    def image_outpaint(self, image_path, target_w, target_h, prompt):
        src = Image.open(image_path)
        new_img = Image.new('RGB', (target_w, target_h), (255,245,225))
        new_img.paste(src, ((target_w - src.size[0])//2, (target_h - src.size[1])//2))
        return new_img

    def image_upscale(self, image_path, target_w, target_h):
        img = Image.open(image_path)
        return img.resize((target_w, target_h), Image.LANCZOS)

    def _placeholder_image(self, prompt, seed, width, height, refs, provider='placeholder'):
        from PIL import ImageDraw
        img = Image.new('RGB', (width, height), color=(255, 245, 225))
        d = ImageDraw.Draw(img)
        d.text((20,20), f'{self.image_model_key}: {prompt[:60]}...', fill=(80,60,40))
        return img

router = ModelRouter()
