# Book Factory — Image Director + KDP Agent

> The first agent for your book factory. Solves the 3 biggest image pains: consistency, locking, and full-page sizing without stretching.
> **Now with Gemini Imagen 3 support — Python agent generates REAL images by itself!**

### Why this agent?

- **Images not consistent?** Uses Character Sheet + IP-Adapter + locked seed. Same girl in every chapter.
- **Fix regenerates whole person?** Uses inpainting (mask only face), not txt2img.
- **No catalog/lock?** `book_data/image_catalog.json` with 🔒 lock. Locked = never touched again.
- **Stretched when resized?** Never stretches. Auto-picks upscale / outpaint / regen_full with same refs.
- **No KDP export?** `kdp` command exports print-ready PDF with correct margins.

### 🚀 Quick Start (One Command)

**Option 1: Auto Setup Script (Recommended)**
```bash
git clone https://github.com/monamagarwal123-dotcom/book-factory.git
cd book-factory
chmod +x setup.sh
./setup.sh
# It will:
# - Fix pip not found (uses python3 -m pip)
# - Create .venv, install deps
# - Prompt for GOOGLE_API_KEY (get free at https://aistudio.google.com/app/apikey)
# - Prompt for REPLICATE_API_TOKEN (optional)
# - Save to .env, test generation
```

**Option 2: Python Setup Script**
```bash
git clone https://github.com/monamagarwal123-dotcom/book-factory.git
cd book-factory
python3 setup.py
# Same as above, cross-platform (Windows/Mac/Linux)
```

**After setup, every new terminal:**
```bash
source .venv/bin/activate
export $(cat .env | xargs)  # load API keys
python cli.py gen ch1_01 "Sarah finds magic seed" --character sarah --seed 4421
```

### 📦 Manual Install (if you prefer)

> **IMPORTANT:** On Mac, NEVER use `pip` — use `python3 -m pip` 
> `-bash: pip: command not found` happens because `pip` is not in PATH, but `python3 -m pip` always works.

```bash
git clone https://github.com/monamagarwal123-dotcom/book-factory.git
cd book-factory

# 1. Check Python (needs 3.9+, but 3.11+ recommended to avoid FutureWarning)
python3 --version
# If Python 3.9, you'll see:
# FutureWarning: You are using Python 3.9 past its end of life
# To upgrade: brew install python@3.11

# 2. Create venv (isolates deps, fixes permission issues)
python3 -m venv .venv
source .venv/bin/activate

# 3. Install - ALWAYS use python3 -m pip, NOT pip
python3 -m pip --version  # check pip exists
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
# Or inside venv:
python -m pip install -r requirements.txt

# 4. Verify SDKs installed to correct Python
python3 -c "from google import genai; print('google-genai OK')"
python3 -c "import google.generativeai; print('google-generativeai OK')"

# 5. API Keys - Get free Gemini key
# https://aistudio.google.com/app/apikey -> Create API Key -> Copy AIza...
export GOOGLE_API_KEY="AIzaSy..."
export REPLICATE_API_TOKEN="r8_..."  # optional, for Flux Pro

# Save for future
echo "GOOGLE_API_KEY=$GOOGLE_API_KEY" > .env
echo "REPLICATE_API_TOKEN=$REPLICATE_API_TOKEN" >> .env

# 6. Test
python cli.py gen test_gemini "Sarah in kitchen, watercolor children's book" --seed 4421
open book_data/images/test_gemini.jpg
```

### 🔑 API Keys

| Provider | Cost | Quality | How to get | Env var |
|----------|------|---------|------------|---------|
| **Gemini Imagen 3 / Flash** | $0.02/img, free tier | Great watercolor | https://aistudio.google.com/app/apikey | `GOOGLE_API_KEY` |
| **Replicate Flux Pro** | $0.05/img | Best | https://replicate.com/account/api-tokens | `REPLICATE_API_TOKEN` |
| **Local SDXL Turbo** | Free, local Mac | Good | `python3 -m pip install torch diffusers` | None |

Provider priority (auto): Gemini REST → Gemini SDK → Replicate → Local SDXL → Placeholder

### 🧪 Testing & Daily Use

