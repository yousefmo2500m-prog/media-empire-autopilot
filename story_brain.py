# -*- coding: utf-8 -*-
"""
عقل القصة والتأليف السينمائي V2.0 (Story Brain Multi-Engine)
- محرك ذكاء اصطناعي متعدد المزودين (Multi-Provider Fallback Engine):
  1. Google Gemini Flash (gemini-flash-lite-latest, gemini-flash-latest, gemini-3.5-flash-lite, gemini-2.5-flash-lite)
  2. Groq Cloud (llama-3.3-70b-versatile, llama-3.1-8b-instant)
  3. BigModel GLM-4-Flash (ZhipuAI Lifetime Free Tier)
  4. Hugging Face Serverless Router (Qwen2.5-72B-Instruct)
  5. Local Deterministic Narrative Fallback Engine
- يدعم تدوير كافة المفاتيح تلقائياً (Key Rotation & Auto-Heal).
"""

import json
import os
import re
import requests
from pathlib import Path
from typing import Any, Dict, List, Optional
import _env_loader

GEMINI_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-3-flash-preview"
]

def _collect_keys(prefix_or_names: List[str]) -> List[str]:
    """تجميع مفاتيح البيئة الصالحة مع منع التكرار"""
    keys = []
    for k in prefix_or_names:
        v = os.environ.get(k, "").strip()
        if v and v not in keys:
            keys.append(v)
    return keys

def _get_gemini_keys() -> List[str]:
    """دالة التوافقية مع smart_director"""
    return _collect_keys(["GEMINI_API_KEY_2", "GEMINI_API_KEY", "GEMINI_API_KEY_3"])

def _clean_json_text(raw_text: str) -> Optional[Dict[str, Any]]:
    """استخراج كائن JSON من النص الخام حتى لو احتوى على كتل ماركداون أو نصوص جانبية"""
    try:
        clean = re.sub(r"^```(?:json)?\s*", "", raw_text.strip())
        clean = re.sub(r"\s*```$", "", clean).strip()
        # محاولة البحث عن أول { وآخر }
        start_idx = clean.find("{")
        end_idx = clean.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            clean = clean[start_idx:end_idx + 1]
        data = json.loads(clean)
        if isinstance(data, dict) and ("scenes" in data or "narration_text" in data):
            if "narration_text" not in data and "scenes" in data:
                data["narration_text"] = " ".join(
                    sc.get("dialogue", sc.get("narration_part", "")) for sc in data["scenes"]
                ).strip()
            return data
    except Exception:
        pass
    return None

def _try_gemini(prompt: str) -> Optional[Dict[str, Any]]:
    """محاولة التوليد عبر مزود Google Gemini مع تدوير المفاتيح والموديلات"""
    keys = _collect_keys(["GEMINI_API_KEY_2", "GEMINI_API_KEY", "GEMINI_API_KEY_3"])
    if not keys:
        return None

    for key in keys:
        for model in GEMINI_MODELS:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                r = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    timeout=20
                )
                if r.status_code == 200:
                    raw = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    parsed = _clean_json_text(raw)
                    if parsed:
                        print(f"   [StoryBrain] Story generated via Gemini ({model})")
                        return parsed
            except Exception:
                continue
    return None

def _try_groq(prompt: str) -> Optional[Dict[str, Any]]:
    """محاولة التوليد عبر Groq Cloud API الفائق السرعة"""
    groq_keys = [f"GROQ_API_KEY_{i}" for i in range(1, 11)] + ["GROQ_API_KEY", "GROQ_KEY"]
    keys = _collect_keys(groq_keys)
    if not keys:
        return None

    models = [
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "allam-2-7b"
    ]
    for key in keys:
        for model in models:
            try:
                r = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "response_format": {"type": "json_object"}
                    },
                    timeout=15
                )
                if r.status_code == 200:
                    raw = r.json()["choices"][0]["message"]["content"].strip()
                    parsed = _clean_json_text(raw)
                    if parsed:
                        print(f"   [StoryBrain] Story generated via Groq ({model})")
                        return parsed
            except Exception:
                continue
    return None

