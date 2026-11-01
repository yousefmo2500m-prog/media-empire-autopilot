# -*- coding: utf-8 -*-
"""
مؤلف الإثارة النفسية وحلقات الدوبامين المفتوحة V6.0 (Psychological Open-Loop Thriller Brain)
يطبق قوانين علم نفس الانتباه والاحتفاظ بالمشاهد (Zeigarnik Effect & Dopamine Loops):
1) ممنوع نهائياً المقدمات التقليدية ("تعالوا أحكيلكم"، "في يوم من الأيام") — تبدأ القصة في الثانية الأولى بلحظة صدمة أو تناقض مستحيل (الساعة 3 الفجر، غرفة مغلقة من الداخل، رسالة من شخص مختفٍ، كاميرا تلتقط مستحيلاً).
2) كل فصل يفتح لغزاً أكبر قبل إغلاق اللغز السابق ليبقى المشاهد مشدوداً لمدة 16–18 دقيقة متواصلة.
3) عامية مصرية قاهرية حقيقية ونظيفة 100% بدون تشكيل غريب أو جمل مترجمة ركيكة، وآمنة تماماً لإعلانات يوتيوب وفيسبوك وتيك توك.
4) يولّد 10 أوصاف مشاهد ذكاء اصطناعي سينمائية داكنة (Dark Thriller Cinema Stills) تعبّر عما يحدث لحظة بلحظة.
"""

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List

import requests

GROQ_BASE = "https://api.groq.com/openai/v1"
PREFERRED_MODELS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
]


def load_memory(memory_path: Path) -> Dict[str, Any]:
    if memory_path.exists():
        try:
            return json.loads(memory_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {k: {"used_topics": []} for k in ("ch1_eg_thriller", "ch2_eg_mystery", "ch3_en_thriller", "ch4_en_mystery")}


def save_memory(memory_path: Path, data: Dict[str, Any]) -> None:
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    memory_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _extract_json(raw: str) -> Dict[str, Any]:
    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, flags=re.DOTALL)
    if fence:
        cleaned = fence.group(1)
    else:
        s, e = cleaned.find("{"), cleaned.rfind("}")
        if s != -1 and e > s:
            cleaned = cleaned[s : e + 1]
    return json.loads(cleaned)


def _groq_json(api_key: str, sys_prompt: str, usr_prompt: str, max_tokens: int = 5000) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    last_err = None
    for attempt in range(9):
        cur_model = PREFERRED_MODELS[attempt % len(PREFERRED_MODELS)]
        try:
            payload = {
                "model": cur_model,
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": usr_prompt},
                ],
                "temperature": 0.84,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            }
            resp = requests.post(f"{GROQ_BASE}/chat/completions", headers=headers, json=payload, timeout=95)
            if resp.status_code == 429:
                time.sleep(min(14.0, float(resp.headers.get("retry-after", 4.5))))
                continue
            if resp.status_code != 200:
                payload.pop("response_format", None)
                resp = requests.post(f"{GROQ_BASE}/chat/completions", headers=headers, json=payload, timeout=95)
                if resp.status_code == 429:
                    time.sleep(5.0)
                    continue
            resp.raise_for_status()
            return _extract_json(resp.json()["choices"][0]["message"]["content"])
        except Exception as exc:
            last_err = exc
            time.sleep(2.5)
    raise RuntimeError(f"Groq JSON generation failed: {last_err}")