```bash
# Load env each new terminal
source .venv/bin/activate
export $(cat .env | xargs)

# Generate images - Python agent does it itself, no chat needed!
python cli.py init --title "My Children's Book"
python cli.py gen ch1_img1 "Sarah in kitchen, morning light" --character sarah --seed 4421
python cli.py gen ch1_img2 "Sarah in garden with dog" --character sarah --seed 4421

# Lock good images
python cli.py lock ch1_img1

# Resize without stretching
python cli.py resize ch1_img1 --target full_bleed_6x9 --width 1875 --height 2775
# Auto picks: upscale / outpaint / regen_full (never stretch)

# Fix only face, not whole image
python cli.py fix ch1_img2 "warmer skin tone"

# Export KDP PDF
python cli.py kdp --trim 6x9 --pages 200

# List all
python cli.py list
```

### ⚠️ Troubleshooting

**`-bash: pip: command not found`**
```bash
# NEVER use `pip`, use:
python3 -m pip install -r requirements.txt
# Or inside venv:
python -m pip install -r requirements.txt
```

**`FutureWarning: Python 3.9 past its end of life` + `NotOpenSSLWarning`**
```bash
# You're on Python 3.9 which is EOL. Upgrade:
brew install python@3.11
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# Or use pyenv:
pyenv install 3.11.9
pyenv local 3.11.9
```

**`404 NOT_FOUND: models/imagen-3.0-generate-001 is not found for v1beta`**
- Fixed in latest `core/meta_provider.py` - uses correct 2026 model `gemini-2.0-flash-preview-image-generation`
- Update: `git pull origin main` or copy latest `meta_provider.py`

**`No module named 'google.generativeai'` or `google-genai not installed`**
```bash
# Install to correct Python:
python3 -m pip install google-genai google-generativeai -q
# Verify:
python3 -c "from google import genai; print('OK')"
# If still fails, you installed to different Python - use python3 -m pip always
```

**Git asks for password**
```bash
# Setup SSH once (no more passwords)
ssh-keygen -t ed25519 -C "you@github"
cat ~/.ssh/id_ed25519.pub  # copy to https://github.com/settings/keys
ssh -T git@github.com  # should say "successfully authenticated"
git remote set-url origin git@github.com:monamagarwal123-dotcom/book-factory.git
git push
```

### Architecture

```
book_data/
  book_bible.json       # Characters, art style, tone
  image_catalog.json    # All images with lock, alt, variants
  images/               # Originals + variants (full_bleed_6x9, etc)
  chapters/
  output/kdp_print.pdf

core/
  book_bible.py         # Prompt context builder
  image_catalog.py      # Lock / variant DB
  models.py             # Router: text vs image vs vision
  meta_provider.py      # Gemini + Replicate + Local - FIXED 2026 models

agents/
  image_director.py     # generate() / fix() / resize_or_regen()

exporters/
  kdp_pdf.py            # Trim + margins + bleed

setup.sh / setup.py     # One-command install + API key prompts
.env                    # Your API keys (gitignored)
.venv/                  # Virtual env (gitignored)
```

### Model Router

| Task | Model (real) | Fallback |
|------|--------------|----------|
| Image gen | Gemini 2.0 Flash Preview → Imagen 3 → Flux Pro + IP-Adapter | Local SDXL Turbo |
| Fix face | SDXL inpainting + mask | Overlay |
| Upscale | Real-ESRGAN | Lanczos |
| Outpaint | SDXL outpainting | Extend canvas |
| KDP PDF | ReportLab | Placeholder |

All via `core/models.py` — swap models in `config.yaml`.

### Image Sizing Logic

```python
def resize_or_regen(img_id, target_w, target_h):
    ratio_diff = abs(src_ratio - target_ratio)
    if ratio_diff < 0.15:
        mode = "outpaint" if "full" in target else "upscale"  # no new person
    else:
        mode = "regen_full"  # same refs + same seed, new composition
    # NEVER stretch
```

### Next Agents

- [x] Gemini support - Python agent generates real images via API
- [x] Setup script with python3 -m pip fix + API prompts
- [ ] Editorial Squad: tone, flow, fact check
- [ ] Product Agent: market research, BISAC categories
- [ ] Publish Readiness: STOP agent says 90% ready
- [ ] Web UI: 3-pane Obsidian-like editor

### License

MIT — push your book, keep your IP local.
