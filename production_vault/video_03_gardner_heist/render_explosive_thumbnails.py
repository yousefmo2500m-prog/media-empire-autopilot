import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

cairo_font = "/home/user/media-empire-autopilot/fonts/Cairo-Variable.ttf"
base_thumb = "/home/user/thumbnail_gardner_raw.jpg"
if not os.path.exists(base_thumb):
    base_thumb = "/home/user/media-empire-autopilot/production_vault/video_03_gardner_heist/thumbnail_gardner_raw.jpg"

def render_explosive_arabic_thumbnail():
    im = Image.open(base_thumb).convert("RGBA")
    im = im.resize((1280, 720), Image.Resampling.LANCZOS)
    
    im = ImageEnhance.Contrast(im).enhance(1.22)
    im = ImageEnhance.Color(im).enhance(1.25)
    
    overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    d_over = ImageDraw.Draw(overlay)
    
    # 1. 100% opaque solid top bar to completely mask "HEIST"
    d_over.rectangle([0, 0, 1280, 108], fill=(12, 14, 20, 255))
    d_over.line([(0, 108), (1280, 108)], fill=(255, 215, 0, 240), width=3)
    
    # 2. Darken bottom strongly (y: 530 to 720) to hide credit text completely
    for y in range(530, 610):
        prog = (y - 530) / 80.0
        alpha = int(prog * 255)
        d_over.line([(0, y), (1280, y)], fill=(8, 10, 15, alpha))
    d_over.rectangle([0, 610, 1280, 720], fill=(8, 10, 15, 255))
    
    im = Image.alpha_composite(im, overlay)
    draw = ImageDraw.Draw(im)
    
    # 1. Top-Left Badge: Red Pill -> "سرقة الـ 500 مليون دولار!"
    f_badge = ImageFont.truetype(cairo_font, 38)
    b_text = "سرقة الـ 500 مليون دولار!"
    bx, by, bw, bh = 25, 18, 560, 72
    draw.rounded_rectangle([bx+3, by+3, bx+bw+3, by+bh+3], radius=12, fill=(0, 0, 0, 220))
    draw.rounded_rectangle([bx, by, bx+bw, by+bh], radius=12, fill=(225, 25, 25), outline=(255, 230, 80), width=3)
    bbox_b = f_badge.getbbox(b_text, direction='rtl')
    tbw = bbox_b[2] - bbox_b[0]
    draw.text((bx + (bw - tbw)//2, by + 9), b_text, fill=(255, 255, 255), font=f_badge, direction='rtl')
    
    # 2. Top-Right Badge: Dark Slate Pill with Gold -> "لغز حير الـ FBI لـ 34 سنة!"
    f_badge_r = ImageFont.truetype(cairo_font, 35)
    r_text = "لغز حير الـ FBI لـ 34 سنة!"
    rx, ry, rw, rh = 695, 18, 560, 72
    draw.rounded_rectangle([rx+3, ry+3, rx+rw+3, ry+rh+3], radius=12, fill=(0, 0, 0, 220))
    draw.rounded_rectangle([rx, ry, rx+rw, ry+rh], radius=12, fill=(22, 28, 40), outline=(255, 215, 0), width=3)
    bbox_r = f_badge_r.getbbox(r_text, direction='rtl')
    trw = bbox_r[2] - bbox_r[0]
    draw.text((rx + (rw - trw)//2, ry + 11), r_text, fill=(255, 225, 20), font=f_badge_r, direction='rtl')
    
    # 3. Bottom Massive Hook Headline:
    # "أكبر عملية سرقة في التاريخ!"
    f_huge = ImageFont.truetype(cairo_font, 76)
    h_text = "أكبر عملية سرقة في التاريخ!"
    bbox = f_huge.getbbox(h_text, direction='rtl')
    tw = bbox[2] - bbox[0]
    hx = (1280 - tw) // 2
    hy = 600
    
    # Red accent bar just above text at hy - 14
    draw.line([(hx - 15, hy - 12), (hx + tw + 15, hy - 12)], fill=(225, 25, 25), width=4)
    
    for ox in range(-5, 6):
        for oy in range(-5, 6):
            if ox != 0 or oy != 0:
                draw.text((hx + ox, hy + oy), h_text, fill=(0, 0, 0), font=f_huge, direction='rtl')
            
    draw.text((hx, hy), h_text, fill=(255, 235, 15), font=f_huge, direction='rtl')
    
    out_path = "/home/user/thumbnail_gardner_egyptian_blockbuster.jpg"
    im.convert("RGB").save(out_path, quality=96)
    print("Explosive Arabic thumbnail saved:", out_path)

def render_explosive_english_thumbnail():
    im = Image.open(base_thumb).convert("RGBA")
    im = im.resize((1280, 720), Image.Resampling.LANCZOS)
    
    im = ImageEnhance.Contrast(im).enhance(1.22)
    im = ImageEnhance.Color(im).enhance(1.25)
    
    overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    d_over = ImageDraw.Draw(overlay)
    
    d_over.rectangle([0, 0, 1280, 108], fill=(12, 14, 20, 255))
    d_over.line([(0, 108), (1280, 108)], fill=(255, 215, 0, 240), width=3)
    
    for y in range(530, 610):
        prog = (y - 530) / 80.0
        alpha = int(prog * 255)
        d_over.line([(0, y), (1280, y)], fill=(8, 10, 15, alpha))
    d_over.rectangle([0, 610, 1280, 720], fill=(8, 10, 15, 255))
    
    im = Image.alpha_composite(im, overlay)
    draw = ImageDraw.Draw(im)
    
    # Left: "$500,000,000 HEIST"
    f_badge = ImageFont.truetype(cairo_font, 38)
    b_text = "$500,000,000 HEIST"
    bx, by, bw, bh = 25, 18, 520, 72
    draw.rounded_rectangle([bx+3, by+3, bx+bw+3, by+bh+3], radius=12, fill=(0, 0, 0, 220))
    draw.rounded_rectangle([bx, by, bx+bw, by+bh], radius=12, fill=(225, 25, 25), outline=(255, 230, 80), width=3)
    bbox_b = f_badge.getbbox(b_text)
    tbw = bbox_b[2] - bbox_b[0]
    draw.text((bx + (bw - tbw)//2, by + 9), b_text, fill=(255, 255, 255), font=f_badge)
    
    # Right: "UNSOLVED FOR 34 YEARS!"
    f_badge_r = ImageFont.truetype(cairo_font, 35)
    r_text = "UNSOLVED FOR 34 YEARS!"
    rx, ry, rw, rh = 695, 18, 560, 72
    draw.rounded_rectangle([rx+3, ry+3, rx+rw+3, ry+rh+3], radius=12, fill=(0, 0, 0, 220))
    draw.rounded_rectangle([rx, ry, rx+rw, ry+rh], radius=12, fill=(22, 28, 40), outline=(255, 215, 0), width=3)
    bbox_r = f_badge_r.getbbox(r_text)
    trw = bbox_r[2] - bbox_r[0]
    draw.text((rx + (rw - trw)//2, ry + 11), r_text, fill=(255, 225, 20), font=f_badge_r)
    
    # Bottom: "THE BIGGEST HEIST IN HISTORY!"
    f_huge = ImageFont.truetype(cairo_font, 68)
    h_text = "THE BIGGEST HEIST IN HISTORY!"
    bbox = f_huge.getbbox(h_text)
    tw = bbox[2] - bbox[0]
    hx = (1280 - tw) // 2
    hy = 605
    
    draw.line([(hx - 15, hy - 12), (hx + tw + 15, hy - 12)], fill=(225, 25, 25), width=4)
    
    for ox in range(-5, 6):
        for oy in range(-5, 6):
            if ox != 0 or oy != 0:
                draw.text((hx + ox, hy + oy), h_text, fill=(0, 0, 0), font=f_huge)
            
    draw.text((hx, hy), h_text, fill=(255, 235, 15), font=f_huge)
    
    out_path = "/home/user/thumbnail_gardner_english_blockbuster.jpg"
    im.convert("RGB").save(out_path, quality=96)
    print("Explosive English thumbnail saved:", out_path)

render_explosive_arabic_thumbnail()
render_explosive_english_thumbnail()
