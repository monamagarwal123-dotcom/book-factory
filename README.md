# Book Factory — Image Director + KDP Agent

> The first agent for your book factory. Solves the 3 biggest image pains: consistency, locking, and full-page sizing without stretching.

### Why this agent?

- **Images not consistent?** Uses Character Sheet + IP-Adapter + locked seed. Same girl in every chapter.
- **Fix regenerates whole person?** Uses inpainting (mask only face), not txt2img.
- **No catalog/lock?** `book_data/image_catalog.json` with 🔒 lock. Locked = never touched again.
- **Stretched when resized?** Never stretches. Auto-picks upscale / outpaint / regen_full with same refs.
- **No KDP export?** `kdp` command exports print-ready PDF with correct margins: `inside = 0.375 + pages/1000*0.125`.

### Quick Start

```bash
git clone https://github.com/yourname/book-factory
cd book-factory
pip install -r requirements.txt

# Set API key for real images (optional - works with placeholders offline)
export REPLICATE_API_TOKEN=r8_xxx

python cli.py init --title "My Children's Book"
python cli.py gen ch1_img1 "Sarah in kitchen, morning light" --character sarah --seed 4421
python cli.py lock ch1_img1
python cli.py alt ch1_img1 "A curly-haired girl in blue dress in sunlit kitchen"
python cli.py resize ch1_img1 --target full_bleed_6x9 --width 1875 --height 2775
python cli.py fix ch1_img2 "warmer skin tone"  # inpaint, preserves identity
python cli.py kdp --trim 6x9 --pages 200
python cli.py list
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

agents/
  image_director.py     # generate() / fix() / resize_or_regen()

exporters/
  kdp_pdf.py            # Trim + margins + bleed
```

### Model Router

| Task | Model (real) | Fallback (offline) |
|------|--------------|-------------------|
| Image gen consistent | `black-forest-labs/flux-pro` + IP-Adapter ref | Placeholder with prompt |
| Fix face color | `stability-ai/sdxl-inpainting` + mask | Overlay text |
| Upscale | `nightmareai/real-esrgan` | Lanczos |
| Outpaint full bleed | `stability-ai/sdxl-outpainting` | Extend canvas |
| KDP PDF | ReportLab / WeasyPrint | Placeholder PDF |

All via `core/models.py` — swap models in `config.yaml`.

### Image Sizing Logic (your question)

```python
def resize_or_regen(img_id, target_w, target_h):
    ratio_diff = abs(src_ratio - target_ratio)
    if ratio_diff < 0.15:
        mode = "outpaint" if "full" in target else "upscale"  # no new person
    else:
        mode = "regen_full"  # same refs + same seed, new composition
    
    # NEVER stretch
```

Variants stored: `ch1_img1.jpg` + `ch1_img1_full_bleed_6x9.jpg` (same logical image).

### Next Agents (roadmap)

- [ ] Editorial Squad: tone, flow, fact check
- [ ] Product Agent: market research, BISAC categories, MOAT
- [ ] Publish Readiness: STOP agent says 90% ready
- [ ] Web UI: 3-pane Obsidian-like editor

### Config

Edit `config.yaml`:

```yaml
models:
  image_gen: "replicate:flux-pro"
  image_inpaint: "replicate:sdxl-inpainting"
  image_ref_strength: 0.8  # IP-Adapter strength for identity
```

### License

MIT — push your book, keep your IP local.
