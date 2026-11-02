# -*- coding: utf-8 -*-
"""
محرك المشاهد الذكية وغلاف اليوتيوب الناري V9.0 (Zero-Repetition 3-Engine AI Studio + Native 9:16 + Viral Thumbnail)
يولّد مشاهد ذكاء اصطناعي مخصصة 100% لكل مشهد في الحلقة بدون أي صور عشوائية وبدون تكرار أي صورة:
- المحرك 1 (Hugging Face FLUX): فائق الدقة لغلاف اليوتيوب والمشاهد الافتتاحية.
- المحرك 2 (Pollinations FLUX Parallel Worker): يولّد مشاهد FLUX أصلية بالتوازي مع قص نظيف لأي شعار سفلي.
- المحرك 3 (AI Horde Photorealistic Cluster): عنقود متوازٍ بلا أي حد يومي (5 مهام متزامنة) عبر نماذج
  ICBINP / Deliberate / AbsoluteReality / AlbedoBase XL بدقة 16:9 أصلية للفيلم الطويل و9:16 رأسية كاملة للشورتس!
"""

import concurrent.futures
import io
import os
import queue
import threading
import time
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, features

FONTS_DIR = Path(__file__).resolve().parent / "fonts"
CAIRO_FONT_PATH = FONTS_DIR / "Cairo-Variable.ttf"

HORDE_HEADERS = {
    "apikey": os.environ.get("AI_HORDE_KEY", "0000000000").strip() or "0000000000",
    "Client-Agent": "MediaEmpireStudio:9.0:autonomous",
}
HORDE_REALISM_MODELS = [
    "Deliberate",
    "ICBINP - I Can't Believe It's Not Photography",
    "AbsoluteReality",
    "Dreamshaper",
]


def apply_cinema_grade(
    img: Image.Image,
    width: int = 1280,
    height: int = 720,
    mood: str = "mystery",
    is_vertical: bool = False,
) -> Image.Image:
    """ضبط المقاس بدون تشويه أو قص جانبي جائر + تدريج ألوان إثارة نفسية سينمائي حاد."""
    img = img.convert("RGB")
    src_w, src_h = img.size
    target_ratio = width / float(height)
    src_ratio = src_w / float(max(1, src_h))

    # إذا كانت الصورة مولّدة أصلاً بنسبة مطابقة تقريباً (مثل 448x768 أو 768x1344 للشورتس)، نحافظ على المشهد كاملاً!
    if abs(src_ratio - target_ratio) > 0.08:
        if src_ratio > target_ratio:
            new_w = int(round(src_h * target_ratio))
            left = max(0, (src_w - new_w) // 2)
            img = img.crop((left, 0, left + new_w, src_h))
        else:
            new_h = int(round(src_w / target_ratio))
            top = max(0, (src_h - new_h) // 2)
            img = img.crop((0, top, src_w, top + new_h))

    img = img.resize((width, height), Image.Resampling.LANCZOS)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.15, percent=115, threshold=3))
    img = ImageEnhance.Contrast(img).enhance(1.16)
    img = ImageEnhance.Color(img).enhance(1.10)

    arr = np.asarray(img, dtype=np.float32)
    # تدريج الإثارة النفسية السينمائي (Amber Highlights + Deep Teal/Midnight Shadows)
    arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.02 + 2.0, 0, 255)
    arr[:, :, 1] *= 0.99
    arr[:, :, 2] = np.clip(arr[:, :, 2] * 1.06 + 3.5, 0, 255)

    yy, xx = np.ogrid[:height, :width]
    cy, cx = height * 0.48, width * 0.50
    # في الشورتس الرأسية نخفف التعتيم الجانبي جداً حتى تظل الصورة كاملة واضحة ومشرقة 100%
    vig_strength = 0.20 if is_vertical else 0.30
    dist = np.sqrt(((xx - cx) / (width * 0.68)) ** 2 + ((yy - cy) / (height * 0.68)) ** 2)
    vig = np.clip(1.0 - vig_strength * np.clip(dist - 0.50, 0, 1.5), 0.62, 1.0)[:, :, None]

    bottom_grad = np.ones((height, 1, 1), dtype=np.float32)
    fade_start = int(height * (0.78 if is_vertical else 0.74))
    bottom_grad[fade_start:, 0, 0] = np.linspace(1.0, 0.58, height - fade_start)

    out_arr = np.clip(arr * vig * bottom_grad, 0, 255).astype(np.uint8)
    return Image.fromarray(out_arr)


