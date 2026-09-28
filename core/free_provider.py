"""
FREE PROVIDER - Fixed for Pollinations 402
- Uses POST first (bypasses GET rate limit), tries turbo (most reliable free)
- Supports POLLINATIONS_API_KEY from https://auth.pollinations.ai
"""
import os
import time
import urllib.parse
from io import BytesIO
from PIL import Image
import requests

class FreeImageProvider:
    def __init__(self):
        from core.config import config
        self.config = config
        self.get_base = "https://image.pollinations.ai/prompt"
        self.post_base = "https://image.pollinations.ai/prompt"
        self.api_key = os.getenv("POLLINATIONS_API_KEY") or os.getenv("POLLINATIONS_TOKEN") or ""
        model_key, model_cfg = config.get_image_model()
        token_note = "with token" if self.api_key else "no token (get free at auth.pollinations.ai)"
        print(f"[FreeProvider] Initialized with {model_key} -> {model_cfg} - {token_note}")

    def _headers(self):
        h = {"User-Agent": "BookFactory/1.0"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _try_post(self, prompt, seed, width, height, model):
        payload = {"prompt": prompt[:1500], "width": width, "height": height, "seed": seed, "model": model, "nologo": True, "enhance": True, "safe": True}
        print(f"[FreeProvider] POST {model} {width}x{height} seed {seed}")
        try:
            resp = requests.post(self.post_base, json=payload, headers=self._headers(), timeout=90)
            print(f"[FreeProvider] POST status {resp.status_code}")
            if resp.status_code == 200 and 'image' in resp.headers.get('content-type',''):
                img = Image.open(BytesIO(resp.content)).convert("RGB")
                print(f"[FreeProvider] ✅ POST SUCCESS {model} {img.size}")
                return img
            elif resp.status_code == 402:
                print(f"[FreeProvider] POST 402 - {resp.text[:400]}")
            elif resp.status_code == 429:
                time.sleep(2)
        except Exception as e:
            print(f"[FreeProvider] POST error {model}: {e}")
        return None

    def _try_get(self, prompt, seed, width, height, model):
        safe = urllib.parse.quote(prompt[:1500])
        params = f"width={width}&height={height}&seed={seed}&model={model}&nologo=true&enhance=true&safe=true"
        url = f"{self.get_base}/{safe}?{params}"
        print(f"[FreeProvider] GET {model} {width}x{height}")
        try:
            resp = requests.get(url, headers=self._headers(), timeout=90)
            if resp.status_code == 200 and 'image' in resp.headers.get('content-type',''):
                img = Image.open(BytesIO(resp.content)).convert("RGB")
                print(f"[FreeProvider] ✅ GET SUCCESS {model} {img.size}")
                return img
            elif resp.status_code == 402:
                print(f"[FreeProvider] GET 402 for {model}")
            elif resp.status_code == 429:
                time.sleep(2)
        except Exception as e:
            print(f"[FreeProvider] GET error {model}: {e}")
        return None

    def generate(self, prompt, seed=4421, width=1024, height=1024, style="watercolor"):
        model_key, model_cfg = self.config.get_image_model()
        model_name = model_cfg.get("model", "turbo")
        full_prompt = f"{prompt}, {style} children's book illustration, soft watercolor, warm lighting, high detail, storybook style, no text, cute, vibrant colors"
        free_models = ["turbo", "flux", "zimage", "flux-realism"]
        models_to_try = []
        for m in [model_name] + free_models:
            if m not in models_to_try:
                models_to_try.append(m)
        for model in models_to_try:
            img = self._try_post(full_prompt, seed, width, height, model)
            if img:
                return img
            time.sleep(0.6)
            img = self._try_get(full_prompt, seed, width, height, model)
            if img:
                return img
            time.sleep(0.8)
        print(f"[FreeProvider] ❌ All models failed - will use placeholder")
        return None

free_provider = FreeImageProvider()
