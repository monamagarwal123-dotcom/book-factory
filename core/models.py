import os
from pathlib import Path
from PIL import Image

class ModelRouter:
    def __init__(self):
        self.replicate_token = os.getenv('REPLICATE_API_TOKEN')
        self.meta_ai_enabled = os.getenv('USE_META_AI', 'true').lower() == 'true'
        self.use_real = bool(self.replicate_token) or self.meta_ai_enabled
        self.use_meta_ai = self.meta_ai_enabled
        if self.use_meta_ai:
            try:
                from core.meta_provider import meta_provider
                self.meta_provider = meta_provider
            except:
                self.meta_provider = None
        else:
            self.meta_provider = None
    def image_generate(self, prompt, character_refs=None, seed=4421, width=1024, height=1024):
        if self.use_meta_ai and self.meta_provider:
            try:
                result = self.meta_provider.generate(prompt, character_refs, seed, width, height)
                if isinstance(result, dict) and result.get('status') == 'ready_for_generation':
                    return self._placeholder_image(f'[META AI] {prompt}', seed, width, height, character_refs, provider='meta_ai')
            except Exception as e:
                print(f'Meta AI failed: {e}')
        if self.use_real and self.replicate_token:
            try:
                import replicate
                output = replicate.run('black-forest-labs/flux-1.1-pro', input={'prompt': prompt, 'seed': seed, 'width': width, 'height': height})
                return self._download_image(output, prompt)
            except Exception as e:
                print(f'Real gen failed: {e}')
        return self._placeholder_image(prompt, seed, width, height, character_refs)
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
    def _download_image(self, url_or_path, prompt):
        import requests, tempfile
        if isinstance(url_or_path, str) and url_or_path.startswith('http'):
            r = requests.get(url_or_path)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            tmp.write(r.content)
            tmp.close()
            return Image.open(tmp.name)
        return Image.open(url_or_path)
    def _placeholder_image(self, prompt, seed, width, height, refs, provider='placeholder'):
        from PIL import ImageDraw
        bg = (240,230,255) if provider=='meta_ai' else (255,245,225)
        img = Image.new('RGB', (width, height), color=bg)
        d = ImageDraw.Draw(img)
        d.text((20,20), f'{provider}: {prompt[:80]}', fill=(80,60,40))
        return img
router = ModelRouter()
