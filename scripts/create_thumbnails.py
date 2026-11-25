import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

cairo_font_path = "/home/user/media-empire-autopilot/fonts/Cairo-Variable.ttf"
base_thumb = "/home/user/thumbnail_gardner_egyptian_blockbuster.jpg"

def create_arabic_thumb():
    im = Image.open(base_thumb).convert("RGBA")
    im = im.resize((1280, 720), Image.Resampling.LANCZOS)
    
    # Increase contrast and color saturation slightly for high CTR
    enhancer = ImageEnhance.Contrast(im)
    im = enhancer.enhance(1.15)
    enhancer = ImageEnhance.Color(im)
    im = enhancer.enhance(1.2)
    
    draw = ImageDraw.Draw(im)
    
    # Red badge top-left: "$500,000,000"
    badge_x, badge_y = 40, 40
    badge_w, badge_h = 360, 80
    draw.rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], fill=(220, 20, 20, 235), outline=(255, 255, 255, 255), width=4)
    
    f_badge = ImageFont.truetype(cairo_font_path, 44)
    draw.text((badge_x + 25, badge_y + 10), "500,000,000 $", fill=(255, 255, 255), font=f_badge)
    
    # Bottom banner
    f_title = ImageFont.truetype(cairo_font_path, 62)
    text = "أكبر سرقة فنية في التاريخ!"
    
    # Dark gradient overlay at bottom
    overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    d_over = ImageDraw.Draw(overlay)
    d_over.rectangle([0, 580, 1280, 720], fill=(0, 0, 0, 190))
    im = Image.alpha_composite(im, overlay)
    draw = ImageDraw.Draw(im)
    
    # Yellow text with thick black border
    x, y = 300, 610
    for ox in range(-4, 5):
        for oy in range(-4, 5):
            draw.text((x + ox, y + oy), text, fill=(0, 0, 0), font=f_title)
    draw.text((x, y), text, fill=(255, 215, 0), font=f_title)
    
    out_path = "/home/user/thumbnail_gardner_egyptian_blockbuster.jpg"
    im.convert("RGB").save(out_path, quality=95)
    print("Arabic thumbnail saved:", out_path)

def create_english_thumb():
    im = Image.open(base_thumb).convert("RGBA")
    im = im.resize((1280, 720), Image.Resampling.LANCZOS)
    
    enhancer = ImageEnhance.Contrast(im)
    im = enhancer.enhance(1.15)
    enhancer = ImageEnhance.Color(im)
    im = enhancer.enhance(1.2)
    
    draw = ImageDraw.Draw(im)
    
    # Red badge
    badge_x, badge_y = 40, 40
    badge_w, badge_h = 360, 80
    draw.rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], fill=(220, 20, 20, 235), outline=(255, 255, 255, 255), width=4)
    
    f_badge = ImageFont.truetype(cairo_font_path, 44)
    draw.text((badge_x + 30, badge_y + 10), "$500 MILLION", fill=(255, 255, 255), font=f_badge)
    
    # Bottom banner
    f_title = ImageFont.truetype(cairo_font_path, 56)
    text = "THE GREATEST UNSOLVED HEIST"
    
    overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    d_over = ImageDraw.Draw(overlay)
    d_over.rectangle([0, 580, 1280, 720], fill=(0, 0, 0, 190))
    im = Image.alpha_composite(im, overlay)
    draw = ImageDraw.Draw(im)
    
    x, y = 180, 615
    for ox in range(-4, 5):
        for oy in range(-4, 5):
            draw.text((x + ox, y + oy), text, fill=(0, 0, 0), font=f_title)
    draw.text((x, y), text, fill=(255, 215, 0), font=f_title)
    
    out_path = "/home/user/thumbnail_gardner_english_blockbuster.jpg"
    im.convert("RGB").save(out_path, quality=95)
    print("English thumbnail saved:", out_path)

create_arabic_thumb()
create_english_thumb()
