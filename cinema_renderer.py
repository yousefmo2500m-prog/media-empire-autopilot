# -*- coding: utf-8 -*-
"""
محرك الإخراج البصري السينمائي (Multi-Scene Ken Burns Cinema & Thumbnail Renderer)
- يجلب لوحات المشاهد بالذكاء الاصطناعي مجاناً مع قص أمان 12% من جميع الحواف (صفر علامات مائية)
  مع مولّد مشاهد ضوئية احتياطي يعمل بدون إنترنت لضمان عدم تعطل أي حلقة لمدة سنتين.
- يطبّق حركة كاميرا Ken Burns ناعمة، انتقالات تلاشي (Cross-Dissolve)، ذرات ضوء عائمة،
  بطاقة المتحدث النشط، وترجمة سينمائية واضحة بخط Cairo.
"""

import io
import math
import subprocess
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Tuple

import imageio_ffmpeg
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()
FONT_PATH = Path(__file__).resolve().parent / "fonts" / "Cairo-Variable.ttf"
FPS = 24
_ART_CACHE: Dict[Tuple[str, int, int], Image.Image] = {}


def _clean_glyphs(text: str) -> str:
    """إزالة الإيموجي غير المدعومة في ملف الخط لضمان عدم ظهور مربعات فارغة نهائياً."""
    import re

    cleaned = re.sub(
        r"[\U00010000-\U0010ffff\u2600-\u27bf\ufe0f]",
        "",
        str(text or ""),
    )
    return " ".join(cleaned.split()).strip()


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size=size)


def _crop_border_safety(img: Image.Image, ratio: float = 0.12) -> Image.Image:
    """قص 12% من الحواف الأربع لإزالة أي شعارات طرفية وضمان نقاء الكادر السينمائي 100%."""
    w, h = img.size
    dx = int(w * ratio)
    dy = int(h * ratio)
    return img.crop((dx, dy, w - dx, h - dy))


def _procedural_cinema_backdrop(
    width: int,
    height: int,
    palette: Dict[str, Any],
    seed: int,
) -> Image.Image:
    """مشهد سينمائي ضوئي احتياطي فخم يعمل حتى عند بطء الشبكة."""
    rng = np.random.default_rng(seed)
    y = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, None]
    x = np.linspace(0.0, 1.0, width, dtype=np.float32)[None, :]

    top = np.array(palette["bg_top"], dtype=np.float32)
    bot = np.array(palette["bg_bottom"], dtype=np.float32)
    acc = np.array(palette["accent"], dtype=np.float32)

    grad = top[None, None, :] * (1.0 - y[..., None]) + bot[None, None, :] * y[..., None]
    canvas = np.broadcast_to(grad, (height, width, 3)).copy()

    # شعاع إضاءة حجمي درامي + هالة قمرية/مصباح دافئ
    cx = 0.28 + 0.44 * ((seed % 5) / 4.0)
    cy = 0.28 + 0.12 * ((seed % 3) / 2.0)
    beam = np.exp(-(((x - cx) * 1.8) ** 2 + ((y - cy) * 1.4) ** 2))
    mist = np.exp(-(((y - 0.68) * 4.2) ** 2)) * (0.5 + 0.5 * np.sin(x * 7.0 + seed))
    canvas += acc[None, None, :] * (beam[..., None] * 0.42)
    canvas += np.array([180.0, 195.0, 225.0], dtype=np.float32)[None, None, :] * (mist[..., None] * 0.14)

    img = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8), mode="RGB")
    draw = ImageDraw.Draw(img, "RGBA")

    # أفق معماري ليلي ظلي (Silhouettes + نوافذ مضيئة خافتة)
    horizon_y = int(height * 0.72)
    bx = 0
    while bx < width:
        bw = int(rng.uniform(width * 0.06, width * 0.15))
        bh = int(rng.uniform(height * 0.14, height * 0.38))
        btop = horizon_y - bh
        draw.rectangle((bx, btop, bx + bw, height), fill=(6, 8, 15, 235))
        # نافذة مضيئة دافئة
        if rng.random() > 0.35 and bw > 40:
            wx = bx + bw // 2 - 8
            wy = btop + int(bh * 0.28)
            draw.rectangle((wx, wy, wx + 14, wy + 22), fill=(*palette["accent"], 175))
        bx += bw - int(rng.uniform(4, 18))

    for _ in range(42):
        px = int(rng.uniform(0, width))
        py = int(rng.uniform(0, height * 0.80))
        r = int(rng.uniform(2, 8))
        alpha = int(rng.uniform(25, 95))
        draw.ellipse((px - r, py - r, px + r, py + r), fill=(*palette["accent"], alpha))
    return img.filter(ImageFilter.GaussianBlur(radius=1.2))


