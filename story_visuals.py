# -*- coding: utf-8 -*-
"""
محرك المشاهد القصصية السينمائية V4.0 (Zero-Cost Story Scene Visual Engine)
يجلب ويولّد مشاهد بصرية عالية الدقة (1280x720) تطابق أحداث كل فصل في القصة بدون أي علامات مائية:
1) إذا توفر HF_TOKEN مجاني: يولّد المشهد بالذكاء الاصطناعي عبر FLUX.1-schnell / SDXL-Lightning.
2) إذا توفر PEXELS_API_KEY مجاني: يجلب لقطات فوتوغرافية سينمائية مطابقة لوصف المشهد.
3) بدون أي مفاتيح نهائياً ($0.00 Zero-Key): يبحث في مكتبة Wikimedia Commons العالمية المفتوحة (CC0/CC-BY)
   عن صور فوتوغرافية حقيقية عالية الدقة تطابق الكلمات المفتاحية لكل مشهد، ويطبّق عليها تدريج لوني سينمائي
   موحد (Cinematic Film Color Grading + Soft Vignette) لتظهر الحلقة كلها بروح فيلم وثائقي/درامي واحد!
"""

import io
import os
import re
from pathlib import Path
from typing import List, Optional

import numpy as np
import requests
from PIL import Image, ImageEnhance, ImageFilter

STOPWORDS = {
    "cinematic", "photorealistic", "still", "wide", "widescreen", "movie", "scene", "shot",
    "dramatic", "lighting", "warm", "soft", "glow", "text", "watermark", "16:9", "close",
    "closeup", "portrait", "background", "blurred", "subtle", "intense", "atmosphere",
    "showing", "standing", "sitting", "looking", "holding", "inside", "outside", "with",
    "from", "into", "over", "under", "through", "while", "where", "there", "their", "this",
}


def apply_cinema_grade(img: Image.Image, width: int = 1280, height: int = 720, mood: str = "warm") -> Image.Image:
    """قص ذكي للأبعاد المطلوبة مع تدريج ألوان سينمائي درامي وتعتيم أطراف خفيف (Vignette)."""
    img = img.convert("RGB")
    src_w, src_h = img.size
    target_ratio = width / height
    src_ratio = src_w / max(1, src_h)

    if src_ratio > target_ratio:
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    else:
        new_h = int(src_w / target_ratio)
        top = (src_h - new_h) // 2
        img = img.crop((0, top, src_w, top + new_h))

    img = img.resize((width, height), Image.Resampling.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(1.14)
    img = ImageEnhance.Color(img).enhance(1.08)

    arr = np.asarray(img, dtype=np.float32)
    if mood == "mystery":
        # تدرج Teal & Amber سينمائي لأفلام الغموض والتحقيقات
        arr[:, :, 0] *= 0.96
        arr[:, :, 1] *= 0.99
        arr[:, :, 2] = np.clip(arr[:, :, 2] * 1.07 + 4.0, 0, 255)
    else:
        # تدرج درامي دافئ للقصص الاجتماعية والكارما
        arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.05 + 3.0, 0, 255)
        arr[:, :, 2] *= 0.95

    # Vignette ناعم حول الأطراف لإبراز قلب المشهد والترجمة
    yy, xx = np.ogrid[:height, :width]
    cy, cx = height * 0.48, width * 0.50
    dist = np.sqrt(((xx - cx) / (width * 0.62)) ** 2 + ((yy - cy) / (height * 0.62)) ** 2)
    vig = np.clip(1.0 - 0.34 * np.clip(dist - 0.45, 0, 1.5), 0.52, 1.0)[:, :, None]
    # تعتيم خفيف أسفل الشاشة لقراءة الترجمة بوضوح تام
    bottom_grad = np.ones((height, 1, 1), dtype=np.float32)
    fade_start = int(height * 0.72)
    bottom_grad[fade_start:, 0, 0] = np.linspace(1.0, 0.55, height - fade_start)

    out_arr = np.clip(arr * vig * bottom_grad, 0, 255).astype(np.uint8)
    return Image.fromarray(out_arr)


