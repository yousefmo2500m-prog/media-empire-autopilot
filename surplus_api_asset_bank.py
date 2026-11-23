# -*- coding: utf-8 -*-
"""
محرك بنك الأصول الفائضة الذكي (Surplus API Asset Bank) V1.0
- يستغل الحصص المجانية التي تتجدد يومياً وأسبوعياً في الـ APIs (مثل Pixabay Video, HuggingFace, Kling, Cloudflare, Pollinations).
- في حالة وجود فائض أو بين دورات الإنتاج، يقوم بتوليد وحفظ لقطات فيديو سينمائية متحركة وخلفيات عالية الدقة في بنك الأصول `state/api_surplus_clips/`.
- عند إنتاج الحلقة التالية، يسحب منها فوراً كأصول جاهزة بأعلى جودة وبأسرع وقت وبدون استهلاك حصص وقت الذروة!
"""

import os
import json
import re
import time
import requests
from pathlib import Path
from typing import Any, Dict, List, Optional

BANK_DIR = Path(__file__).resolve().parent / "state" / "api_surplus_clips"

# بنك المشاهد السينمائية الأكثر طلباً للغموض والإثارة والتحقيقات
CURATED_SURPLUS_THEMES = [
    {"tag": "glowing_vault", "query": "vault opening gold light", "prompt": "ancient mysterious metallic vault cracked open glowing with blinding volumetric amber light dark atmosphere 8k film still"},
    {"tag": "dark_corridor", "query": "dark corridor flickering light", "prompt": "dark mysterious apartment hallway flickering fluorescent lights shadows cinematic 35mm"},
    {"tag": "surveillance_cctv", "query": "cctv surveillance monitor", "prompt": "security surveillance camera static scan monitor dark control room nighttime"},
    {"tag": "ancient_manuscript", "query": "ancient manuscript magnifying glass", "prompt": "hands examining ancient glowing cipher papyrus with vintage magnifying glass candlelight"},
    {"tag": "crime_scene_lights", "query": "police siren night rain", "prompt": "flashing police siren blue and red lights reflection wet asphalt midnight crime scene"},
    {"tag": "antique_safe", "query": "safe combination dial", "prompt": "macro shot hands turning antique brass safe combination dial dark shadows cinematic"},
    {"tag": "foggy_mansion", "query": "abandoned mansion night fog", "prompt": "isolated grand mansion in dense midnight fog with one single glowing golden window cinematic"},
    {"tag": "confidential_file", "query": "classified document desk", "prompt": "red confidential classified dossier folder opening on vintage wooden desk dramatic lamp light"},
    {"tag": "cyber_investigation", "query": "computer screen code reflection", "prompt": "detective eyes reflecting green glowing terminal code in dark office nighttime"},
    {"tag": "submerged_artifact", "query": "underwater temple ruins", "prompt": "ancient submerged stone ruins glowing underwater with mysterious shafts of turquoise light"},
]


def get_surplus_bank_dir(channel_id: str) -> Path:
    ch_dir = BANK_DIR / channel_id
    ch_dir.mkdir(parents=True, exist_ok=True)
    return ch_dir


def harvest_surplus_api_assets(channel_id: str, max_clips: int = 5) -> int:
    """
    يقوم بحصاد وتوليد لقطات فيديو سينمائية مسبقة للاستفادة الكاملة من الحصص المجانية اليومية المتجددة.
    """
    ch_dir = get_surplus_bank_dir(channel_id)
    pixabay_key = os.environ.get("PIXABAY_API_KEY", "").strip() or "58562427-888666fb1b6895d44dd719aa6"
    harvested = 0

    print(f"[{channel_id}][SURPLUS-BANK] فحص واستغلال الحصص المجانية المتجددة لتجهيز أصول الحلقات القادمة...", flush=True)

    for theme in CURATED_SURPLUS_THEMES:
        if harvested >= max_clips:
            break

        tag = theme["tag"]
        target_mp4 = ch_dir / f"surplus_{tag}.mp4"
        meta_json = ch_dir / f"surplus_{tag}.json"

        # لو الملف موجود بالفعل وصالح نتخطاه لتوفير الحصة لباقي المشاهد
        if target_mp4.exists() and target_mp4.stat().st_size > 25000:
            continue

        try:
            if pixabay_key:
                url = f"https://pixabay.com/api/videos/?key={pixabay_key}&q={requests.utils.quote(theme['query'])}&video_type=film&per_page=4"
                r = requests.get(url, timeout=12)
                if r.status_code == 200:
                    hits = r.json().get("hits", [])
                    if hits:
                        hit = hits[harvested % len(hits)]
                        v_obj = hit.get("videos", {})
                        v_url = (
                            v_obj.get("large", {}).get("url")
                            or v_obj.get("medium", {}).get("url")
                            or v_obj.get("small", {}).get("url")
                        )
                        if v_url:
                            vb = requests.get(v_url, timeout=25).content
                            if len(vb) > 25000:
                                target_mp4.write_bytes(vb)
                                meta = {
                                    "tag": tag,
                                    "query": theme["query"],
                                    "prompt": theme["prompt"],
                                    "harvested_at": time.time(),
                                    "file_size": len(vb),
                                }
                                meta_json.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
                                harvested += 1
                                print(f"    💎 [Banked] تم استغلال حصة API مجانية وتخزين لقطة: «{tag}» ({len(vb)} بايت)", flush=True)
                                time.sleep(1.0)
        except Exception as exc:
            print(f"    ⚠️ [Surplus-Bank-Warn] تعذر حصاد {tag}: {exc}", flush=True)

    print(f"[{channel_id}][SURPLUS-BANK] ✅ تم تأمين {harvested} مقطع فيديو في البنك الاحتياطي للاستخدام الفوري في الحلقات القادمة.", flush=True)
    return harvested


def claim_surplus_clips_for_episode(channel_id: str, count: int = 12) -> List[Path]:
    """
    تسحب لقطات الفيديو المخزنة من الحصص الفائضة لدعم الفيلم القادم كفيلم سينمائي متصل!
    """
    ch_dir = get_surplus_bank_dir(channel_id)
    ready_clips = sorted(ch_dir.glob("surplus_*.mp4"))
    claimed: List[Path] = []

    for p in ready_clips:
        if p.exists() and p.stat().st_size > 25000:
            claimed.append(p)
            if len(claimed) >= count:
                break

    return claimed