def fetch_scene_artwork(
    prompt_en: str,
    target_w: int,
    target_h: int,
    palette: Dict[str, Any],
    seed: int,
) -> Image.Image:
    """جلب لوحة المشهد وتجهيزها بمقاس أكبر بنسبة 18% لحركة الكاميرا السلسة."""
    import time

    overscale_w = int(target_w * 1.18)
    overscale_h = int(target_h * 1.18)

    req_w = 1280 if target_w >= target_h else 768
    req_h = 768 if target_w >= target_h else 1280
    short_prompt = " ".join(prompt_en.split()[:16])
    cache_key = (short_prompt, overscale_w, overscale_h)
    if cache_key in _ART_CACHE:
        return _ART_CACHE[cache_key].copy()

    clean_prompt = f"{short_prompt}, cinematic dark lighting, no text"
    encoded = urllib.parse.quote(clean_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={req_w}&height={req_h}&nologo=true&seed={seed}"

    img = None
    for attempt in range(3):
        try:
            if attempt > 0:
                time.sleep(3.2 * attempt)
            r = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) MediaStudio/1.0"},
                timeout=28,
            )
            if r.status_code == 200 and len(r.content) > 8000:
                raw = Image.open(io.BytesIO(r.content)).convert("RGB")
                img = _crop_border_safety(raw, ratio=0.12)
                time.sleep(3.2)  # احترام معدل الطلبات المجاني لضمان نجاح كل المشاهد
                break
        except Exception:
            time.sleep(2.5)

    if img is None:
        img = _procedural_cinema_backdrop(overscale_w, overscale_h, palette, seed)

    # ضبط النسبة والملء الكامل بدون تشويه
    src_ratio = img.width / img.height
    dst_ratio = overscale_w / overscale_h
    if src_ratio > dst_ratio:
        new_h = overscale_h
        new_w = int(new_h * src_ratio)
    else:
        new_w = overscale_w
        new_h = int(new_w / src_ratio)

    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - overscale_w) // 2
    top = (new_h - overscale_h) // 2
    img = img.crop((left, top, left + overscale_w, top + overscale_h))

    # تدريج لوني سينمائي (Cinema Color Grade)
    img = ImageEnhance.Contrast(img).enhance(1.12)
    img = ImageEnhance.Brightness(img).enhance(0.84)
    _ART_CACHE[cache_key] = img.copy()
    return img


def _wrap_text_lines(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> List[str]:
    words = text.split()
    lines: List[str] = []
    current = ""
    for w in words:
        cand = f"{current} {w}".strip()
        bbox = draw.textbbox((0, 0), cand, font=font)
        if (bbox[2] - bbox[0]) <= max_w or not current:
            current = cand
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines[:4]


def _make_vignette_mask(width: int, height: int) -> Image.Image:
    """قناع تظليل سينمائي للحواف والجزء السفلي لوضوح الترجمة بنسبة 100%."""
    y = np.linspace(-1.0, 1.0, height, dtype=np.float32)[:, None]
    x = np.linspace(-1.0, 1.0, width, dtype=np.float32)[None, :]
    rad = np.clip((x**2 + y**2) * 0.58, 0.0, 1.0)
    # تعتيم إضافي أسفل وأعلى الكادر
    ynorm = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, None]
    bottom_shade = np.clip((ynorm - 0.52) / 0.48, 0.0, 1.0) * 0.78
    top_shade = np.clip((0.18 - ynorm) / 0.18, 0.0, 1.0) * 0.55
    alpha = np.clip(rad * 0.55 + bottom_shade + top_shade, 0.0, 0.90) * 255.0
    rgba = np.zeros((height, width, 4), dtype=np.uint8)
    rgba[..., 3] = alpha.astype(np.uint8)
    return Image.fromarray(rgba, mode="RGBA")