def _extract_search_keywords(prompt: str) -> str:
    words = re.findall(r"[A-Za-z]{4,}", prompt.lower())
    picked = [w for w in words if w not in STOPWORDS]
    return " ".join(picked[:4]) if picked else "dramatic architecture interior"


def _try_cloudflare_flux(prompt: str) -> Optional[Image.Image]:
    """توليد مشاهد ذكاء اصطناعي مجاناً للأبد عبر Cloudflare Workers AI Free Tier (@cf/black-forest-labs/flux-1-schnell)."""
    acc_id = os.environ.get("CF_ACCOUNT_ID", "").strip()
    cf_tok = os.environ.get("CF_API_TOKEN", "").strip()
    if not (acc_id and cf_tok):
        return None
    try:
        import base64
        r = requests.post(
            f"https://api.cloudflare.com/client/v4/accounts/{acc_id}/ai/run/@cf/black-forest-labs/flux-1-schnell",
            headers={"Authorization": f"Bearer {cf_tok}"},
            json={"prompt": prompt, "num_steps": 4},
            timeout=35,
        )
        if r.status_code == 200:
            b64 = (r.json().get("result") or {}).get("image")
            if b64:
                return Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
    except Exception:
        pass
    return None


def _try_meta_ai_scene(prompt: str) -> Optional[Image.Image]:
    """دعم اختياري لتوليد المشاهد عبر Meta AI إذا وفّر المستخدم الكوكيز في Secrets."""
    datr = os.environ.get("META_DATR_COOKIE", "").strip()
    ecto = os.environ.get("META_ECTO_COOKIE", "").strip()
    if not (datr and ecto):
        return None
    try:
        from metaai_api import MetaAI
        ai = MetaAI(cookies={"datr": datr, "ecto_1_sess": ecto})
        res = ai.generate_image_new(prompt)
        urls = res.get("image_urls") or []
        ai.close()
        if urls:
            raw = requests.get(urls[0], timeout=25).content
            return Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        pass
    return None


def _try_hf_flux(prompt: str, hf_token: str) -> Optional[Image.Image]:
    if not hf_token:
        return None
    try:
        from gradio_client import Client

        client = Client("black-forest-labs/FLUX.1-schnell", token=hf_token)
        res, _ = client.predict(
            prompt=prompt,
            seed=0,
            randomize_seed=True,
            width=1280,
            height=720,
            num_inference_steps=4,
            api_name="/infer",
        )
        p = res["path"] if isinstance(res, dict) else str(res)
        return Image.open(p).convert("RGB")
    except Exception:
        return None


def _try_pexels_photo(query: str, pexels_key: str) -> Optional[Image.Image]:
    if not pexels_key:
        return None
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": pexels_key},
            params={"query": query, "orientation": "landscape", "per_page": 5},
            timeout=15,
        )
        if r.status_code == 200:
            photos = r.json().get("photos", [])
            if photos:
                url = photos[0]["src"].get("large2x") or photos[0]["src"].get("large")
                raw = requests.get(url, timeout=20).content
                return Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        pass
    return None


def _is_modern_color_photo(img: Image.Image) -> bool:
    """يرفض الصور الأبيض والأسود أو الرسوم التاريخية القديمة ويضمن صوراً ملونة حديثة فقط."""
    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    rg = np.abs(arr[:, :, 0] - arr[:, :, 1]).mean()
    yb = np.abs(0.5 * (arr[:, :, 0] + arr[:, :, 1]) - arr[:, :, 2]).mean()
    colorfulness = float(np.sqrt(rg ** 2 + yb ** 2))
    return colorfulness >= 11.5