def generate_full_episode_and_short(
    channel_cfg: Dict[str, Any],
    api_key: str,
    memory: Dict[str, Any],
) -> Dict[str, Any]:
    cid = channel_cfg["id"]
    used = memory.setdefault(cid, {"used_topics": []}).get("used_topics", [])[-60:]
    lang = channel_cfg["language"]
    niche = channel_cfg["niche"]

    if lang == "ar":
        style_guide = (
            "أنتِ كاتبة سيناريو إثارة نفسية وتشويق من الطراز الأول، تكتبين بالعامية المصرية القاهرية الطبيعية 100% "
            "كما يحكي المصريون في الحقيقة تماماً (بدون أي فصحى مدرسية، وبدون أي شدّات أو تشكيل يربك النطق، وبدون مقدمات مثل «تعالوا أحكيلكم»). "
            "تطبقين علم نفس الحلقات المفتوحة (Zeigarnik Open Loops): أول ثانية تبدأ داخل قلب الحدث بصدمة مستحيلة أو خطر غامض، "
            "وكل 60 ثانية تظهر مفاجأة تقلب توقعات المستمع بالكامل، مع التزام كامل بمعايير أمان الإعلانات (تشويق نفسي وذكاء قانوني بدون عنف دموي)."
        )
        niche_desc = (
            "إثارة نفسية عائلية/مالية تحبس الأنفاس (مثل رسالة في الفجر تكشف مؤامرة كبرى من أقرب الناس، وكيف يقلب البطل الفخ بذكاء قانوني مذهل)"
            if niche == "eg_psych_thriller"
            else "لغز غامض ومستحيل عقلياً في مكان واقعي بمصر (مثل طابق سري غير موجود في الخريطة، أو غرفة مغلقة اختفى منها شيء مستحيل، وكيف يتكشف السر المذهل خطوة بخطوة)"
        )
        blueprint_prompt = f"""
الأفكار المستعملة سابقاً (ممنوع تكرارها نهائياً): {used}

صمّمي حلقة إثارة وتشويق نفسي كاملة مدتها 16–17 دقيقة من نوع: {niche_desc}
أخرجي JSON صالح بالهيكل التالي:
{{
  "topic_key": "ملخص 5 كلمات للفكرة",
  "youtube_title": "عنوان يوتيوب ناري بالعامية المصرية يثير فضولاً لا يقاوم",
  "short_1_title": "عنوان ناري للشورت الأول (صدمة البداية) + #shorts #قصص",
  "short_2_title": "عنوان ناري مختلف للشورت الثاني (المفاجأة الكبرى في قلب القصة) + #shorts #قصص",
  "description": "وصف مشوق جداً للحلقة + هاشتاجات",
  "acts_outline": [
    {{"act_num": 1, "act_title": "عنوان الفصل 1", "summary": "دخول مباشر في أول ثانية بحدث صادم ومستحيل + أول مفاجأة"}},
    {{"act_num": 2, "act_title": "عنوان الفصل 2", "summary": "اكتشاف الدليل المخفي واتساع دائرة الشك"}},
    {{"act_num": 3, "act_title": "عنوان الفصل 3", "summary": "المفاجأة الصادمة عن الشريك الخفي وتصميم الفخ النفسي"}},
    {{"act_num": 4, "act_title": "عنوان الفصل 4", "summary": "المواجهة الحابسة للأنفاس ولحظة الوقوع في المصيدة"}},
    {{"act_num": 5, "act_title": "عنوان الفصل 5", "summary": "كشف كل الخيوط وانقلاب الطاولة والعدالة الكاملة + سؤال تفاعلي"}}
  ],
  "scene_prompts": [
    "Wide 16:9 widescreen cinematic dark thriller film still for Scene 1, photorealistic, dramatic chiaroscuro lighting, expressive faces, no text, no watermark",
    "Wide 16:9 widescreen cinematic dark thriller film still for Scene 2, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic dark thriller film still for Scene 3, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic dark thriller film still for Scene 4, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic dark thriller film still for Scene 5, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic dark thriller film still for Scene 6, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic dark thriller film still for Scene 7, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic dark thriller film still for Scene 8, photorealistic, no text, no watermark"
  ],
  "cliffhanger_short_1_body": "أقوى 130 كلمة من افتتاحية القصة بالعامية المصرية الصافية تبدأ في الثانية الأولى بالصدمة وتقف فجأة في ذروة الرعب والتشويق قبل كشف من وراء الباب مباشرة!",
  "cliffhanger_short_2_body": "أقوى 130 كلمة من منتصف القصة (لحظة اكتشاف الخدعة الخفية وتجهيز المصيدة) بالعامية المصرية الصافية تبدأ فجأة بدون مقدمات وتقف في ذروة الصدمة قبل وقوعهم في الكمين بثانية واحدة!"
}}
"""
    else:
        style_guide = (
            "You are an elite psychological thriller & mystery storyteller (combining MrBallen's claustrophobic suspense with razor-sharp legal/twist payoffs). "
            "NEVER write slow introductions—drop the listener into an impossible, heart-pounding sensory moment at 2:47 AM in sentence one. "
            "Use nested Zeigarnik open loops every 60 seconds and keep content 100% advertiser-safe (psychological tension, zero gore)."
        )
        niche_desc = (
            "a high-adrenaline domestic/financial psychological thriller with a jaw-dropping midnight discovery, hidden betrayal, and genius legal trap"
            if niche == "en_psych_thriller"
            else "an impossible locked-room / vanished-vessel / hidden-floor real-style mystery investigation where every clue deepens the paranoia until a mind-blowing reveal"
        )
        blueprint_prompt = f"""
Avoid all previously used premises: {used}

Design a complete 16-minute 5-Act thriller episode for: {niche_desc}.
Return exact valid JSON:
{{
  "topic_key": "5-word unique summary",
  "youtube_title": "Impossible-to-ignore high-CTR YouTube title",
  "short_1_title": "Viral cliffhanger title #1 (midnight shock hook) #shorts #thriller",
  "short_2_title": "Viral cliffhanger title #2 (mid-story secret trap hook) #shorts #mystery",
  "description": "Gripping description + hashtags",
  "acts_outline": [
    {{"act_num": 1, "act_title": "Act 1 Title", "summary": "Immediate 3-second shock hook + first escalation"}},
    {{"act_num": 2, "act_title": "Act 2 Title", "summary": "Hidden clue & deepening paranoia"}},
    {{"act_num": 3, "act_title": "Act 3 Title", "summary": "Second shocking twist & setting the trap"}},
    {{"act_num": 4, "act_title": "Act 4 Title", "summary": "High-wire confrontation & irreversible mistake by antagonist"}},
    {{"act_num": 5, "act_title": "Act 5 Title", "summary": "Jaw-dropping reveal, full justice & closing comment question"}}
  ],
  "scene_prompts": [
    "Wide 16:9 widescreen cinematic dark thriller movie still for Scene 1, photorealistic, dramatic shadows, no text, no watermark",
    "Wide 16:9 widescreen cinematic dark thriller movie still for Scene 2, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic dark thriller movie still for Scene 3, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic dark thriller movie still for Scene 4, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic dark thriller movie still for Scene 5, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic dark thriller movie still for Scene 6, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic dark thriller movie still for Scene 7, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic dark thriller movie still for Scene 8, photorealistic, no text, no watermark"
  ],
  "cliffhanger_short_1_body": "135-word heart-pounding opening hook starting in second one and cutting RIGHT at the sharpest cliffhanger before the reveal!",
  "cliffhanger_short_2_body": "135-word mid-story escalation starting right when the hidden second twist/clue is found and cutting ONE SECOND before the trap snaps shut!"
}}
"""

    plan = _groq_json(api_key, style_guide, blueprint_prompt, max_tokens=5000)

    acts_full: List[Dict[str, Any]] = []
    prev_tail = ""
    for act in plan.get("acts_outline", []):
        anum = act["act_num"]
        atitle = act["act_title"]
        asum = act["summary"]

        if lang == "ar":
            act_prompt = f"""
عنوان القصة: {plan.get('youtube_title')}
مخطط الفصول: {json.dumps(plan.get('acts_outline'), ensure_ascii=False)}
نهاية الفصل السابق (أكملي بعدها مباشرة بتصاعد ناري بدون تكرار): "{prev_tail}"

اكتبي النص الكامل المسموع لـ **الفصل {anum} ({atitle})** بحيث يغطي: {asum}
قواعد صارمة لا تقبل التهاون:
1. الطول: **بين 490 و 550 كلمة كاملة** بالعامية المصرية القاهرية الطبيعية السلسة بدون أي تشكيل أو شدّات وبدون أي جمل فصحى مدرسية.
2. ممنوع أي مقدمات إنشائية! ادخلي فوراً في الحركة، الأصوات، الحوارات المتوترة، والتفاصيل النفسية الدقيقة.
3. أرجعي JSON فقط: {{"narration": "النص الكامل المتصل للفصل"}}
"""
        else:
            act_prompt = f"""
Title: {plan.get('youtube_title')}
Outline: {json.dumps(plan.get('acts_outline'))}
Previous ending (continue seamlessly): "{prev_tail}"

Write the full spoken narration for **Act {anum} ({atitle})** covering: {asum}
Strict rules:
1. Length: **between 500 and 560 words** of taut, sensory, conversational American thriller storytelling.
2. Zero fluff or generic summary—use real-time suspense, dialogue, micro-clues, and open loops.
3. Return JSON only: {{"narration": "Full spoken text"}}
"""
        act_res = _groq_json(api_key, style_guide, act_prompt, max_tokens=3400)
        txt = str(act_res.get("narration", "")).strip()
        # إزالة أي تشكيل عربي يربك محركات النطق
        txt = re.sub(r"[\u064B-\u065F\u0670]", "", txt)
        acts_full.append({"act_num": anum, "act_title": atitle, "narration": txt})
        prev_tail = " ".join(txt.split()[-35:])

    cliff_1 = re.sub(
        r"[\u064B-\u065F\u0670]",
        "",
        str(plan.get("cliffhanger_short_1_body") or plan.get("cliffhanger_short_body") or " ".join(acts_full[0]["narration"].split()[:130])).strip(),
    )
    mid_act_idx = min(2, len(acts_full) - 1)
    cliff_2 = re.sub(
        r"[\u064B-\u065F\u0670]",
        "",
        str(plan.get("cliffhanger_short_2_body") or " ".join(acts_full[mid_act_idx]["narration"].split()[:130])).strip(),
    )
    short_1_full = f"{cliff_1} {channel_cfg['cta_spoken']}"
    short_2_full = f"{cliff_2} {channel_cfg['cta_spoken']}"

    tk = str(plan.get("topic_key") or plan.get("youtube_title", cid))[:80]
    if tk:
        memory[cid].setdefault("used_topics", []).append(tk)

    sh1_title = plan.get("short_1_title") or plan.get("short_title") or f"{plan.get('youtube_title', '')[:60]} #shorts"
    sh2_title = plan.get("short_2_title") or f"{plan.get('youtube_title', '')[:55]} - الجزء الأخطر #shorts"

    return {
        "channel_id": cid,
        "topic_key": tk,
        "youtube_title": plan.get("youtube_title", channel_cfg["brand_name"]),
        "short_title": sh1_title,
        "short_1_title": sh1_title,
        "short_2_title": sh2_title,
        "description": plan.get("description", ""),
        "acts": acts_full,
        "scene_prompts": (plan.get("scene_prompts") or [f"Wide 16:9 dark thriller film still scene {i+1}, no text" for i in range(8)])[:8],
        "short_narration": short_1_full,
        "short_1_narration": short_1_full,
        "short_2_narration": short_2_full,
        "cta_banner": channel_cfg["cta_banner"],
    }
