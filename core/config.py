"""
Central Config Loader - Single source of truth for all models
All agents use this - change config.yaml once, all agents switch!
"""
import os
import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

class Config:
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.load()
        return cls._instance
    
    def load(self):
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = {"models": {"text": {"default": "pollinations:openai"}, "image": {"default": "pollinations:flux"}}}
        
        # Allow env overrides - easiest way to switch
        # TEXT_MODEL=pollinations:openai or ollama:llama3.1:8b etc
        if os.getenv("TEXT_MODEL"):
            self._config["models"]["text"]["default"] = os.getenv("TEXT_MODEL")
        if os.getenv("IMAGE_MODEL"):
            self._config["models"]["image"]["default"] = os.getenv("IMAGE_MODEL")
    
    def get_text_model(self):
        """Get current text model - all text agents use this"""
        default = self._config.get("models", {}).get("text", {}).get("default", "pollinations:openai")
        providers = self._config.get("models", {}).get("text", {}).get("providers", {})
        return default, providers.get(default, {"provider": "pollinations", "model": "openai", "free": True})
    
    def get_image_model(self):
        """Get current image model - all image agents use this"""
        default = self._config.get("models", {}).get("image", {}).get("default", "pollinations:flux")
        providers = self._config.get("models", {}).get("image", {}).get("providers", {})
        return default, providers.get(default, {"provider": "pollinations", "model": "flux", "free": True})
    
    def get(self, key, default=None):
        keys = key.split(".")
        cur = self._config
        for k in keys:
            cur = cur.get(k, {}) if isinstance(cur, dict) else {}
        return cur if cur != {} else default

# Singleton
config = Config()