def _try_bigmodel(prompt: str) -> Optional[Dict[str, Any]]:
    """محاولة التوليد عبر BigModel GLM-4-Flash المجاني دائمياً"""
    keys = _collect_keys(["BIGMODEL_API_KEY", "ZHIPUAI_API_KEY", "GLM_API_KEY"])
    if not keys:
        return None

    for key in keys:
        try:
            r = requests.post(
                "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "glm-4-flash",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                },
                timeout=20
            )
            if r.status_code == 200:
                raw = r.json()["choices"][0]["message"]["content"].strip()
                parsed = _clean_json_text(raw)
                if parsed:
                    print("   [StoryBrain] Story generated via BigModel GLM-4-Flash")
                    return parsed
        except Exception:
            continue
    return None

def _try_huggingface(prompt: str) -> Optional[Dict[str, Any]]:
    """محاولة التوليد عبر Hugging Face Serverless Router"""
    hf_keys = [f"HF_TOKEN_{i}" for i in range(1, 11)] + ["HF_TOKEN", "HUGGINGFACE_API_KEY"]
    keys = _collect_keys(hf_keys)
    if not keys:
        return None

    models = ["Qwen/Qwen2.5-72B-Instruct", "meta-llama/Llama-3.3-70B-Instruct"]
    for key in keys:
        for model in models:
            try:
                r = requests.post(
                    f"https://api-inference.huggingface.co/models/{model}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 1200
                    },
                    timeout=20
                )
                if r.status_code == 200:
                    raw = r.json()["choices"][0]["message"]["content"].strip()
                    parsed = _clean_json_text(raw)
                    if parsed:
                        print(f"   [StoryBrain] Story generated via HuggingFace ({model})")
                        return parsed
            except Exception:
                continue
    return None

