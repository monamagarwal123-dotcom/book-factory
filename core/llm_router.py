"""
LLM Router - Grok + Gemini focused
Supports: Gemini (Google) and Grok (xAI) as primary, with fallbacks
"""
import os
import requests
import time

class LLMRouter:
    def __init__(self):
        from core.config import config
        self.config = config
        self.model_key, self.model_cfg = config.get_text_model()
        print(f"[LLMRouter] Default: {self.model_key} -> {self.model_cfg}")
        self.has_openai = bool(os.getenv("OPENAI_API_KEY"))
        self.has_gemini = bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))
        self.has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
        self.has_groq = bool(os.getenv("GROQ_API_KEY"))
        self.has_grok = bool(os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY"))
        print(f"[LLMRouter] Keys: gemini={self.has_gemini} grok={self.has_grok} groq={self.has_groq} openai={self.has_openai}")
        self._gemini_models = None
        self._groq_models = None
    
    def generate(self, prompt, system=None, max_tokens=2000, temperature=0.7):
        # User wants grok or gemini - prioritize those
        default_provider = self.model_cfg.get("provider", "gemini")
        order = []
        if default_provider not in order:
            order.append(default_provider)
        # Prioritize grok and gemini as requested
        for prov in ["grok", "gemini", "pollinations", "groq", "ollama", "openai", "anthropic"]:
            if prov not in order:
                order.append(prov)
        
        print(f"[LLMRouter] Order: {order}")
        
        for provider in order:
            if provider == "openai" and not self.has_openai:
                continue
            if provider == "gemini" and not self.has_gemini:
                print(f"[LLMRouter] Skip gemini - no GOOGLE_API_KEY")
                continue
            if provider == "grok" and not self.has_grok:
                print(f"[LLMRouter] Skip grok - no XAI_API_KEY")
                continue
            if provider == "groq" and not self.has_groq:
                continue
            if provider == "anthropic" and not self.has_anthropic:
                continue
            
            print(f"[LLMRouter] Trying {provider}...")
            try:
                if provider == "gemini":
                    result = self._generate_gemini(prompt, system, max_tokens, temperature)
                elif provider == "grok":
                    result = self._generate_grok(prompt, system, max_tokens, temperature)
                elif provider == "pollinations":
                    result = self._generate_pollinations(prompt, system, max_tokens, temperature)
                elif provider == "groq":
                    result = self._generate_groq(prompt, system, max_tokens, temperature)
                elif provider == "ollama":
                    result = self._generate_ollama(prompt, system, max_tokens, temperature)
                elif provider == "openai":
                    result = self._generate_openai(prompt, system, max_tokens, temperature)
                elif provider == "anthropic":
                    result = self._generate_anthropic(prompt, system, max_tokens, temperature)
                else:
                    result = self._generate_gemini(prompt, system, max_tokens, temperature)
                
                if result and len(result) > 80 and "[Placeholder" not in result[:150]:
                    print(f"[LLMRouter] SUCCESS {provider} {len(result)} chars")
                    return result
            except Exception as e:
                print(f"[LLMRouter] {provider} failed: {e}")
                time.sleep(0.5)
                continue
        
        print(f"[LLMRouter] All failed - fallback")
        return self._fallback_story(prompt)

    def _generate_grok(self, prompt, system, max_tokens, temperature):
        """xAI Grok - OpenAI compatible"""
        api_key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
        if not api_key:
            raise Exception("No XAI_API_KEY - get at https://console.x.ai")
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        messages = []
        if system:
            messages.append({"role": "system", "content": system[:2000]})
        messages.append({"role": "user", "content": prompt[:4000]})
        
        # Grok models - try newest first
        models_to_try = [
            "grok-4",
            "grok-3",
            "grok-3-mini",
            "grok-3-fast",
            "grok-2-1212",
            "grok-2",
            "grok-beta",
        ]
        
        for model in models_to_try:
            try:
                print(f"[LLMRouter] Grok trying {model}...")
                payload = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
                resp = requests.post("https://api.x.ai/v1/chat/completions", json=payload, headers=headers, timeout=90)
                if resp.status_code == 200:
                    data = resp.json()
                    text = data["choices"][0]["message"]["content"]
                    if text and len(text) > 80:
                        print(f"[LLMRouter] Grok {model} OK {len(text)} chars")
                        return text
                else:
                    print(f"[LLMRouter] Grok {model} {resp.status_code}: {resp.text[:200]}")
                    if resp.status_code == 404:
                        continue
                    if "insufficient" in resp.text.lower() or "credit" in resp.text.lower():
                        raise Exception(f"Grok billing issue: {resp.text[:200]}")
            except Exception as e:
                print(f"[LLMRouter] Grok {model} err: {e}")
                continue
        
        raise Exception("Grok all models failed")

    def _discover_gemini_models(self):
        if self._gemini_models is not None:
            return self._gemini_models
        
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            return []
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                models = []
                for m in data.get("models", []):
                    name = m.get("name", "").replace("models/", "")
                    if "flash" in name or "pro" in name:
                        if "embedding" not in name and "image" not in name and "tts" not in name and "native-audio" not in name:
                            models.append(name)
                # Sort: 1.5-flash first (most stable)
                models.sort(key=lambda x: (0 if "1.5-flash" in x else 1 if "2.0-flash" in x else 2))
                print(f"[LLMRouter] Discovered Gemini models: {models[:15]}")
                self._gemini_models = models
                return models
        except Exception as e:
            print(f"[LLMRouter] Gemini discovery failed: {e}")
        
        fallback = [
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-1.5-pro",
            "gemini-2.0-flash",
            "gemini-flash-latest",
            "gemini-pro-latest",
        ]
        self._gemini_models = fallback
        return fallback

    def _generate_gemini(self, prompt, system, max_tokens, temperature):
        # Try new SDK first
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise Exception("No GOOGLE_API_KEY")
        
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        
        # Try old SDK first - it's more stable for 1.5-flash
        try:
            import google.generativeai as old_genai
            old_genai.configure(api_key=api_key)
            models_to_try = self._discover_gemini_models()
            # Prioritize 1.5-flash - most stable
            models_to_try = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-flash-001", "gemini-1.5-pro"] + models_to_try
            
            seen = set()
            deduped = []
            for m in models_to_try:
                if m not in seen:
                    deduped.append(m)
                    seen.add(m)
            models_to_try = deduped
            
            for model in models_to_try[:8]:
                try:
                    print(f"[LLMRouter] Gemini (old SDK) trying {model}...")
                    gen_model = old_genai.GenerativeModel(model)
                    resp = gen_model.generate_content(
                        full_prompt,
                        generation_config=old_genai.GenerationConfig(
                            max_output_tokens=max_tokens,
                            temperature=temperature
                        )
                    )
                    text = resp.text
                    if text and len(text) > 80:
                        print(f"[LLMRouter] Gemini old SDK {model} OK {len(text)}")
                        return text
                except Exception as e:
                    err = str(e)
                    if "404" in err or "not found" in err.lower():
                        print(f"[LLMRouter] Gemini old SDK {model} 404")
                        continue
                    if "429" in err or "quota" in err.lower() or "503" in err:
                        print(f"[LLMRouter] Gemini {model} quota/overload: {e}")
                        time.sleep(2)
                        continue
                    print(f"[LLMRouter] Gemini old SDK {model} err: {e}")
                    continue
        except Exception as e:
            print(f"[LLMRouter] Old SDK not available: {e}")
        
        # Try new SDK
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)
            models_to_try = self._discover_gemini_models()
            
            for model in models_to_try[:8]:
                try:
                    print(f"[LLMRouter] Gemini (new SDK) trying {model}...")
                    resp = client.models.generate_content(
                        model=model,
                        contents=[full_prompt],
                        config=types.GenerateContentConfig(
                            max_output_tokens=max_tokens,
                            temperature=temperature
                        )
                    )
                    text = resp.text
                    if text and len(text) > 80:
                        print(f"[LLMRouter] Gemini new SDK {model} OK")
                        return text
                except Exception as e:
                    err = str(e)
                    if "404" in err or "NOT_FOUND" in err:
                        print(f"[LLMRouter] Gemini new SDK {model} 404")
                        continue
                    if "503" in err or "429" in err or "UNAVAILABLE" in err:
                        print(f"[LLMRouter] Gemini {model} overloaded, retry")
                        time.sleep(2)
                        continue
                    print(f"[LLMRouter] Gemini new SDK {model} err: {e}")
                    continue
        except Exception as e:
            print(f"[LLMRouter] New SDK failed: {e}")
        
        raise Exception("Gemini all failed")

    def _discover_groq_models(self):
        if self._groq_models is not None:
            return self._groq_models
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return []
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            resp = requests.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=10)
            if resp.status_code == 200:
                models = [m["id"] for m in resp.json().get("data", [])]
                print(f"[LLMRouter] Groq models: {models}")
                self._groq_models = models
                return models
        except Exception as e:
            print(f"[LLMRouter] Groq discovery failed: {e}")
        self._groq_models = []
        return []

    def _generate_groq(self, prompt, system, max_tokens, temperature):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise Exception("No GROQ_API_KEY")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        messages = []
        if system:
            messages.append({"role": "system", "content": system[:2000]})
        messages.append({"role": "user", "content": prompt[:4000]})
        
        models_to_try = self._discover_groq_models()
        if not models_to_try:
            models_to_try = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile"]
        
        for model in models_to_try:
            try:
                payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
                resp = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=60)
                if resp.status_code == 200:
                    text = resp.json()["choices"][0]["message"]["content"]
                    if text and len(text) > 80:
                        print(f"[LLMRouter] Groq {model} OK")
                        return text
            except Exception as e:
                print(f"[LLMRouter] Groq {model} err: {e}")
                continue
        raise Exception("Groq all failed")

    def _generate_pollinations(self, prompt, system, max_tokens, temperature):
        api_url = "https://text.pollinations.ai/openai"
        messages = []
        if system:
            messages.append({"role": "system", "content": system[:2000]})
        messages.append({"role": "user", "content": prompt[:4000]})
        payload = {"model": "openai", "messages": messages, "max_tokens": max_tokens, "temperature": temperature, "stream": False}
        
        for attempt in range(3):
            try:
                resp = requests.post(api_url, json=payload, timeout=60, headers={"Content-Type": "application/json"})
                if resp.status_code == 200:
                    data = resp.json()
                    if "choices" in data and data["choices"]:
                        text = data["choices"][0]["message"]["content"]
                        if text and len(text) > 80:
                            return text
            except Exception as e:
                print(f"[LLMRouter] Pollinations err: {e}")
            time.sleep(1.5 ** attempt)
        raise Exception("Pollinations failed")

    def _generate_ollama(self, prompt, system, max_tokens, temperature):
        try:
            requests.get("http://localhost:11434/api/tags", timeout=2)
        except:
            raise Exception("Ollama not running")
        payload = {"model": "llama3.1:8b", "prompt": f"{system}\n\n{prompt}" if system else prompt, "stream": False, "options": {"num_predict": max_tokens, "temperature": temperature}}
        resp = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
        if resp.status_code == 200:
            text = resp.json().get("response", "")
            if text and len(text) > 80:
                return text
        raise Exception("Ollama failed")

    def _generate_openai(self, prompt, system, max_tokens, temperature):
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages, max_tokens=max_tokens, temperature=temperature)
        return resp.choices[0].message.content

    def _generate_anthropic(self, prompt, system, max_tokens, temperature):
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        resp = client.messages.create(model="claude-3-5-sonnet-20241022", max_tokens=max_tokens, temperature=temperature, system=system or "", messages=[{"role": "user", "content": prompt}])
        return resp.content[0].text
    
    def _fallback_story(self, prompt):
        import re
        m = re.search(r"Chapter prompt:\s*(.+)", prompt, re.IGNORECASE)
        chapter_prompt = m.group(1).strip()[:200] if m else "A fun adventure"
        m2 = re.search(r"ch(\d+)", prompt.lower())
        ch_num = int(m2.group(1)) if m2 else 1
        return f"Chapter {ch_num}: {chapter_prompt}\n\nSarah smiled. {chapter_prompt} She looked around with joy. The day was bright and full of colors.\n\n[All APIs failed]"

llm_router = LLMRouter()
