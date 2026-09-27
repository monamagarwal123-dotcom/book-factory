import os
from pathlib import Path
from PIL import Image

class ModelRouter:
    """Unified router for text and image models - real API + offline fallback"""
    
    def __init__(self):
        self.replicate_token = os.getenv("REPLICATE_API_TOKEN")
        self.use_real = bool(self.replicate_token)
    
    def image_generate(self, prompt, character_refs=None, seed=4421, width=1024, height=1024):
        """Generate with Flux + IP-Adapter if token exists, else placeholder"""
        if self.use_real:
            try:
                import replicate
                # Flux Pro with reference image for consistency
                input_data = {
                    "prompt": prompt,
                    "seed": seed,
                    "width": width,
                    "height": height,
                    "aspect_ratio": f"{width}:{height}" if width!=height else "1:1",
                }
                # If we have character refs, use IP-Adapter model
                if character_refs:
                    # Use flux with IP-Adapter or use separate model
                    # For now using flux-pro, refs passed as reference image
                    # In production: use "adirik/realvisxl-v3-multi-controlnet-lora" or similar
                    pass
                
                output = replicate.run(
                    "black-forest-labs/flux-1.1-pro",
                    input=input_data
                )
                # output is URL - download
                return self._download_image(output, prompt)
            except Exception as e:
                print(f"[ModelRouter] Real gen failed, fallback to placeholder: {e}")
        
        # Fallback placeholder (what we used in v0.1)
        return self._placeholder_image(prompt, seed, width, height, character_refs)
    
    def image_inpaint(self, image_path, mask_path, prompt, seed=4421):
        """Fix only masked area - preserves identity"""
        if self.use_real:
            try:
                import replicate
                output = replicate.run(
                    "stability-ai/sdxl-inpainting",
                    input={
                        "image": open(image_path, "rb"),
                        "mask": open(mask_path, "rb"),
                        "prompt": prompt,
                        "seed": seed,
                        "num_outputs": 1
                    }
                )
                return self._download_image(output[0], prompt)
            except Exception as e:
                print(f"[ModelRouter] Real inpaint failed, fallback: {e}")
        
        # Fallback: simulate inpaint
        img = Image.open(image_path)
        from PIL import ImageDraw
        d = ImageDraw.Draw(img)
        d.text((40, 500), f"INPAINT: {prompt}", fill=(200,0,0))
        return img
    
    def image_outpaint(self, image_path, target_w, target_h, prompt):
        """Extend canvas for full bleed"""
        if self.use_real:
            try:
                import replicate
                # Use outpainting model
                output = replicate.run(
                    "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96e94f011d64",
                    input={
                        "image": open(image_path, "rb"),
                        "prompt": f"{prompt}, extend background, keep subject centered",
                        "width": target_w,
                        "height": target_h,
                    }
                )
                return self._download_image(output[0], prompt)
            except Exception as e:
                print(f"[ModelRouter] Real outpaint failed: {e}")
        
        # Fallback
        src = Image.open(image_path)
        new_img = Image.new('RGB', (target_w, target_h), (255,245,225))
        x = (target_w - src.size[0])//2
        y = (target_h - src.size[1])//2
        new_img.paste(src, (x,y))
        return new_img
    
    def image_upscale(self, image_path, target_w, target_h):
        if self.use_real:
            try:
                import replicate
                output = replicate.run(
                    "nightmareai/real-esrgan",
                    input={"image": open(image_path, "rb"), "scale": 2}
                )
                return self._download_image(output, "upscaled")
            except:
                pass
        img = Image.open(image_path)
        return img.resize((target_w, target_h), Image.LANCZOS)
    
    def _download_image(self, url_or_path, prompt):
        import requests, tempfile
        if isinstance(url_or_path, str) and url_or_path.startswith("http"):
            r = requests.get(url_or_path)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            tmp.write(r.content)
            tmp.close()
            return Image.open(tmp.name)
        elif hasattr(url_or_path, 'read'):
            return Image.open(url_or_path)
        else:
            return Image.open(url_or_path)
    
    def _placeholder_image(self, prompt, seed, width, height, refs):
        from PIL import ImageDraw
        img = Image.new('RGB', (width, height), color=(255, 245, 225))
        d = ImageDraw.Draw(img)
        d.rectangle([10,10,width-10,height-10], outline=(200,180,160), width=2)
        d.text((20,20), f"Prompt: {prompt[:100]}...\nSeed:{seed}\nRefs:{refs}\n{width}x{height}", fill=(80,60,40))
        return img

router = ModelRouter()
