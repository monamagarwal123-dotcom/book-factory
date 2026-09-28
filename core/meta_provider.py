"""
HYBRID PROVIDER - Uses central config.yaml for easy switching
- Reads models.image.default - change ONE line to switch all image agents!
- FREE first (Pollinations) then paid fallback
"""
import os, traceback, time, random
os.environ["PYTHONWARNINGS"] = "ignore"
import warnings
warnings.filterwarnings("ignore")
from io import BytesIO
from PIL import Image

class MetaAIProvider:
    def __init__(self):
        from core.config import config
        self.config = config
        self.google_api_key = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
        
        # Get current models from central config
        self.image_model_key, self.image_model_cfg = config.get_image_model()
        self.text_model_key, self.text_model_cfg = config.get_text_model()
        
        print(f"[MetaAIProvider] Image: {self.image_model_key} -> {self.image_model_cfg}")
        print(f"[MetaAIProvider] Text: {self.text_model_key} -> {self.text_model_cfg}")
        
        # Load free provider if needed
        if self.image_model_cfg.get("provider") == "pollinations":
            try:
                from core.free_provider import free_provider
                self.free_provider = free_provider
            except Exception as e:
                print(f"[MetaAIProvider] Free provider import failed: {e}")
                self.free_provider = None
        else:
            self.free_provider = None

    def _generate_free(self, prompt, seed, width, height, style):
        if not self.free_provider:
            try:
                from core.free_provider import free_provider
                self.free_provider = free_provider
            except:
                return None
        
        print(f"\n[MetaAIProvider] Trying FREE {self.image_model_key}...")
        try:
            img = self.free_provider.generate(prompt, seed=seed, width=width, height=height, style=style)
            if img:
                print(f"[MetaAIProvider] ✅ FREE SUCCESS! {img.size} - $0!")
                return img
        except Exception as e:
            print(f"[MetaAIProvider] Free failed: {e}")
            traceback.print_exc()
        return None

    def _generate_gemini(self, prompt, max_retries=3):
        if not self.google_api_key:
            print("[MetaAIProvider] No GOOGLE_API_KEY for Gemini")
            return None
            
        print("\n[MetaAIProvider] === Gemini paid fallback ===")
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=self.google_api_key)
            model = self.image_model_cfg.get("model", "gemini-2.5-flash-image")
            
            for attempt in range(max_retries):
                try:
                    print(f"[MetaAIProvider] Gemini {model} attempt {attempt+1}...")
                    response = client.models.generate_content(
                        model=model,
                        contents=[prompt],
                        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"])
                    )
                    for cand in getattr(response, 'candidates', []):
                        content = getattr(cand, 'content', None)
                        if not content:
                            continue
                        for part in getattr(content, 'parts', []):
                            inline = getattr(part, 'inline_data', None)
                            if inline and getattr(inline, 'data', None):
                                img = Image.open(BytesIO(inline.data)).convert("RGB")
                                print(f"[MetaAIProvider] ✅ Gemini SUCCESS! {img.size}")
                                return img
                    break
                except Exception as e:
                    err = str(e)
                    if "503" in err and attempt < max_retries - 1:
                        wait = (2 ** attempt) + random.uniform(0, 1)
                        print(f"[MetaAIProvider] 503 retry in {wait:.1f}s...")
                        time.sleep(wait)
                        continue
                    else:
                        print(f"[MetaAIProvider] Gemini failed: {err[:500]}")
                        break
        except Exception as e:
            print(f"[MetaAIProvider] Gemini error: {e}")
        return None

    def generate(self, prompt, character_refs=None, seed=4421, width=1024, height=1024, style="watercolor"):
        full_prompt = f"{prompt}, {style} children's picture book illustration, soft watercolor, warm lighting, high detail, no text, storybook style"
        print(f"\n[MetaAIProvider] Prompt: {full_prompt[:80]}...")
        
        provider = self.image_model_cfg.get("provider", "pollinations")
        
        # Route based on provider from central config
        if provider == "pollinations":
            img = self._generate_free(full_prompt, seed, width, height, style)
            if img:
                if img.size != (width, height):
                    img = img.resize((width, height), Image.LANCZOS)
                return img
        elif provider == "gemini":
            img = self._generate_gemini(full_prompt)
            if img:
                if img.size != (width, height):
                    img = img.resize((width, height), Image.LANCZOS)
                return img
        
        # Fallback: try free if paid failed, or vice versa
        if provider != "pollinations":
            img = self._generate_free(full_prompt, seed, width, height, style)
            if img:
                if img.size != (width, height):
                    img = img.resize((width, height), Image.LANCZOS)
                return img
        
        print("\n[MetaAIProvider] ❌ All providers failed")
        return self._placeholder(full_prompt)

    def _placeholder(self, prompt):
        from PIL import ImageDraw
        img = Image.new('RGB', (1024, 1024), color=(255, 240, 230))
        d = ImageDraw.Draw(img)
        d.text((20,30), f"All failed - model: {self.image_model_key}", fill=(60,40,40))
        d.text((20,60), "Change config.yaml to switch", fill=(80,60,40))
        return img

meta_provider = MetaAIProvider()