def _try_wikimedia_photo(query: str, used_urls: set) -> Optional[Image.Image]:
    headers = {"User-Agent": "MediaEmpireStoryBot/4.0 (https://github.com/yousefmo2500m-prog)"}
    bad_title_words = ("diagram", "map", "icon", "logo", "chart", "stamp", "engraving", "drawing", "sketch", "statue", "monument", "coat_of_arms")
    words = [w for w in re.findall(r"[A-Za-z]{3,}", query.lower()) if w not in STOPWORDS]
    variants = []
    if len(words) >= 2:
        variants.append(f"intitle:{words[0]} intitle:{words[1]}")
    if len(words) >= 3:
        variants.append(f"intitle:{words[0]} intitle:{words[2]}")
    if words:
        variants.append(f"intitle:{words[0]} {words[1] if len(words) > 1 else ''}".strip())
        variants.append(f"intitle:{words[0]}")

    for q in variants:
        try:
            r = requests.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "generator": "search",
                    "gsrsearch": f"filetype:bitmap {q}",
                    "gsrnamespace": 6,
                    "gsrlimit": 20,
                    "prop": "imageinfo",
                    "iiprop": "url|dimensions|mime",
                    "iiurlwidth": 1280,
                    "format": "json",
                },
                headers=headers,
                timeout=15,
            )
            pages = r.json().get("query", {}).get("pages", {})
            for p in pages.values():
                title_low = str(p.get("title", "")).lower()
                if any(bw in title_low for bw in bad_title_words):
                    continue
                info = (p.get("imageinfo") or [{}])[0]
                mime = str(info.get("mime", ""))
                w, h = int(info.get("width", 0)), int(info.get("height", 0))
                turl = info.get("thumburl") or info.get("url")
                if not turl or turl in used_urls:
                    continue
                if "jpeg" not in mime:
                    continue
                if w < 900 or h < 500 or (w / max(1, h)) < 1.2:
                    continue
                resp = requests.get(turl, headers=headers, timeout=20)
                if resp.status_code == 200 and len(resp.content) > 35_000:
                    cand = Image.open(io.BytesIO(resp.content)).convert("RGB")
                    if _is_modern_color_photo(cand):
                        used_urls.add(turl)
                        print(f"    [Matched Scene] '{query}' -> {p.get('title')}")
                        return cand
        except Exception:
            continue
    return None


def prepare_episode_scenes(
    scene_prompts: List[str],
    out_dir: Path,
    mood: str = "warm",
    search_queries_override: Optional[List[str]] = None,
) -> List[Path]:
    """يجهز 8 مشاهد قصصية عالية الدقة (1280x720) في المجلد المحدد، مع احترام أي مشاهد موجودة مسبقاً."""
    out_dir.mkdir(parents=True, exist_ok=True)
    hf_tok = os.environ.get("HF_TOKEN", "").strip()
    px_key = os.environ.get("PEXELS_API_KEY", "").strip()
    used_urls: set = set()
    final_paths: List[Path] = []

    for idx, prompt in enumerate(scene_prompts, 1):
        target = out_dir / f"s{idx}.jpg"
        if target.exists() and target.stat().st_size > 15_000:
            # نطبّق التدريج السينمائي الموحد وضبط المقاس 1280x720
            graded = apply_cinema_grade(Image.open(target), 1280, 720, mood=mood)
            graded.save(target, quality=90)
            final_paths.append(target)
            continue

        q = (
            search_queries_override[idx - 1]
            if search_queries_override and idx - 1 < len(search_queries_override)
            else _extract_search_keywords(prompt)
        )
        img = (
            _try_cloudflare_flux(prompt)
            or _try_hf_flux(prompt, hf_tok)
            or _try_meta_ai_scene(prompt)
            or _try_pexels_photo(q, px_key)
            or _try_wikimedia_photo(q, used_urls)
        )
        if img is None:
            # خلفية سينمائية احتياطية مضمونة في حال انقطاع الإنترنت
            img = Image.new("RGB", (1280, 720), (24, 32, 48)).filter(ImageFilter.GaussianBlur(2))

        graded = apply_cinema_grade(img, 1280, 720, mood=mood)
        graded.save(target, quality=90)
        final_paths.append(target)

    return final_paths