def generate_reel_story(channel_info: Dict[str, Any], call_idx: int = 0) -> Dict[str, Any]:
    """يولد اسكريبت ريلز خاطف (45-55 ثانية) بالعامية المصرية أو الإنجليزية عبر المحركات المتتالية مع حماية كاملة."""
    c_name = channel_info.get("name", "أساطير")
    c_theme = channel_info.get("theme") or channel_info.get("tagline", "خيال علمي وأساطير")
    c_style = channel_info.get("voice_style") or channel_info.get("bio", "تشويق وإثارة")
    lang = channel_info.get("lang", "ar")

    if lang == "ar":
        system_prompt = f"""أنت مخرج ومؤلف سينمائي مصري عبقري متخصص في إنتاج دراما الغموض والإثارة الفيروسية لقناة '{c_name}' على غرار كبار صناع المحتوى (محيي أبو زيد وسرداب الأساطير).
التخصص والموضوع: {c_theme}
الهوية والأسلوب: {c_style}

قواعد الإخراج الإلزامية:
1. ليست مشاهد عشوائية على الكلمات؛ بل فيلم سينمائي قصير متكامل ومتصل ومترابط الأحداث والشخصيات.
2. تعدد الشخصيات الحوارية: حوار درامي حي وممتع وطبيعي بالعامية المصرية الصميمة (ليس كلمتين جافتين)، يضم الراوي مع شخصيتين حواريتين على الأقل (مثل الشاب المغامر، الفتاة، الشيخ الحكيم، أو الكيان الأثري).
3. تدرج سينمائي في اللقطات: (Shot 1: كادر تأسيسي واسع مع عاصفة ورياح -> Shot 2: كادر متوسط وتفاعل وحوار وتوتر -> Shot 3: زاوية POV من فوق الكتف مع اكتشاف اللغز -> Shot 4: لقطة مقربة فائقة لكسر القفل أو فتح الحجر -> Shot 5: قمة الذروة والصدمة).
4. تحديد مؤثر الفولي الصوتي لكل لقطة: (wind, stone_friction, wooden_creak, parchment_turn, heartbeat_ramp, braam_hit, explosion).
5. صياغة التعليق المثبت التفاعلي (Pinned Comment) الذي يشعل الجدل والنقاش في الكومنتات.

أنتج النتيجة كـ JSON صارم فقط دون أي نص إضافي:
{{
  "hook_title": "عنوان درامي صادم يخطف المشاهد",
  "hook_badge": "⚠️ تحقيق غامض",
  "pinned_comment": "سؤال جدلي ناري للمشاهدين يُثبت في أول التعليقات لإشعال النقاش وتكثير التفاعل",
  "cliffhanger_hook": "جملة قفلة صادمة في آخر ثانيتين تدعو لمتابعة الجزء الثاني فوراً",
  "scenes": [
    {{
      "shot_number": 1,
      "shot_type": "establishing_wide",
      "character_name": "الراوي",
      "voice_role": "narrator",
      "dialogue": "في ليلة كانت الرياح فيها بتهب على المقبرة المهجورة زي صفير تحذيري.. دخلنا المكان اللي كل أهالي القرية حذرونا من عتبته!",
      "foley_sfx": "wind_howl",
      "visual_prompt": "Cinematic wide establishing shot of an ominous ancient sandstone tomb entrance at midnight, violent desert dust storm swirling, dramatic volumetric amber torchlight, photorealistic 8k, 35mm film grain"
    }},
    {{
      "shot_number": 2,
      "shot_type": "medium_dialogue",
      "character_name": "يوسف",
      "voice_role": "hero",
      "dialogue": "يا مريم بلاش نقرب من الباب ده.. النقش الهيروغليفي المكتوب على الجدار ده بيقول إن اللي هيزيح الحجر مش هيطلع سليم!",
      "foley_sfx": "heartbeat_ramp",
      "visual_prompt": "Cinematic medium two-shot of a young terrified Egyptian adventurer holding a flickering torch looking nervously at his companion, ancient stone corridors, detailed expressive eyes, dramatic shadows, 8k"
    }},
    {{
      "shot_number": 3,
      "shot_type": "pov_discovery",
      "character_name": "مريم",
      "voice_role": "female_lead",
      "dialogue": "اسمع الصوت ده كويس.. ده مش صوت صدى، في حاجة بتتحرك ورا الجدار الصخري ده وبتزيح الحجر ناحيتنا!",
      "foley_sfx": "stone_friction",
      "visual_prompt": "Over-the-shoulder POV shot inspecting a massive sealed granite door with ancient glowing cracks, dust crumbling between stone seams, extreme depth of field, hyperrealistic texture"
    }},
    {{
      "shot_number": 4,
      "shot_type": "extreme_close_up",
      "character_name": "الكاهن الأثري",
      "voice_role": "entity",
      "dialogue": "من تجرأ على كسر ختم الصمت بعد ثلاثة آلاف عام؟ لن تغادروا هذا السرداب!",
      "foley_sfx": "braam_hit",
      "visual_prompt": "Cinematic extreme close-up of a terrifying shadowy ancient silhouette with glowing cyan eyes emerging from deep darkness, volumetric smoke, cinematic horror lighting, 8k masterpiece"
    }},
    {{
      "shot_number": 5,
      "shot_type": "climax_cliffhanger",
      "character_name": "الراوي",
      "voice_role": "narrator",
      "dialogue": "وهنا وفجأة.. انطفأت كل المشاعل، وانقفل الباب الصخري ورانا تماماً! انتظروا الجزء الثاني لمعرفة ما حدث!",
      "foley_sfx": "sub_bass_drop",
      "visual_prompt": "Cinematic shock cut to complete darkness with a single glowing ancient hieroglyphic seal violently slamming shut, dust shockwave, dramatic film still"
    }}
  ]
}}"""
    else:
        system_prompt = f"""You are an elite cinematic mystery director and scriptwriter for '{c_name}' on Facebook Reels.
Niche & Theme: {c_theme}
Tone & Style: {c_style}

Directing Directives:
1. Not disjointed random stock footage; a continuous, connected cinematic short film with consistent narrative flow.
2. Multi-character dramatic dialogue with rising suspense and realistic tension.
3. Cinematic shot progression (Wide establishing -> Medium dialogue tension -> POV discovery -> Extreme close-up -> Shock climax).
4. Foley SFX cues (wind_howl, stone_scrape, wooden_creak, parchment_turn, heartbeat_ramp, braam_hit, sub_bass_drop).
5. Viral Pinned Comment to ignite comment section debates.

Output strict JSON only:
{{
  "hook_title": "Viral Cinematic Title",
  "hook_badge": "⚠️ CLASSIFIED DOSSIER",
  "pinned_comment": "Provocative debate question for viewers to discuss in the comments",
  "cliffhanger_hook": "Shocking cliffhanger call to action for Part 2",
  "scenes": [
    {{
      "shot_number": 1,
      "shot_type": "establishing_wide",
      "character_name": "Narrator",
      "voice_role": "narrator",
      "dialogue": "Deep in the forgotten Siberian perimeter, an undocumented vault breached yesterday...",
      "foley_sfx": "wind_howl",
      "visual_prompt": "Cinematic wide shot of a frozen military bunker entrance during a blizzarding arctic twilight, cinematic lighting, 35mm lens, 8k"
    }}
  ]
}}"""

    # 1. Groq Cloud (72,000 requests/day - Instant response in 0.5s)
    res = _try_groq(system_prompt)
    if res:
        return res

    # 2. Gemini Flash Multi-Key / Multi-Model
    res = _try_gemini(system_prompt)
    if res:
        return res

    # 3. BigModel GLM-4-Flash
    res = _try_bigmodel(system_prompt)
    if res:
        return res

    # 4. Hugging Face Serverless
    res = _try_huggingface(system_prompt)
    if res:
        return res

    # 5. Resilient Dynamic Fallback (Never Fails)
    print("   [StoryBrain] Activating dynamic narrative fallback engine")
    if lang == "ar":
        return {
            "hook_title": f"سراديب محرمة تكشفها {c_name}",
            "hook_badge": "⚠️ تحقيق سري",
            "pinned_comment": "لو كنت مكان يوسف ولقيت الباب الصخري ده.. كنت هتدخل السرداب ولا هتهرب فوراً؟ مستني رأيكم تحت 👇",
            "cliffhanger_hook": "وفي اللحظة دي.. انقفل الباب تماماً! تابعوا الجزء الثاني لمعرفة المصير!",
            "scenes": [
                {
                    "shot_number": 1,
                    "shot_type": "establishing_wide",
                    "character_name": "الراوي",
                    "voice_role": "narrator",
                    "dialogue": f"في ليلة شديدة الرياح بالقرب من مقبرة قديمة تخص {c_name}.. وقف يوسف ومريم قدام مدخل سرداب مهجور بقاله آلاف السنين!",
                    "foley_sfx": "wind_howl",
                    "visual_prompt": "Cinematic wide establishing shot of an ancient sandstone tomb entrance at midnight, swirling desert sandstorm, flickering volumetric amber torches, 35mm film grain, 8k"
                },
                {
                    "shot_number": 2,
                    "shot_type": "medium_dialogue",
                    "character_name": "يوسف",
                    "voice_role": "hero",
                    "dialogue": "يا مريم الرياح دي مش طبيعية، والنقش اللي على الحجر بيحذر من لمس البوابة.. خلينا نرجع فوراً!",
                    "foley_sfx": "heartbeat_ramp",
                    "visual_prompt": "Cinematic medium two-shot of a young anxious Egyptian explorer holding a torch, glancing nervously at an ancient inscribed stone doorway, photorealistic 8k"
                },
                {
                    "shot_number": 3,
                    "shot_type": "pov_discovery",
                    "character_name": "مريم",
                    "voice_role": "female_lead",
                    "dialogue": "بص ورا الحجر ده يا يوسف.. النقوش الهيروغليفية بدأت تتوهج بلون أزرق غريب والحجر بيتحرك لوحده!",
                    "foley_sfx": "stone_friction",
                    "visual_prompt": "Over-the-shoulder POV shot looking closely at glowing ancient hieroglyphic stone cracks sliding open, dust crumbling down, cinematic volumetric lighting"
                },
                {
                    "shot_number": 4,
                    "shot_type": "extreme_close_up",
                    "character_name": "الكاهن الأثري",
                    "voice_role": "entity",
                    "dialogue": "من تجرأ على إيقاظ حارس السرداب؟ لن يخرج أحد من هنا على قيد الحياة!",
                    "foley_sfx": "braam_hit",
                    "visual_prompt": "Cinematic extreme close-up of a dark ancient shadowy entity with piercing glowing cyan eyes stepping from darkness, dramatic rim lighting, 8k"
                },
                {
                    "shot_number": 5,
                    "shot_type": "climax_cliffhanger",
                    "character_name": "الراوي",
                    "voice_role": "narrator",
                    "dialogue": "وهنا وبضغطة واحدة، انقفل الباب الصخري ورانا تماماً! تابعوا الجزء الثاني لمعرفة ما حدث!",
                    "foley_sfx": "sub_bass_drop",
                    "visual_prompt": "Cinematic dramatic slam of a massive stone vault door sealing shut in darkness, dust explosion shockwave, high-contrast shadows, 8k"
                }
            ]
        }
    else:
        return {
            "hook_title": f"Forbidden Vault of {c_name}",
            "hook_badge": "⚠️ TOP SECRET",
            "pinned_comment": "If you stood before this locked vault in the dark, would you turn the key or run? Comment below 👇",
            "cliffhanger_hook": "And then the iron door sealed shut behind them! Follow for Part 2!",
            "scenes": [
                {
                    "shot_number": 1,
                    "shot_type": "establishing_wide",
                    "character_name": "Narrator",
                    "voice_role": "narrator",
                    "dialogue": f"Deep inside the perimeter linked to {c_name}, investigators breached a sealed subterranean chamber lost for centuries.",
                    "foley_sfx": "wind_howl",
                    "visual_prompt": "Cinematic wide shot of a frozen military bunker entrance during a blizzarding arctic twilight, cinematic lighting, 35mm lens, 8k"
                },
                {
                    "shot_number": 2,
                    "shot_type": "medium_dialogue",
                    "character_name": "Investigator",
                    "voice_role": "hero",
                    "dialogue": "The frequency emitter is spiking off the charts. We should not be opening this chamber!",
                    "foley_sfx": "heartbeat_ramp",
                    "visual_prompt": "Cinematic medium shot of two researchers with flashlights staring at an anomalous glowing steel bulkhead, volumetric atmospheric fog"
                },
                {
                    "shot_number": 3,
                    "shot_type": "pov_discovery",
                    "character_name": "Scientist",
                    "voice_role": "female_lead",
                    "dialogue": "Look at the seal... the locking gears are rotating by themselves from the inside!",
                    "foley_sfx": "stone_friction",
                    "visual_prompt": "Over the shoulder shot inspecting heavy mechanical vault locking pins sliding open in darkness, sparks and steam"
                },
                {
                    "shot_number": 4,
                    "shot_type": "extreme_close_up",
                    "character_name": "The Anomaly",
                    "voice_role": "entity",
                    "dialogue": "You have broken the cycle. The quarantine has ended.",
                    "foley_sfx": "braam_hit",
                    "visual_prompt": "Cinematic extreme close-up of a glowing biomechanical monolith awakening in deep darkness, pulsing blue plasma rays, 8k"
                },
                {
                    "shot_number": 5,
                    "shot_type": "climax_cliffhanger",
                    "character_name": "Narrator",
                    "voice_role": "narrator",
                    "dialogue": "Within seconds, the blast doors locked permanently. Watch Part 2 to see what happens next!",
                    "foley_sfx": "sub_bass_drop",
                    "visual_prompt": "Dramatic heavy vault door slamming shut, emergency red strobe light, smoke billows, 35mm film still"
                }
            ]
        }
