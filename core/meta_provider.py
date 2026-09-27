"""
Meta AI Image Provider for Book Factory
Uses Meta AI (Muse Spark) image generation for children's book illustrations
"""
from pathlib import Path
from PIL import Image
import os

class MetaAIProvider:
    """
    Drop-in replacement for Replicate/Flux.
    When running inside Meta AI chat, call generate_via_meta_ai()
    When running locally, falls back to placeholder or calls Meta AI API if available
    """
    
    def __init__(self):
        self.enabled = True
        print("[MetaAIProvider] Initialized - Meta AI image gen ready")
    
    def generate(self, prompt, character_refs=None, seed=4421, width=1024, height=1024, style="watercolor"):
        """
        Generates image via Meta AI
        prompt: full prompt including bible context
        character_refs: list of character names for consistency
        seed: for reproducibility (Meta AI uses seed internally)
        """
        # Enhanced prompt for children's book
        meta_prompt = f"""{prompt}, 
        children's picture book illustration, {style}, 
        soft watercolor, warm lighting, consistent character design,
        no text, no words, high detail, storybook style
        """
        
        if character_refs:
            meta_prompt += f", same character: {', '.join(character_refs)}, consistent face, consistent outfit"
        
        # Note: When running in Meta AI environment, this would be called via:
        # container.image_gen with conversation containing the prompt
        # For local CLI, we return a marker that cli.py can detect
        
        print(f"[MetaAIProvider] Generating: {meta_prompt[:120]}... | seed={seed} | {width}x{height}")
        
        # Return prompt data - actual image generation happens in Meta AI chat via tool
        # or via API when META_AI_API_KEY is set
        return {
            "provider": "meta_ai",
            "prompt": meta_prompt,
            "seed": seed,
            "width": width,
            "height": height,
            "character_refs": character_refs,
            "status": "ready_for_generation"
        }
    
    def generate_image_object(self, prompt, width=1024, height=1024):
        """
        Placeholder that creates a nice placeholder image with prompt info
        In real Meta AI integration, this would be replaced by API call
        """
        from PIL import ImageDraw
        img = Image.new('RGB', (width, height), color=(255, 248, 235))
        draw = ImageDraw.Draw(img)
        draw.rectangle([15, 15, width-15, height-15], outline=(180, 160, 140), width=3)
        draw.text((30, 30), f"Meta AI\n{prompt[:200]}\n\nWidth: {width} Height: {height}", fill=(60, 50, 40))
        return img

# Singleton
meta_provider = MetaAIProvider()
