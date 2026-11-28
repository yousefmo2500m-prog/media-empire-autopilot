import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import arabic_reshaper
from bidi.algorithm import get_display

thumb_path = Path("/home/user/production_vault/video_eldalil_wonders/thumbnail_well_of_wonders_daftar_rawi.jpg")
font_path = Path("/home/user/media-empire-autopilot/fonts/Cairo-Variable.ttf")

img = Image.open(thumb_path).convert("RGB")
w, h = img.size

draw = ImageDraw.Draw(img)

# Helper for Arabic text rendering
def draw_ar_text(draw, text, xy, font, fill, shadow_fill=None, shadow_offset=(3, 3)):
    reshaped = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped)
    x, y = xy
    if shadow_fill:
        for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, 4), (4, 0), shadow_offset]:
            draw.text((x + dx, y + dy), bidi_text, font=font, fill=shadow_fill)
    draw.text((x, y), bidi_text, font=font, fill=fill)

try:
    font_badge = ImageFont.truetype(str(font_path), int(h * 0.055))
    font_main = ImageFont.truetype(str(font_path), int(h * 0.125))
    
    # 1. Top Badge Pill
    badge_txt = "حكاية من بطن الجبل | دفتر راوي"
    badge_reshaped = get_display(arabic_reshaper.reshape(badge_txt))
    bbox = font_badge.getbbox(badge_reshaped)
    bw = bbox[2] - bbox[0]
    bh = bbox[3] - bbox[1]
    
    pad_x, pad_y = 28, 14
    bx0, by0 = w - bw - pad_x * 2 - 40, 40
    bx1, by1 = w - 40, by0 + bh + pad_y * 2
    
    # Draw badge background
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.rounded_rectangle([bx0, by0, bx1, by1], radius=16, fill=(220, 20, 60, 220), outline=(255, 215, 0, 255), width=3)
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    draw_ar_text(draw, badge_txt, (bx0 + pad_x, by0 + pad_y - 4), font_badge, fill=(255, 255, 255), shadow_fill=(0, 0, 0))
    
    # 2. Main Shock Hook Text at Bottom-Right
    hook_txt = "السر الصادم في القاع!"
    hook_reshaped = get_display(arabic_reshaper.reshape(hook_txt))
    hbbox = font_main.getbbox(hook_reshaped)
    hw = hbbox[2] - hbbox[0]
    hh = hbbox[3] - hbbox[1]
    
    hx = w - hw - 60
    hy = h - hh - 70
    
    # Draw shadow backing pill for readability
    poverlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    podraw = ImageDraw.Draw(poverlay)
    podraw.rounded_rectangle([hx - 30, hy - 15, w - 30, hy + hh + 25], radius=20, fill=(0, 0, 0, 190), outline=(255, 215, 0, 230), width=4)
    img = Image.alpha_composite(img.convert("RGBA"), poverlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    draw_ar_text(draw, hook_txt, (hx, hy), font_main, fill=(255, 220, 0), shadow_fill=(0, 0, 0), shadow_offset=(5, 5))
    
    img.save(str(thumb_path), quality=95)
    print("Successfully rendered high-CTR YouTube typography on thumbnail!")
except Exception as e:
    print("Error rendering text:", e)