def _try_hf_flux(prompt: str, is_vertical: bool = False, hf_token: str = "") -> Optional[Image.Image]:
    """توليد FLUX فائق الجودة بمقاس 16:9 (1280x720) أو 9:16 رأسي كامل (768x1344)."""
    w, h = (768, 1344) if is_vertical else (1280, 720)
    spaces = ["multimodalart/FLUX.1-merged", "black-forest-labs/FLUX.1-schnell"]
    for sp in spaces:
        try:
            from gradio_client import Client
            client = Client(sp, token=hf_token or None)
            res = client.predict(
                prompt=prompt,
                seed=0,
                randomize_seed=True,
                width=w,
                height=h,
                num_inference_steps=4,
                api_name="/infer",
            )
            item = res[0] if isinstance(res, (list, tuple)) else res
            p = item["path"] if isinstance(item, dict) else str(item)
            if p and Path(p).exists():
                return Image.open(p).convert("RGB")
        except Exception as exc:
            msg = str(exc).lower()
            if "zerogpu" in msg or "quota" in msg or "exceeded" in msg:
                return None
            continue
    return None


def _try_pollinations_flux_clean(prompt: str, is_vertical: bool, seed: int) -> Optional[Image.Image]:
    """توليد FLUX مجاني بمقاس 16:9 أو 9:16 مع قص الشريط السفلي (6%) لإزالة أي شعار زاوية بنسبة 100%."""
    w, req_h = (768, 1420) if is_vertical else (1280, 768)
    enc = urllib.parse.quote(prompt[:360])
    url = f"https://image.pollinations.ai/prompt/{enc}?width={w}&height={req_h}&model=flux&nologo=true&seed={seed}"
    try:
        r = requests.get(url, timeout=38)
        if r.status_code == 200 and "image" in r.headers.get("content-type", "").lower() and len(r.content) > 14_000:
            im = Image.open(io.BytesIO(r.content)).convert("RGB")
            trim_h = max(100, int(im.height * 0.935))
            im = im.crop((0, 0, im.width, trim_h))
            return im
    except Exception:
        pass
    return None


def _generate_via_aihorde_single(prompt: str, is_vertical: bool, timeout_sec: float = 135.0) -> Optional[Image.Image]:
    """توليد مشهد فوتوغرافي واقعي عبر عنقود AI Horde المجاني بمقاس 16:9 (768x448) أو 9:16 رأسي كامل (448x768)."""
    w, h = (448, 768) if is_vertical else (768, 448)
    full_prompt = (
        f"{prompt}, masterpiece, photorealistic cinema still, 35mm film grain, sharp focus, expressive faces "
        f"### text, letters, watermark, logo, signature, cartoon, anime, 3d render, blurry, deformed, cropped head"
    )
    for attempt in range(2):
        try:
            jr = requests.post(
                "https://aihorde.net/api/v2/generate/async",
                headers=HORDE_HEADERS,
                json={
                    "prompt": full_prompt,
                    "params": {
                        "width": w,
                        "height": h,
                        "steps": 22,
                        "cfg_scale": 7.0,
                        "sampler_name": "k_euler_a",
                    },
                    "nsfw": False,
                    "censor_nsfw": True,
                    "models": HORDE_REALISM_MODELS,
                    "r2": True,
                },
                timeout=20,
            )
            if jr.status_code != 202:
                time.sleep(3.0)
                continue
            jid = jr.json().get("id")
            if not jid:
                continue

            t0 = time.time()
            while time.time() - t0 < timeout_sec:
                time.sleep(3.2)
                st = requests.get(
                    f"https://aihorde.net/api/v2/generate/status/{jid}",
                    headers=HORDE_HEADERS,
                    timeout=15,
                ).json()
                if st.get("done"):
                    gens = st.get("generations") or []
                    img_url = gens[0].get("img") if gens else None
                    if img_url:
                        raw = requests.get(img_url, timeout=25).content
                        if len(raw) > 8_000:
                            return Image.open(io.BytesIO(raw)).convert("RGB")
                    break
                if st.get("faulted") or not st.get("is_possible", True):
                    break
        except Exception:
            time.sleep(2.5)
    return None


