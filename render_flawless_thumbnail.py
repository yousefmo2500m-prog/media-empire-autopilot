from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from pathlib import Path

thumb_path = Path("/home/user/production_vault/video_eldalil_wonders/thumbnail_well_of_wonders_daftar_rawi.jpg")
font_path = Path("/home/user/media-empire-autopilot/fonts/Cairo-Variable.ttf")

img = Image.open(thumb_path).convert("RGB")
img = img.resize((1280, 720), Image.Resampling.LANCZOS)

# Enhance contrast & punchiness for YouTube clickability
img = ImageEnhance.Contrast(img).enhance(1.20)
img = ImageEnhance.Color(img).enhance(1.25)
img = ImageEnhance.Sharpness(img).enhance(1.30)

canvas = img.convert("RGBA")

# Dark gradient at the bottom for crystal-clear readability
grad = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
gdraw = ImageDraw.Draw(grad)
for y in range(480, 720):
    alpha = int(220 * ((y - 480) / 240.0) ** 1.2)
    gdraw.line([(0, y), (1280, y)], fill=(5, 5, 12, alpha))

canvas = Image.alpha_composite(canvas, grad)
draw = ImageDraw.Draw(canvas)

# Fonts
f_badge = ImageFont.truetype(str(font_path), 32)
f_main = ImageFont.truetype(str(font_path), 76)

# 1. Top-Right Badge: «حكاية من بطن الجبل | دفتر راوي»
badge_text = "حكاية من بطن الجبل | دفتر راوي"
bbox = draw.textbbox((0, 0), badge_text, font=f_badge)
bw = bbox[2] - bbox[0] + 44
bh = bbox[3] - bbox[1] + 20

bx0 = 1280 - bw - 40
by0 = 36
bx1 = 1280 - 40
by1 = by0 + bh

# Red & Gold rounded badge
draw.rounded_rectangle([bx0, by0, bx1, by1], radius=16, fill=(215, 20, 45, 240), outline=(255, 215, 0, 255), width=3)
# Badge text direct
draw.text((bx0 + 22, by0 + 8), badge_text, font=f_badge, fill=(255, 255, 255))

# 2. Main Shock Hook Text at Bottom-Center / Bottom: «السر الصادم في القاع!»
hook_text = "السر الصادم في القاع!"
hbbox = draw.textbbox((0, 0), hook_text, font=f_main)
hw = hbbox[2] - hbbox[0]
hh = hbbox[3] - hbbox[1]

hx = (1280 - hw) // 2
hy = 720 - hh - 55

# Multi-layer heavy black outline / drop shadow for maximum 3D pop
for dx in (-4, -3, -2, -1, 0, 1, 2, 3, 4):
    for dy in (-4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6):
        if dx != 0 or dy != 0:
            draw.text((hx + dx, hy + dy), hook_text, font=f_main, fill=(0, 0, 0, 255))

# Front vibrant golden-yellow text
draw.text((hx, hy), hook_text, font=f_main, fill=(255, 225, 20, 255))

final_img = canvas.convert("RGB")
final_img.save(str(thumb_path), "JPEG", quality=95)
print("Rendered flawless Arabic thumbnail!")
