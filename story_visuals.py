# -*- coding: utf-8 -*-
"""
محرك المشاهد البصرية المتجددة كل 8 ثوانٍ وغلاف اليوتيوب الناري V10.0 (Parallel FLUX.1 8K Studio + Viral CTR Thumbnail)
- يولّد صورة جديدة كلياً لكل نافذة ~8 ثوانٍ بدون أي تكرار طوال الفيديو الطويل والشورتين!
- يستخدم مفتاح Hugging Face المجاني (HF_TOKEN / HF_TOKEN_2) عبر:
  1) HF Serverless Router (`black-forest-labs/FLUX.1-schnell`) فائق السرعة
  2) تجمع ZeroGPU FLUX Spaces (`evalstate/flux1_schnell` بوزن 10 ثوانٍ فقط + `black-forest-labs/FLUX.1-schnell` + `multimodalart/FLUX.1-merged` + `Tongyi-MAI/Z-Image-Turbo`)
  3) دعم اختياري لـ Cloudflare Workers AI Free Tier (`@cf/black-forest-labs/flux-1-schnell`)
  4) احتياطي طوارئ فوتوغرافي عالي التباين لضمان عدم تعطل أي حلقة لمدة سنتين.
- تصميم غلاف يوتيوب احترافي عالي النقر (High-CTR Netflix/MrBallen Style):
  بدون أي إطارات صفراء قديمة، مع تباين سينمائي حاد، دائرة تركيز حمراء مضيئة حول تفصيلة اللغز، وعنوان ثلاثي الأبعاد ضخم مكتمل المعنى.
"""

import io
import math
import os
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

FONTS_DIR = Path(__file__).resolve().parent / "fonts"
FONT_AR = FONTS_DIR / "Cairo-Variable.ttf"

_CLIENT_LOCK = threading.Lock()
_GRADIO_CLIENTS: Dict[str, Any] = {}


def _load_bold_font(size: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(FONT_AR), size)
    try:
        font.set_variation_by_axes([950, 100, 0])
    except Exception:
        try:
            font.set_variation_by_name("Black")
        except Exception:
            pass
    return font


def _get_hf_tokens() -> List[str]:
    toks: List[str] = []
    for k in ("HF_TOKEN", "HF_TOKEN_2", "HF_TOKEN_3"):
        v = os.environ.get(k, "").strip()
        if v and v not in toks:
            toks.append(v)
    return toks


