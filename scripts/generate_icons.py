"""Generate PWA icons for Guide Me Krishna.
Requires: pip install Pillow
Run: python scripts/generate_icons.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

SIZES = [72, 96, 128, 144, 152, 192, 384, 512]
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'static', 'icons')
os.makedirs(OUT_DIR, exist_ok=True)

BG = (12, 6, 1)        # #0c0601
GOLD = (245, 200, 66)  # #f5c842

for size in SIZES:
    img = Image.new('RGB', (size, size), BG)
    draw = ImageDraw.Draw(img)

    # Gold circle border
    margin = size // 12
    draw.ellipse([margin, margin, size - margin, size - margin],
                 outline=GOLD, width=max(2, size // 40))

    # OM symbol — use default font, scale text to fit
    text = 'OM'
    font_size = size // 3
    try:
        font = ImageFont.truetype('arial.ttf', font_size)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, (size - th) / 2 - size * 0.04),
              text, fill=GOLD, font=font)

    path = os.path.join(OUT_DIR, f'icon-{size}.png')
    img.save(path)
    print(f'  saved {path}')

print('Done. Icons saved to src/static/icons/')