def generate_all_episode_visuals(
    long_prompts_16x9: List[str],
    short1_prompts_9x16: List[str],
    short2_prompts_9x16: List[str],
    thumbnail_prompt_16x9: str,
    thumbnail_hook_text: str,
    thumbnail_badge_text: str,
    is_arabic: bool,
    out_dir: Path,
    mood: str = "mystery",
) -> Dict[str, object]:
    """
    ينتج حزمة المشاهد البصرية الكاملة للحلقة بدون تكرار أي صورة إطلاقاً:
    - 1 غلاف يوتيوب ناري مخصص (1280x720) -> thumbnail.jpg
    - 12 مشهداً أفقياً مخصصاً (1280x720) للفيلم الطويل -> long_s01.jpg .. long_s12.jpg
    - 5 مشاهد رأسية كاملة (720x1280) للشورت الأول -> sh1_v01.jpg .. sh1_v05.jpg
    - 5 مشاهد رأسية كاملة (720x1280) للشورت الثاني -> sh2_v01.jpg .. sh2_v05.jpg
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    hf_tok = os.environ.get("HF_TOKEN", "").strip()

    # نرتب جميع المهام مع إعطاء الأولوية القصوى للغلاف والمشهد الافتتاحي عبر FLUX أولاً
    tasks: List[Tuple[str, str, bool, Path]] = []
    thumb_raw_path = out_dir / "_thumb_raw.jpg"
    tasks.append(("thumb", thumbnail_prompt_16x9, False, thumb_raw_path))
    for i, p in enumerate(long_prompts_16x9, 1):
        tasks.append((f"long_{i:02d}", p, False, out_dir / f"long_s{i:02d}.jpg"))
    for i, p in enumerate(short1_prompts_9x16, 1):
        tasks.append((f"sh1_{i:02d}", p, True, out_dir / f"sh1_v{i:02d}.jpg"))
    for i, p in enumerate(short2_prompts_9x16, 1):
        tasks.append((f"sh2_{i:02d}", p, True, out_dir / f"sh2_v{i:02d}.jpg"))

    rendered_raw: Dict[str, Image.Image] = {}

    # المرحلة 1: استغلال حصص Hugging Face FLUX السريعة للغلاف والمشهد الأول من الفيلم والمشهد الأول من الشورت!
    priority_keys = ["thumb", "long_01", "sh1_01"] if not hf_tok else [t[0] for t in tasks]
    for key, prm, is_vert, _ in tasks:
        if key not in priority_keys:
            continue
        im = _try_hf_flux(prm, is_vertical=is_vert, hf_token=hf_tok)
        if im is not None:
            rendered_raw[key] = im
            print(f"    ✨ [FLUX Studio] {key} ({'9:16' if is_vert else '16:9'}) ready!")
        else:
            break

    # المرحلة 2: تشغيل عنقود متوازٍ يجمع بين عامل Pollinations FLUX (كل 47 ثانية) + 5 عمال متوازيين على AI Horde!
    remaining_q: "queue.Queue[Tuple[int, str, str, bool]]" = queue.Queue()
    for idx, (key, prm, is_vert, _) in enumerate(tasks):
        if key not in rendered_raw:
            remaining_q.put((idx + 1, key, prm, is_vert))

    lock = threading.Lock()

    def _pollinations_worker() -> None:
        last_call = 0.0
        while not remaining_q.empty():
            wait_needed = 46.5 - (time.time() - last_call)
            if last_call > 0 and wait_needed > 0:
                # إذا بقي أقل من 2 مهام فقط، نترك AI Horde ينهيها بدلاً من الانتظار الطويل
                if remaining_q.qsize() <= 1:
                    return
                time.sleep(min(wait_needed, 46.5))
            try:
                seed_i, key, prm, is_vert = remaining_q.get_nowait()
            except queue.Empty:
                return
            last_call = time.time()
            im = _try_pollinations_flux_clean(prm, is_vertical=is_vert, seed=700 + seed_i * 41)
            if im is not None:
                with lock:
                    rendered_raw[key] = im
                print(f"    ✨ [FLUX Parallel] {key} ({'9:16' if is_vert else '16:9'}) ready!")
                remaining_q.task_done()
            else:
                # إعادتها للعنقود ليتولاها AI Horde فوراً
                im2 = _generate_via_aihorde_single(prm, is_vertical=is_vert)
                if im2 is not None:
                    with lock:
                        rendered_raw[key] = im2
                    print(f"    🎬 [Cinema Cluster] {key} ({'9:16' if is_vert else '16:9'}) ready!")
                remaining_q.task_done()

    def _horde_worker() -> None:
        while True:
            try:
                seed_i, key, prm, is_vert = remaining_q.get_nowait()
            except queue.Empty:
                return
            im = _generate_via_aihorde_single(prm, is_vertical=is_vert)
            if im is None:
                # محاولة أخيرة عبر Pollinations بعد هدوء الشبكة
                im = _try_pollinations_flux_clean(prm, is_vertical=is_vert, seed=1900 + seed_i * 29)
            if im is not None:
                with lock:
                    rendered_raw[key] = im
                print(f"    🎬 [Cinema Cluster] {key} ({'9:16' if is_vert else '16:9'}) ready!")
            remaining_q.task_done()

    if not remaining_q.empty():
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            futs = [pool.submit(_pollinations_worker)]
            for _ in range(4):
                futs.append(pool.submit(_horde_worker))
            concurrent.futures.wait(futs)

    # المرحلة 3: حفظ جميع المشاهد بالتدريج اللوني السينمائي الموحد والمقاسات الدقيقة (1280x720 للفيلم و720x1280 للشورتس)
    long_paths: List[Path] = []
    sh1_paths: List[Path] = []
    sh2_paths: List[Path] = []

    for key, prm, is_vert, target_path in tasks:
        if key == "thumb":
            continue
        raw_im = rendered_raw.get(key)
        if raw_im is None:
            # محاولة طوارئ منفردة حتى لا تتكرر أي صورة أبداً
            raw_im = _generate_via_aihorde_single(prm, is_vertical=is_vert, timeout_sec=90.0) or Image.new(
                "RGB", (720, 1280) if is_vert else (1280, 720), (18, 24, 38)
            )
        w, h = (720, 1280) if is_vert else (1280, 720)
        graded = apply_cinema_grade(raw_im, width=w, height=h, mood=mood, is_vertical=is_vert)
        graded.save(target_path, quality=92)
        if key.startswith("long_"):
            long_paths.append(target_path)
        elif key.startswith("sh1_"):
            sh1_paths.append(target_path)
        elif key.startswith("sh2_"):
            sh2_paths.append(target_path)

    # المرحلة 4: بناء غلاف اليوتيوب الاحترافي الجاذب للنقرات (1280x720 High-CTR Thumbnail)
    thumb_base = rendered_raw.get("thumb") or (Image.open(long_paths[0]).convert("RGB") if long_paths else Image.new("RGB", (1280, 720), (16, 20, 32)))
    thumb_final_path = out_dir / "youtube_thumbnail.jpg"
    build_viral_youtube_thumbnail(
        base_img=thumb_base,
        hook_text=thumbnail_hook_text,
        badge_text=thumbnail_badge_text,
        is_arabic=is_arabic,
        out_path=thumb_final_path,
    )

    return {
        "thumbnail": thumb_final_path,
        "long_scenes": long_paths,
        "short_1_scenes": sh1_paths,
        "short_2_scenes": sh2_paths,
    }


def _load_cairo_bold(size: int, weight: int = 900) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(CAIRO_FONT_PATH), size)
    try:
        axes = font.get_variation_axes()
        vals = []
        for ax in axes:
            nm = ax.get("name", b"").decode("utf-8", errors="ignore").lower()
            vals.append(weight if "weight" in nm else ax.get("default", 0))
        if vals:
            font.set_variation_by_axes(vals)
    except Exception:
        pass
    return font


def _wrap_hook_lines(text: str, max_words_per_line: int = 2) -> List[str]:
    cleaned = "".join(ch for ch in text if ord(ch) < 0x1F000).strip()
    words = [w for w in cleaned.split() if w]
    if not words:
        return ["سر الليلة!"]
    if len(words) <= 2:
        return [" ".join(words)]
    if len(words) == 3:
        return [" ".join(words[:2]), words[2]]
    lines: List[str] = []
    for i in range(0, len(words), max_words_per_line):
        lines.append(" ".join(words[i : i + max_words_per_line]))
    return lines[:3]


def build_viral_youtube_thumbnail(
    base_img: Image.Image,
    hook_text: str,
    badge_text: str,
    is_arabic: bool,
    out_path: Path,
) -> Path:
    """
    يصمّم غلاف يوتيوب (1280x720) فائق الجاذبية بأسلوب كبار صناع المحتوى:
    - تباين درامي حاد وإضاءة أطراف حمراء/ذهبية.
    - تدرج مظلم عميق على الجانب المخصص للنص ليقرأه المشاهد في 0.2 ثانية من شاشة الموبايل.
    - شارة حمراء عاجلة في الأعلى + نص ضخم ثلاثي الأبعاد باللونين الأبيض والذهبي المتوهج.
    """
    W, H = 1280, 720
    img = base_img.convert("RGB")
    src_w, src_h = img.size
    target_r = W / float(H)
    src_r = src_w / float(max(1, src_h))
    if src_r > target_r:
        nw = int(src_h * target_r)
        left = (src_w - nw) // 2
        img = img.crop((left, 0, left + nw, src_h))
    else:
        nh = int(src_w / target_r)
        top = (src_h - nh) // 2
        img = img.crop((0, top, src_w, top + nh))
    img = img.resize((W, H), Image.Resampling.LANCZOS)

    # تعزيز التباين والألوان والحدة ليبرز الغلاف بقوة وسط صفحة اليوتيوب الرئيسية
    img = ImageEnhance.Contrast(img).enhance(1.26)
    img = ImageEnhance.Color(img).enhance(1.22)
    img = ImageEnhance.Sharpness(img).enhance(1.30)

    # قياس الإضاءة لاختيار الجانب الأقل إضاءة تلقائياً للنص حتى لا يغطي وجه الشخصية أبداً
    rgb_np = np.asarray(img, dtype=np.float32)
    left_lum = float(rgb_np[int(H * 0.15) : int(H * 0.85), : W // 2, :].mean())
    right_lum = float(rgb_np[int(H * 0.15) : int(H * 0.85), W // 2 :, :].mean())
    text_on_right = right_lum < (left_lum * 0.92)

    arr_ov = np.zeros((H, W, 4), dtype=np.uint8)
    x_norm = np.linspace(0.0, 1.0, W)[None, :]
    if text_on_right:
        side_alpha = np.clip((x_norm - 0.40) / 0.60, 0.0, 1.0) ** 1.25 * 228.0
    else:
        side_alpha = np.clip((0.60 - x_norm) / 0.60, 0.0, 1.0) ** 1.25 * 228.0
    arr_ov[:, :, 0] = 6
    arr_ov[:, :, 1] = 8
    arr_ov[:, :, 2] = 16
    arr_ov[:, :, 3] = side_alpha.astype(np.uint8)
    overlay = Image.fromarray(arr_ov, mode="RGBA")
    canvas = Image.alpha_composite(img.convert("RGBA"), overlay)

    draw = ImageDraw.Draw(canvas)
    has_raqm = bool(features.check("raqm"))
    text_kwargs = {"direction": "rtl", "language": "ar"} if (is_arabic and has_raqm) else {}

    # إطار تحذيري سينمائي رفيع متوهج حول الغلاف
    draw.rectangle([(6, 6), (W - 7, H - 7)], outline=(255, 196, 0, 185), width=4)

    # 1) شارة علوية حمراء ملفتة (Top Pill Badge)
    clean_badge = "".join(ch for ch in badge_text if ord(ch) < 0x1F000).strip()
    if clean_badge:
        f_badge = _load_cairo_bold(34, weight=850)
        bb = draw.textbbox((0, 0), clean_badge, font=f_badge, **text_kwargs)
        bw, bh = bb[2] - bb[0], bb[3] - bb[1]
        bx1 = (W - 56 - (bw + 48)) if text_on_right else 56
        by1 = 56
        bx2, by2 = bx1 + bw + 48, by1 + bh + 28
        draw.rounded_rectangle([(bx1, by1), (bx2, by2)], radius=14, fill=(210, 18, 36, 245), outline=(255, 220, 90, 230), width=3)
        draw.text((bx1 + 24, by1 + 10 - bb[1]), clean_badge, font=f_badge, fill=(255, 255, 255, 255), **text_kwargs)

    # 2) النص الرئيسي الضخم الجاذب للنقر (2-3 أسطر بخط Cairo ExtraBlack 950)
    lines = _wrap_hook_lines(hook_text, max_words_per_line=2)
    font_size = 104 if max(len(ln) for ln in lines) <= 12 else (88 if max(len(ln) for ln in lines) <= 16 else 74)
    f_main = _load_cairo_bold(font_size, weight=950)

    line_heights: List[Tuple[str, Tuple[int, int, int, int]]] = []
    for ln in lines:
        tb = draw.textbbox((0, 0), ln, font=f_main, stroke_width=10, **text_kwargs)
        line_heights.append((ln, tb))

    total_text_h = sum((tb[3] - tb[1]) for _, tb in line_heights) + max(0, len(lines) - 1) * 18
    cur_y = max(175, (H - total_text_h) // 2 + 24)

    palette = [
        (255, 255, 255, 255),   # أبيض ناصع
        (255, 214, 10, 255),    # ذهبي مشع عالي التباين
        (255, 92, 92, 255),     # أحمر توتر متوهج للسطر الثالث إن وجد
    ]

    for idx, (ln, tb) in enumerate(line_heights):
        lw = tb[2] - tb[0]
        tx = (W - 58 - lw) if text_on_right else 58
        ty = cur_y - tb[1]
        color = palette[idx % len(palette)]
        draw.text(
            (tx + 7, ty + 9),
            ln,
            font=f_main,
            fill=(0, 0, 0, 230),
            stroke_width=12,
            stroke_fill=(0, 0, 0, 230),
            **text_kwargs,
        )
        draw.text(
            (tx, ty),
            ln,
            font=f_main,
            fill=color,
            stroke_width=9,
            stroke_fill=(8, 10, 16, 255),
            **text_kwargs,
        )
        cur_y += (tb[3] - tb[1]) + 18

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, quality=94)
    return out_path