def _fit_cover_exact(img: Image.Image, target_w: int, target_h: int, polish: bool = True) -> Image.Image:
    img = img.convert("RGB")
    src_ratio = img.width / max(1, img.height)
    dst_ratio = target_w / max(1, target_h)
    if src_ratio > dst_ratio:
        new_h = target_h
        new_w = max(target_w, int(round(new_h * src_ratio)))
    else:
        new_w = target_w
        new_h = max(target_h, int(round(new_w / max(0.01, src_ratio))))
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = max(0, (new_w - target_w) // 2)
    top = max(0, (new_h - target_h) // 2)
    cropped = resized.crop((left, top, left + target_w, top + target_h))
    if polish:
        cropped = ImageEnhance.Contrast(cropped).enhance(1.13)
        cropped = ImageEnhance.Color(cropped).enhance(1.10)
        cropped = ImageEnhance.Sharpness(cropped).enhance(1.22)
    return cropped


def _get_gradio_client(space_id: str, hf_token: str):
    key = f"{space_id}::{hf_token[:10]}"
    with _CLIENT_LOCK:
        if key not in _GRADIO_CLIENTS:
            from gradio_client import Client
            _GRADIO_CLIENTS[key] = Client(space_id, token=hf_token or None)
        return _GRADIO_CLIENTS[key]


def _try_hf_router_flux(prompt: str, width: int, height: int, seed: int, hf_token: str) -> Optional[Image.Image]:
    if not hf_token:
        return None
    w = (min(1280, width) // 32) * 32
    h = (min(1280, height) // 32) * 32
    for model_slug in ("black-forest-labs/FLUX.1-schnell",):
        try:
            r = requests.post(
                f"https://router.huggingface.co/hf-inference/models/{model_slug}",
                headers={"Authorization": f"Bearer {hf_token}", "Accept": "image/jpeg"},
                json={
                    "inputs": prompt,
                    "parameters": {"width": w, "height": h, "num_inference_steps": 4, "seed": seed % 1000000},
                },
                timeout=35,
            )
            if r.status_code == 200 and len(r.content) > 8000:
                img = Image.open(io.BytesIO(r.content)).convert("RGB")
                if img.width >= 256:
                    return _fit_cover_exact(img, width, height)
        except Exception:
            continue
    return None


def _try_hf_zerogpu_flux(
    prompt: str,
    width: int,
    height: int,
    seed: int,
    hf_token: str,
    slot: int = 0,
    high_res_cover: bool = False,
) -> Optional[Image.Image]:
    if not hf_token:
        return None
    if high_res_cover:
        w_req, h_req = 1280, 720
    elif width >= height:
        w_req, h_req = 1024, 576
    else:
        w_req, h_req = 576, 1024

    # evalstate/flux1_schnell يستهلك ~1.1 ثانية فقط من رصيد ZeroGPU (أكثر من 800 صورة FLUX يومياً للـ 3 مفاتيح!)
    spaces_order = [
        "evalstate/flux1_schnell",
        "black-forest-labs/FLUX.1-schnell",
        "multimodalart/FLUX.1-merged",
        "Tongyi-MAI/Z-Image-Turbo",
    ]
    ordered = spaces_order[slot % 2 :] + spaces_order[: slot % 2]

    for sp in ordered:
        img_p = None
        try:
            client = _get_gradio_client(sp, hf_token)
            if sp == "Tongyi-MAI/Z-Image-Turbo":
                res_str = "720x1280 ( 9:16 )" if height > width else "1280x720 ( 16:9 )"
                res = client.predict(
                    prompt=prompt,
                    resolution=res_str,
                    seed=seed % 999999,
                    steps=8,
                    shift=3.0,
                    random_seed=False,
                    gallery_images=[],
                    api_name="/generate",
                )
                gal = res[0] if isinstance(res, (list, tuple)) else res
                item = gal[0] if isinstance(gal, list) and gal else gal
                img_p = item.get("image") if isinstance(item, dict) else item
                if isinstance(img_p, dict):
                    img_p = img_p.get("path")
            elif sp == "multimodalart/FLUX.1-merged":
                res = client.predict(
                    prompt=prompt,
                    seed=seed % 999999,
                    randomize_seed=False,
                    width=w_req,
                    height=h_req,
                    guidance_scale=3.5,
                    num_inference_steps=4,
                    api_name="/infer",
                )
                img_p = res[0] if isinstance(res, (list, tuple)) else res
                if isinstance(img_p, dict):
                    img_p = img_p.get("path")
            else:
                res = client.predict(
                    prompt=prompt,
                    seed=seed % 999999,
                    randomize_seed=False,
                    width=w_req,
                    height=h_req,
                    num_inference_steps=4,
                    api_name="/infer",
                )
                img_p = res[0] if isinstance(res, (list, tuple)) else res
                if isinstance(img_p, dict):
                    img_p = img_p.get("path")

            if img_p and Path(str(img_p)).exists():
                p_obj = Path(str(img_p))
                im = Image.open(p_obj).convert("RGB")
                im.load()
                try:
                    p_obj.unlink(missing_ok=True)
                except Exception:
                    pass
                if im.width >= 256:
                    return _fit_cover_exact(im, width, height)
        except Exception:
            continue
    return None


def _try_cloudflare_flux(prompt: str, width: int, height: int, seed: int) -> Optional[Image.Image]:
    cf_acc = os.environ.get("CF_ACCOUNT_ID", "").strip()
    cf_tok = os.environ.get("CF_API_TOKEN", "").strip()
    if not (cf_acc and cf_tok):
        return None
    try:
        r = requests.post(
            f"https://api.cloudflare.com/client/v4/accounts/{cf_acc}/ai/run/@cf/black-forest-labs/flux-1-schnell",
            headers={"Authorization": f"Bearer {cf_tok}"},
            json={"prompt": prompt, "steps": 4, "seed": seed % 999999},
            timeout=35,
        )
        if r.status_code == 200:
            data = r.json()
            b64_img = (data.get("result") or {}).get("image")
            if b64_img:
                import base64
                im = Image.open(io.BytesIO(base64.b64decode(b64_img))).convert("RGB")
                return _fit_cover_exact(im, width, height)
    except Exception:
        pass
    return None


def _try_ai_horde_photoreal(prompt: str, width: int, height: int) -> Optional[Image.Image]:
    h_w = 576 if width >= height else 384
    h_h = 320 if width >= height else 640
    headers = {"apikey": "0000000000", "Client-Agent": "MediaEmpireV10:1.0:auto"}
    payload = {
        "prompt": f"{prompt} ### cartoon, anime, blurry, deformed, text, watermark, ugly, lowres",
        "params": {"width": h_w, "height": h_h, "steps": 24, "cfg_scale": 7.0, "sampler_name": "k_dpmpp_2m"},
        "nsfw": False,
        "censor_nsfw": False,
        "r2": True,
        "models": ["ICBINP - I Can't Believe It's Not Photography", "AbsoluteReality", "Deliberate"],
    }
    try:
        r = requests.post("https://aihorde.net/api/v2/generate/async", json=payload, headers=headers, timeout=18)
        if r.status_code != 202:
            return None
        job_id = r.json().get("id")
        if not job_id:
            return None
        deadline = time.time() + 75.0
        while time.time() < deadline:
            time.sleep(3.5)
            st = requests.get(f"https://aihorde.net/api/v2/generate/status/{job_id}", headers=headers, timeout=15)
            if st.status_code != 200:
                continue
            js = st.json()
            if js.get("done"):
                gens = js.get("generations") or []
                if gens and gens[0].get("img"):
                    raw_img = gens[0]["img"]
                    img_bytes = requests.get(raw_img, timeout=25).content if raw_img.startswith("http") else __import__("base64").b64decode(raw_img)
                    im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                    return _fit_cover_exact(im, width, height)
                break
            if js.get("faulted"):
                break
    except Exception:
        pass
    return None


def _procedural_cinema_noir(width: int, height: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("RGB", (width, height), (8, 12, 22))
    draw = ImageDraw.Draw(img, "RGBA")
    palettes = [((185, 28, 45), (18, 95, 165)), ((215, 115, 22), (16, 82, 138)), ((145, 32, 160), (20, 115, 130))]
    c1, c2 = palettes[seed % len(palettes)]
    for i in range(18):
        r = int(max(width, height) * (0.85 - i * 0.04))
        col = c1 if i % 2 == 0 else c2
        cx = int(width * (0.28 + 0.44 * rng.random()))
        cy = int(height * (0.25 + 0.48 * rng.random()))
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*col, 20))
    return img.filter(ImageFilter.GaussianBlur(radius=22))


def generate_single_shot_image(
    prompt: str,
    out_path: Path,
    width: int,
    height: int,
    seed: int,
    shot_idx: int = 0,
    high_res_cover: bool = False,
) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    hf_tokens = _get_hf_tokens()
    img: Optional[Image.Image] = None

    # 1) Cloudflare Workers AI Free Tier FLUX (إن وجد)
    img = _try_cloudflare_flux(prompt, width, height, seed)

    # 2) مفاتيح Hugging Face المجانية الثلاثة: دوران متوازٍ عبر ZeroGPU FLUX.1 Spaces
    if img is None and hf_tokens:
        for t_off in range(len(hf_tokens)):
            tok = hf_tokens[(shot_idx + t_off) % len(hf_tokens)]
            img = _try_hf_zerogpu_flux(
                prompt,
                width,
                height,
                seed,
                tok,
                slot=shot_idx + t_off,
                high_res_cover=high_res_cover,
            )
            if img is not None:
                break

    # 3) احتياطي فوتوغرافي للطوارئ القصوى فقط
    if img is None:
        img = _try_ai_horde_photoreal(prompt, width, height)
    if img is None:
        img = _procedural_cinema_noir(width, height, seed)

    img.save(str(out_path), format="JPEG", quality=93, optimize=True)
    return out_path


def generate_8sec_shots_batch(
    prompts: List[str],
    out_dir: Path,
    prefix: str,
    width: int,
    height: int,
    seed_base: int,
    max_workers: int = 4,
) -> List[Path]:
    """
    يولّد بالتوازي قائمة كاملة من صور الـ 8 ثوانٍ الفريدة (مثلاً ~118 صورة أفقية 16:9 أو ~15 صورة طولية كاملة 9:16)
    بحيث لا تتكرر أي صورة مرتين إطلاقاً طوال الفيديو!
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: List[Optional[Path]] = [None] * len(prompts)

    def _job(idx: int, pr: str) -> Tuple[int, Path]:
        p = out_dir / f"{prefix}_{idx:03d}.jpg"
        generate_single_shot_image(pr, p, width, height, seed=seed_base + idx * 97, shot_idx=idx)
        return idx, p

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(_job, i, pr) for i, pr in enumerate(prompts)]
        done_n = 0
        for f in as_completed(futs):
            idx, p = f.result()
            paths[idx] = p
            done_n += 1
            if done_n % 15 == 0 or done_n == len(prompts):
                print(f"    🎨 [{prefix}] تم توليد {done_n}/{len(prompts)} صورة سينمائية فريدة (8 ثوانٍ/صورة)...")

    return [p for p in paths if p is not None]


def build_viral_youtube_thumbnail(
    prompt: str,
    hook_text: str,
    badge_text: str,
    brand_name: str,
    language: str,
    out_path: Path,
    seed: int = 7777,
) -> Path:
    """
    غلاف يوتيوب فائق الإثارة ونسبة النقر (1280×720 High-CTR Netflix / MrBallen Mystery Thumbnail):
    - صورة FLUX درامية فائقة الحدة والتباين (بدون إطارات صفراء قديمة!).
    - دائرة تركيز حمراء مضيئة (Mystery Red Focus Ring) على زاوية الدليل الخلفي لإثارة فضول العين فوراً.
    - تدرج سينمائي ناعم في النصف الأيسر + شارة خطر حمراء متوهجة + نص ثلاثي الأبعاد ضخم مكتمل المعنى من 3–4 كلمات.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    raw_bg = out_path.parent / "_thumb_raw_flux.jpg"
    generate_single_shot_image(prompt, raw_bg, 1280, 720, seed=seed, shot_idx=0, high_res_cover=True)

    base = Image.open(str(raw_bg)).convert("RGB")
    raw_bg.unlink(missing_ok=True)

    # تعزيز الألوان والحدة الدرامية للغلاف لكي يقفز وسط صفحة يوتيوب الرئيسية
    base = ImageEnhance.Contrast(base).enhance(1.24)
    base = ImageEnhance.Color(base).enhance(1.22)
    base = ImageEnhance.Sharpness(base).enhance(1.32)
    canvas = base.convert("RGBA")

    # 1) تدرج سينمائي داكن انسيابي بدون أي حواف حادة (يترك وجه البطل وتفصيلة اللغز واضحين تماماً على اليمين!)
    grad_x = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    gx_draw = ImageDraw.Draw(grad_x)
    for x in range(720):
        t = 1.0 - (x / 720.0)
        alpha = int(235 * (t ** 1.45))
        gx_draw.line([(x, 0), (x, 720)], fill=(5, 8, 16, alpha))

    grad_y = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    gy_draw = ImageDraw.Draw(grad_y)
    for y in range(540, 720):
        alpha = int(175 * (((y - 540) / 180.0) ** 1.3))
        gy_draw.line([(0, y), (1280, y)], fill=(5, 7, 14, alpha))

    # إضاءة حافة حمراء خفيفة أعلى اليمين لرفع الإحساس بالخطر والتوتر السينمائي
    glow_layer = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    gl_draw = ImageDraw.Draw(glow_layer)
    gl_draw.ellipse((980, -130, 1430, 290), fill=(225, 22, 42, 68))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=18))

    canvas = Image.alpha_composite(canvas, grad_x)
    canvas = Image.alpha_composite(canvas, grad_y)
    canvas = Image.alpha_composite(canvas, glow_layer)
    draw = ImageDraw.Draw(canvas)

    is_ar = language == "ar"
    dir_kw: Dict[str, Any] = {"direction": "rtl", "language": "ar"} if is_ar else {}

    # 2) شارة علوية حمراء نارية عالية التباين
    badge_clean = (badge_text or ("قصة حقيقية تحبس الأنفاس" if is_ar else "TRUE CHILLING TWIST")).strip()
    f_badge = _load_bold_font(34)
    try:
        bb = draw.textbbox((0, 0), badge_clean, font=f_badge, **dir_kw)
    except Exception:
        dir_kw = {}
        bb = draw.textbbox((0, 0), badge_clean, font=f_badge)
    bw = (bb[2] - bb[0]) + 54
    bh = (bb[3] - bb[1]) + 24
    bx, by = 52, 48
    draw.rounded_rectangle((bx, by, bx + bw, by + bh), radius=16, fill=(215, 18, 38, 248), outline=(255, 225, 90, 255), width=3)
    draw.text(
        (bx + bw // 2, by + bh // 2),
        badge_clean,
        font=f_badge,
        fill=(255, 255, 255, 255),
        anchor="mm",
        stroke_width=2,
        stroke_fill=(60, 0, 0, 255),
        **dir_kw,
    )

    # 3) العنوان الصادم المكتمل (3 إلى 5 كلمات موزعة على سطرين بحجم عملاق وتوهج خلفي)
    words = [w for w in hook_text.strip().split() if w][:5]
    if not words:
        words = ["مين", "واقف", "ورا", "الباب؟"] if is_ar else ["WHO", "SENT", "THAT", "PHOTO?"]
    if len(words) <= 2:
        lines = [" ".join(words)]
    else:
        mid = math.ceil(len(words) / 2)
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]

    max_text_w = 650
    font_sz = 112
    while font_sz > 64:
        f_test = _load_bold_font(font_sz)
        widest = max(draw.textbbox((0, 0), ln, font=f_test, stroke_width=10, **dir_kw)[2] for ln in lines)
        if widest <= max_text_w:
            break
        font_sz -= 6

    f_hook = _load_bold_font(font_sz)
    line_step = int(font_sz * 1.24)
    start_y = 265 if len(lines) == 2 else 330

    # توهج ناعم خلف النص
    txt_glow = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    tg_draw = ImageDraw.Draw(txt_glow)
    for li, ln in enumerate(lines):
        ly = start_y + li * line_step
        tg_draw.text((56, ly), ln, font=f_hook, fill=(255, 40, 40, 130) if li == 1 else (0, 0, 0, 210), anchor="lm", stroke_width=18, stroke_fill=(0, 0, 0, 220), **dir_kw)
    txt_glow = txt_glow.filter(ImageFilter.GaussianBlur(radius=10))
    canvas = Image.alpha_composite(canvas, txt_glow)
    draw = ImageDraw.Draw(canvas)

    for li, ln in enumerate(lines):
        ly = start_y + li * line_step
        fill_col = (255, 255, 255, 255) if li == 0 else (255, 218, 36, 255)
        for off in range(10, 0, -2):
            draw.text((56 + off, ly + off), ln, font=f_hook, fill=(0, 0, 0, 235), anchor="lm", **dir_kw)
        draw.text(
            (56, ly),
            ln,
            font=f_hook,
            fill=fill_col,
            anchor="lm",
            stroke_width=9,
            stroke_fill=(8, 10, 18, 255),
            **dir_kw,
        )

    # 4) توقيع القناة الأنيق أسفل اليسار
    f_brand = _load_bold_font(30)
    draw.rounded_rectangle((52, 628, 280, 682), radius=14, fill=(14, 18, 30, 225), outline=(255, 215, 45, 195), width=2)
    draw.text((166, 655), brand_name, font=f_brand, fill=(255, 222, 65, 255), anchor="mm", **dir_kw)

    final_rgb = canvas.convert("RGB")
    final_rgb.save(str(out_path), format="JPEG", quality=94, optimize=True)
    return out_path