def _prebuild_segment_overlay(
    width: int,
    height: int,
    channel_cfg: Dict[str, Any],
    episode_badge: str,
    location_caption: str,
    speaker_badge: str,
    subtitle_text: str,
) -> Image.Image:
    """تجهيز طبقة النصوص الشفافة لكل جملة مسبقاً لسرعة ريندر فائقة ونصوص حادة."""
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    palette = channel_cfg["palette"]
    accent = palette["accent"]
    is_vertical = height > width

    font_brand = _load_font(26 if is_vertical else 22)
    font_loc = _load_font(24 if is_vertical else 20)
    font_spk = _load_font(28 if is_vertical else 24)
    font_sub = _load_font(42 if is_vertical else 34)

    pad_x = 46 if is_vertical else 54
    top_y = 48 if is_vertical else 28

    episode_badge = _clean_glyphs(episode_badge)
    location_caption = _clean_glyphs(location_caption)
    speaker_badge = _clean_glyphs(speaker_badge) or "الراوي"
    subtitle_text = _clean_glyphs(subtitle_text)

    # شارة اسم القناة والحلقة أعلى اليمين/اليسار
    header_txt = f"{_clean_glyphs(channel_cfg['brand_name'])}  •  {episode_badge}"
    hb = draw.textbbox((0, 0), header_txt, font=font_brand)
    hw, hh = hb[2] - hb[0], hb[3] - hb[1]
    hx = width - pad_x - hw - 32 if channel_cfg["language"] == "ar" else pad_x
    draw.rounded_rectangle(
        (hx, top_y, hx + hw + 32, top_y + hh + 20),
        radius=14,
        fill=(12, 14, 24, 205),
        outline=(*accent, 180),
        width=2,
    )
    draw.text((hx + 16, top_y + 7), header_txt, font=font_brand, fill=(255, 255, 255, 245))

    # شارة المكان والزمان للمشهد
    if location_caption:
        lb = draw.textbbox((0, 0), location_caption, font=font_loc)
        lw, lh = lb[2] - lb[0], lb[3] - lb[1]
        lx = hx + (hw + 32 - lw - 26) if channel_cfg["language"] == "ar" else pad_x
        ly = top_y + hh + 30
        draw.rounded_rectangle(
            (lx, ly, lx + lw + 26, ly + lh + 16),
            radius=10,
            fill=(18, 20, 32, 175),
        )
        draw.text((lx + 13, ly + 5), location_caption, font=font_loc, fill=(*accent, 240))

    # منطقة الترجمة السينمائية وبطاقة المتحدث بالأسفل
    max_sub_w = width - pad_x * 2 - 48
    lines = _wrap_text_lines(draw, subtitle_text, font_sub, max_sub_w)
    line_h = 58 if is_vertical else 48
    box_h = len(lines) * line_h + 44
    box_bottom = height - (135 if is_vertical else 52)
    box_top = box_bottom - box_h

    draw.rounded_rectangle(
        (pad_x, box_top, width - pad_x, box_bottom),
        radius=22,
        fill=(10, 12, 22, 212),
        outline=(255, 255, 255, 48),
        width=2,
    )

    # بطاقة اسم الشخصية المتحدثة أعلى صندوق الحوار
    sb = draw.textbbox((0, 0), speaker_badge, font=font_spk)
    sw, sh = sb[2] - sb[0], sb[3] - sb[1]
    sx = (width - pad_x - sw - 38) if channel_cfg["language"] == "ar" else (pad_x + 20)
    pill_h = sh + 22
    sy = box_top - pill_h // 2 - 4
    draw.rounded_rectangle(
        (sx, sy, sx + sw + 38, sy + pill_h),
        radius=14,
        fill=(*accent, 245),
    )
    draw.text((sx + 19 - sb[0], sy + (pill_h - sh) // 2 - sb[1]), speaker_badge, font=font_spk, fill=(12, 14, 22, 255))

    # كتابة أسطر الحوار في المنتصف بوضوح فائق
    curr_y = box_top + 20
    for ln in lines:
        tb = draw.textbbox((0, 0), ln, font=font_sub)
        tw = tb[2] - tb[0]
        tx = (width - tw) // 2
        draw.text(
            (tx, curr_y),
            ln,
            font=font_sub,
            fill=(*palette["text_main"], 255),
            stroke_width=2,
            stroke_fill=(0, 0, 0, 220),
        )
        curr_y += line_h

    return overlay


def render_cinema_video(
    channel_cfg: Dict[str, Any],
    script_data: Dict[str, Any],
    timed_segments: List[Dict[str, Any]],
    audio_wav: Path,
    out_mp4: Path,
    aspect: str = "16:9",
    seed: int = 2026,
) -> Path:
    """تركيب الحلقة الكاملة بالفيديو والصوت والمؤثرات البصرية وحفظها بصيغة MP4 جاهزة للنشر."""
    if aspect == "16:9":
        width, height = 1280, 720
    else:
        width, height = 1080, 1920

    scenes_list = script_data.get("scenes") or [{"scene_id": 1, "visual_prompt_en": "dark mysterious study room", "location_caption": ""}]
    scene_map: Dict[int, Dict[str, Any]] = {}
    for idx, sc in enumerate(scenes_list):
        sid = int(sc.get("scene_id", idx + 1))
        art = fetch_scene_artwork(
            prompt_en=sc.get("visual_prompt_en", "cinematic atmospheric scene"),
            target_w=width,
            target_h=height,
            palette=channel_cfg["palette"],
            seed=seed + sid * 37,
        )
        scene_map[sid] = {
            "art": art,
            "location_caption": sc.get("location_caption", ""),
            "pan_dir": 1 if sid % 2 == 1 else -1,
        }

    default_sid = next(iter(scene_map.keys()))

    # شارة الحلقة
    if "episode_number" in script_data:
        ep_badge = f"الحلقة {script_data['episode_number']} من {script_data.get('total_episodes', 4)}"
    else:
        ep_badge = "وثائقي خاص" if channel_cfg["language"] == "ar" else "SPECIAL DOSSIER"

    # تجهيز طبقات النصوص لكل مقطع صوتي
    for seg in timed_segments:
        sid = int(seg.get("scene_id", default_sid))
        if sid not in scene_map:
            sid = default_sid
        seg["_resolved_sid"] = sid
        seg["_overlay"] = _prebuild_segment_overlay(
            width=width,
            height=height,
            channel_cfg=channel_cfg,
            episode_badge=ep_badge,
            location_caption=scene_map[sid]["location_caption"],
            speaker_badge=seg.get("speaker_badge", "🎙️"),
            subtitle_text=seg["text"],
        )

    # حساب زمن كل مشهد لحركة الكاميرا المستمرة
    scene_spans: Dict[int, Tuple[float, float]] = {}
    for seg in timed_segments:
        sid = seg["_resolved_sid"]
        s0, s1 = seg["start_sec"], seg["end_sec"]
        if sid not in scene_spans:
            scene_spans[sid] = (s0, s1)
        else:
            scene_spans[sid] = (min(scene_spans[sid][0], s0), max(scene_spans[sid][1], s1))

    # معرفة الطول الدقيق لملف الصوت
    import wave

    with wave.open(str(audio_wav), "rb") as wf:
        total_duration = wf.getnframes() / float(wf.getframerate())

    total_frames = max(1, int(math.ceil(total_duration * FPS)))
    vignette = _make_vignette_mask(width, height)
    accent = channel_cfg["palette"]["accent"]

    # ذرات ضوء سينمائية عائمة
    rng = np.random.default_rng(seed)
    motes = [
        (
            rng.uniform(0.05, 0.95),
            rng.uniform(0.10, 0.80),
            rng.uniform(0.008, 0.022),
            int(rng.uniform(2, 5)),
        )
        for _ in range(18)
    ]

    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        FFMPEG_BIN,
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{width}x{height}",
        "-r",
        str(FPS),
        "-i",
        "pipe:0",
        "-i",
        str(audio_wav),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "21",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        "-loglevel",
        "error",
        str(out_mp4),
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    seg_idx = 0
    n_segs = len(timed_segments)

    try:
        for f_idx in range(total_frames):
            t_sec = f_idx / float(FPS)

            # تحديد المقطع النصي والمشهد النشط حالياً
            while seg_idx + 1 < n_segs and t_sec >= timed_segments[seg_idx + 1]["start_sec"] - 0.12:
                seg_idx += 1

            active_seg = timed_segments[seg_idx]
            sid = active_seg["_resolved_sid"]
            sc_info = scene_map[sid]
            art: Image.Image = sc_info["art"]

            sc_start, sc_end = scene_spans.get(sid, (0.0, total_duration))
            sc_progress = np.clip((t_sec - sc_start) / max(0.5, sc_end - sc_start), 0.0, 1.0)

            # حركة كاميرا Ken Burns ناعمة (تقريب تدريجي + إزاحة أفقية هادئة)
            zoom = 1.0 + 0.11 * sc_progress
            crop_w = int(art.width / zoom)
            crop_h = int(art.height / zoom)
            max_dx = max(0, art.width - crop_w)
            max_dy = max(0, art.height - crop_h)
            pan_frac = sc_progress if sc_info["pan_dir"] > 0 else (1.0 - sc_progress)
            cx = int(max_dx * pan_frac)
            cy = int(max_dy * 0.5)

            frame = art.crop((cx, cy, cx + crop_w, cy + crop_h)).resize(
                (width, height), Image.Resampling.BILINEAR
            ).convert("RGBA")

            frame.alpha_composite(vignette)

            # ذرات الضوء العائمة وشريط التقدم
            fx_draw = ImageDraw.Draw(frame, "RGBA")
            for mx, my, mspeed, mr in motes:
                py = ((my - t_sec * mspeed) % 0.85) * height
                px = (mx + 0.02 * math.sin(t_sec * 0.9 + mx * 10.0)) * width
                fx_draw.ellipse((px - mr, py - mr, px + mr, py + mr), fill=(*accent, 85))

            # إظهار نص المتحدث خلال فترة نطقه
            if active_seg["start_sec"] - 0.15 <= t_sec <= active_seg["end_sec"] + 0.35:
                frame.alpha_composite(active_seg["_overlay"])

            # شريط تقدم أنيق أسفل الفيديو
            prog_w = int((t_sec / max(0.1, total_duration)) * width)
            fx_draw.rectangle((0, height - 8, prog_w, height), fill=(*accent, 235))

            proc.stdin.write(frame.convert("RGB").tobytes())
    finally:
        if proc.stdin:
            proc.stdin.close()
        ret = proc.wait()
        if ret != 0:
            raise RuntimeError(f"FFmpeg exited with code {ret}")

    return out_mp4


def render_youtube_thumbnail(
    channel_cfg: Dict[str, Any],
    script_data: Dict[str, Any],
    out_jpg: Path,
    seed: int = 2026,
) -> Path:
    """توليد صورة مصغرة احترافية (1280x720) عالية النقر (High CTR) تلقائياً لكل فيديو يوتيوب."""
    w, h = 1280, 720
    scenes = script_data.get("scenes") or [{}]
    first_sid = int(scenes[0].get("scene_id", 1))
    art = fetch_scene_artwork(
        prompt_en=scenes[0].get("visual_prompt_en", "dramatic mystery scene"),
        target_w=w,
        target_h=h,
        palette=channel_cfg["palette"],
        seed=seed + first_sid * 37,
    ).resize((w, h), Image.Resampling.LANCZOS).convert("RGBA")

    vignette = _make_vignette_mask(w, h)
    art.alpha_composite(vignette)

    draw = ImageDraw.Draw(art, "RGBA")
    accent = channel_cfg["palette"]["accent"]

    # إطار ذهبي/سماوي خارجي خفيف يلفت العين في نتائج البحث
    draw.rectangle((8, 8, w - 8, h - 8), outline=(*accent, 230), width=6)

    headline = _clean_glyphs(script_data.get("thumbnail_headline") or script_data.get("episode_title", ""))
    font_big = _load_font(74)
    font_tag = _load_font(34)

    tag_txt = _clean_glyphs(
        f"{script_data.get('novel_title', channel_cfg['brand_name'])} • الحلقة {script_data['episode_number']}"
        if "episode_number" in script_data
        else channel_cfg["brand_name"]
    )
    tb = draw.textbbox((0, 0), tag_txt, font=font_tag)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    tx = (w - tw - 44) // 2
    draw.rounded_rectangle((tx, 54, tx + tw + 44, 54 + th + 24), radius=16, fill=(*accent, 245))
    draw.text((tx + 22, 61), tag_txt, font=font_tag, fill=(12, 14, 22, 255))

    lines = _wrap_text_lines(draw, headline, font_big, w - 160)[:2]
    y_cursor = h - 115 - len(lines) * 95
    for ln in lines:
        lb = draw.textbbox((0, 0), ln, font=font_big)
        lw = lb[2] - lb[0]
        lx = (w - lw) // 2
        draw.text(
            (lx, y_cursor),
            ln,
            font=font_big,
            fill=(255, 255, 255, 255),
            stroke_width=5,
            stroke_fill=(0, 0, 0, 245),
        )
        y_cursor += 96

    out_jpg.parent.mkdir(parents=True, exist_ok=True)
    art.convert("RGB").save(str(out_jpg), quality=92)
    return out_jpg
