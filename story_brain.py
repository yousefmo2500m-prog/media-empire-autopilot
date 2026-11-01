# -*- coding: utf-8 -*-
"""
مؤلف الروايات المتنوعة وألغاز المحققين الذكية V7.5 (Diverse Novels & Detective Whodunit Brain)
يمنع ملل المشاهد نهائياً عبر التدوير التلقائي بين الألوان القصصية والبيئات المختلفة يومياً:
- القناة 1 (شريط حكايات): تدوير تلقائي بين (كوميديا مواقف مصرية ذكية وساخرة، دراما اجتماعية غير متوقعة، تشويق ومفاجآت، مغامرات حياتية غريبة، قصص إنسانية دافئة بنهاية مدهشة) حتى لا يتوقع المشاهد مسار القصة أبداً!
- القناة 2 (الخيط الخفي): قصص ألغاز وتحقيقات بوليسية كاملة عالية الذكاء على طريقة «المحقق كونان» وأجاثا كريستي بالعامية المصرية (لغز محكم، 3-4 مشتبه بهم لكل منهم حجة غياب قوية، أدلة ذكية مزروعة داخل السرد، واستنتاج عبقري يكشف الحيلة خطوة بخطوة).
- القناة 3 (OffScript Stories): تنوع روائي أمريكي ممتع (كوميديا ذكية، مفاجآت غير متوقعة، تشويق نفسي، دراما واقعية).
- القناة 4 (The Alibi Room): قضايا تحقيقات وألغاز استنتاجية ذكية (Whodunit / Locked-Room / Clever Alibi Mysteries).
"""

import json
import random
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

EG_NOVEL_FLAVORS = [
    "رواية كوميديا مواقف مصرية ذكية وساخرة جداً (موقف يبدأ بسيط ويتحول لسلسلة مفارقات مضحكة وذكية غير متوقعة بنهاية عبقرية)",
    "رواية اجتماعية مشوقة غير متوقعة المسار (سر قديم أو صدفة غريبة تقلب حياة أبطال القصة في اتجاه مستحيل توقعه)",
    "رواية إثارة وذكاء نفسي (خطة ذكية أو لغز اجتماعي معقد تتكشف خيوطه بمفاجآت عكس كل التوقعات)",
    "رواية مغامرة وتجربة حياتية غريبة في مكان غير مألوف بمصر تجمع بين خفة الدم والتشويق والدهشة",
    "رواية درامية إنسانية عميقة وممتعة فيها شخصيات مرسومة ببراعة ونهاية مدهشة تترك أثر كبير",
]

EG_CONAN_CASES = [
    "قضية لغز الغرفة المغلقة على طريقة المحقق كونان (سرقة قطعة نادرة أو اختفاء شخص مستحيل من مكان مغلق بالكامل، مع 4 مشتبه بهم وحيلة فيزيائية/زمنية ذكية جداً)",
    "قضية حجة الغياب المستحيلة على طريقة المحقق كونان (جريمة أو عملية سطو كبرى تحدث بينما المشتبه به الرئيسي يراه الجميع في مكان آخر، وتفصيلة عبقرية صغيرة تكشف الخدعة البصرية أو الزمنية)",
    "قضية القطار أو الباخرة النيلية أو الفندق المنعزل (لغز غامض وسط مجموعة ركاب محاصرين، رسائل مشفرة وأدلة متناقضة، واستنتاج مذهل في المواجهة الأخيرة)",
    "قضية الوصية المشفرة أو المزاد السري (لغز عقلي معقد بين ورثة أو خبراء، حيث تشير كل الأدلة لشخص بريء بينما الجاني الحقيقي استعمل خدعة عبقرية لا يكتشفها إلا محقق شديد الملاحظة)",
]

EN_STORY_FLAVORS = [
    "a sharp, witty comedy-of-errors & clever real-life curveball story where one small misunderstanding snowballs into an unforgettable, hilarious payoff",
    "an unpredictable slice-of-life & human drama novella where a strange coincidence or forgotten object changes everything in a way nobody sees coming",
    "a gripping psychological suspense story full of twists where the listener's assumptions get flipped upside down twice",
    "a brilliant workplace or neighborhood battle-of-wits story mixing dry humor, tension, and an unexpectedly wholesome or genius ending",
]

EN_DETECTIVE_CASES = [
    "a classic Detective Conan / Knives Out style locked-room mystery with 4 suspects, ironclad alibis, fair-play physical clues, and a razor-sharp final deduction",
    "an impossible clockwork alibi investigation where the culprit appeared to be miles away on camera, unraveled by one tiny overlooked detail",
    "an isolated luxury train, island hotel, or private museum heist-mystery where every witness hides a secret and a brilliant investigator connects the hidden thread",
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
                "temperature": 0.86,
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
    ep_count = len(used)

    if lang == "ar":
        if niche == "eg_conan_detective":
            flavor = EG_CONAN_CASES[ep_count % len(EG_CONAN_CASES)]
            style_guide = (
                "أنتِ روائية ألغاز وتحقيقات بوليسية عبقرية على طريقة «المحقق كونان» وأجاثا كريستي، تكتبين بالعامية المصرية القاهرية الطبيعية السلسة 100% "
                "بدون أي تشكيل أو فصحى مدرسية وبدون أي مقدمات تقليدية. تبدئين فوراً بوقوع اللغز المستحيل في أول ثانية، وتقدمين قصة كاملة متكاملة الأركان "
                "(مكان جديد ومختلف، 3 أو 4 شخصيات مرسومة بعمق لكل منهم دافع وحجة غياب، أدلة ذكية حقيقية مزروعة داخل الأحداث ليحاول المشاهد حل اللغز بنفسه، "
                "ثم استنتاج عبقري مدهش يكشف الخدعة بالتفصيل المنطقي في النهاية) مع الالتزام التام بأمان الإعلانات (بدون عنف دموي)."
            )
        else:
            flavor = EG_NOVEL_FLAVORS[ep_count % len(EG_NOVEL_FLAVORS)]
            style_guide = (
                "أنتِ روائية وحكّاءة مصرية موهوبة جداً تكتبين بالعامية المصرية القاهرية الطبيعية الحلوة 100% كما يحكي المصريون في الحقيقة "
                "(بدون أي تشكيل أو جمل مترجمة وبدون مقدمات مثل «تعالوا أحكيلكم»). تبدئين من أول ثانية بموقف لافت أو جملة تخطف الانتباه فوراً، "
                "وتحافظين على عنصر المفاجأة والتجديد وخفة الروح أو الشغف بحيث لا يتوقع المستمع أبداً ما سيحدث في الفصل التالي، مع الالتزام بأمان الإعلانات."
            )

        blueprint_prompt = f"""
الأفكار المستعملة سابقاً (ممنوع تكرارها أو التشابه معها نهائياً): {used}

صمّمي رواية صوتية / قضية كاملة وممتعة مدتها 16–17 دقيقة لهذا اليوم من نوع:
«{flavor}»

أخرجي JSON صالح بالهيكل التالي:
{{
  "topic_key": "ملخص 6 كلمات للفكرة والمكان",
  "youtube_title": "عنوان يوتيوب جذاب جداً بالعامية المصرية يثير الفضول بدون حرق النهاية",
  "short_1_title": "عنوان ناري للشورت الأول (لقطة البداية الخاطفة) + #shorts #حكايات",
  "short_2_title": "عنوان ناري مختلف للشورت الثاني (المفاجأة الكبرى بمنتصف القصة) + #shorts #قصص",
  "description": "وصف مشوق للحلقة + هاشتاجات",
  "acts_outline": [
    {{"act_num": 1, "act_title": "عنوان الفصل 1", "summary": "دخول فوري في أول ثانية بحدث خاطف وبداية القصة أو اللغز"}},
    {{"act_num": 2, "act_title": "عنوان الفصل 2", "summary": "تطور الأحداث وظهور الشخصيات والتفاصيل غير المتوقعة"}},
    {{"act_num": 3, "act_title": "عنوان الفصل 3", "summary": "مفاجأة كبرى في منتصف الرواية تغير مسار كل التوقعات"}},
    {{"act_num": 4, "act_title": "عنوان الفصل 4", "summary": "ذروة المواجهة أو لحظة تجميع خيوط اللغز بذكاء"}},
    {{"act_num": 5, "act_title": "عنوان الفصل 5", "summary": "الكشف الكامل المدهش والحل الذكي + سؤال تفاعلي للمشاهدين"}}
  ],
  "scene_prompts": [
    "Wide 16:9 widescreen cinematic film still matching Scene 1 of this exact story, photorealistic, rich atmospheric lighting, expressive characters, no text, no watermark",
    "Wide 16:9 widescreen cinematic film still matching Scene 2, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic film still matching Scene 3, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic film still matching Scene 4, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic film still matching Scene 5, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic film still matching Scene 6, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic film still matching Scene 7, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic film still matching Scene 8, photorealistic, no text, no watermark"
  ],
  "cliffhanger_short_1_body": "أقوى 130 كلمة من افتتاحية القصة بالعامية المصرية تبدأ في الثانية الأولى داخل الحدث وتقف فجأة عند أقوى لحظة فضول وتشويق!",
  "cliffhanger_short_2_body": "أقوى 130 كلمة من منتصف القصة (لحظة اكتشاف التفصيلة العجيبة أو المفارقة الكبرى) تبدأ مباشرة بدون مقدمات وتقف قبل الكشف بثانية واحدة!"
}}
"""
    else:
        if niche == "en_detective_mystery":
            flavor = EN_DETECTIVE_CASES[ep_count % len(EN_DETECTIVE_CASES)]
            style_guide = (
                "You are a master whodunit & mystery novelist in the tradition of Detective Conan, Agatha Christie, and Knives Out. "
                "Drop the listener into the impossible puzzle in sentence one, build a complete 16-minute mystery with vivid suspects, clever clues, "
                "and a deeply satisfying step-by-step deduction reveal. Keep it 100% advertiser-safe (clever sleuthing, zero gore)."
            )
        else:
            flavor = EN_STORY_FLAVORS[ep_count % len(EN_STORY_FLAVORS)]
            style_guide = (
                "You are a charismatic, versatile American audio-novelist who keeps listeners hooked with fresh, unpredictable stories—ranging from "
                "smart comedy-of-errors to gripping life twists and psychological drama. Never use slow intros; start in the middle of an unforgettable moment."
            )

        blueprint_prompt = f"""
Avoid all previously used premises: {used}

Design a complete 16-minute 5-Act story episode for today's flavor:
"{flavor}"

Return exact valid JSON:
{{
  "topic_key": "6-word unique premise & setting",
  "youtube_title": "High-curiosity YouTube title that never spoils the ending",
  "short_1_title": "Viral hook title #1 (opening moment) #shorts #stories",
  "short_2_title": "Viral hook title #2 (mid-story twist/clue) #shorts #mystery",
  "description": "Engaging episode description + hashtags",
  "acts_outline": [
    {{"act_num": 1, "act_title": "Act 1 Title", "summary": "Immediate 3-second hook + setup of characters/puzzle"}},
    {{"act_num": 2, "act_title": "Act 2 Title", "summary": "Escalating complications, suspects, or comedic/dramatic turns"}},
    {{"act_num": 3, "act_title": "Act 3 Title", "summary": "Mid-story curveball that upends every assumption"}},
    {{"act_num": 4, "act_title": "Act 4 Title", "summary": "Climax confrontation or piecing the hidden clues together"}},
    {{"act_num": 5, "act_title": "Act 5 Title", "summary": "Brilliant payoff/deduction & closing question for comments"}}
  ],
  "scene_prompts": [
    "Wide 16:9 widescreen cinematic movie still for Scene 1 matching this exact story, photorealistic, expressive lighting, no text, no watermark",
    "Wide 16:9 widescreen cinematic movie still for Scene 2, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic movie still for Scene 3, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic movie still for Scene 4, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic movie still for Scene 5, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic movie still for Scene 6, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic movie still for Scene 7, photorealistic, no text, no watermark",
    "Wide 16:9 widescreen cinematic movie still for Scene 8, photorealistic, no text, no watermark"
  ],
  "cliffhanger_short_1_body": "135-word opening hook starting in second one and cutting RIGHT at the sharpest curiosity peak!",
  "cliffhanger_short_2_body": "135-word mid-story twist starting right at the key clue/turn and cutting ONE SECOND before the reveal!"
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
نوع الرواية اليوم: {flavor}
مخطط الفصول: {json.dumps(plan.get('acts_outline'), ensure_ascii=False)}
نهاية الفصل السابق (أكملي بعدها مباشرة بسلاسة وتشويق بدون تكرار): "{prev_tail}"

اكتبي النص الكامل المسموع لـ **الفصل {anum} ({atitle})** بحيث يغطي: {asum}
قواعد صارمة:
1. الطول: **بين 490 و 550 كلمة كاملة** بالعامية المصرية القاهرية الطبيعية السلسة بدون أي تشكيل أو شدّات وبدون أي جمل فصحى مدرسية.
2. املئي الفصل بالحوارات الطبيعية الحية، التفاصيل الذكية، والمواقف الممتعة بدون أي حشو أو مقدمات.
3. أرجعي JSON فقط: {{"narration": "النص الكامل المتصل للفصل"}}
"""
        else:
            act_prompt = f"""
Title: {plan.get('youtube_title')}
Flavor: {flavor}
Outline: {json.dumps(plan.get('acts_outline'))}
Previous ending (continue seamlessly): "{prev_tail}"

Write the full spoken narration for **Act {anum} ({atitle})** covering: {asum}
Strict rules:
1. Length: **between 500 and 560 words** of vivid, natural American storytelling with crisp dialogue and concrete details.
2. Zero filler—keep every paragraph moving forward with curiosity, wit, or deduction clues.
3. Return JSON only: {{"narration": "Full spoken text"}}
"""
        act_res = _groq_json(api_key, style_guide, act_prompt, max_tokens=3400)
        txt = str(act_res.get("narration", "")).strip()
        txt = re.sub(r"[\u064B-\u065F\u0670]", "", txt)
        acts_full.append({"act_num": anum, "act_title": atitle, "narration": txt})
        prev_tail = " ".join(txt.split()[-35:])

    cliff_1 = re.sub(
        r"[\u064B-\u065F\u0670]",
        "",
        str(plan.get("cliffhanger_short_1_body") or " ".join(acts_full[0]["narration"].split()[:130])).strip(),
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

    sh1_title = plan.get("short_1_title") or f"{plan.get('youtube_title', '')[:60]} #shorts"
    sh2_title = plan.get("short_2_title") or f"{plan.get('youtube_title', '')[:55]} - الجزء الثاني #shorts"

    return {
        "channel_id": cid,
        "topic_key": tk,
        "youtube_title": plan.get("youtube_title", channel_cfg["brand_name"]),
        "short_title": sh1_title,
        "short_1_title": sh1_title,
        "short_2_title": sh2_title,
        "description": plan.get("description", ""),
        "acts": acts_full,
        "scene_prompts": (plan.get("scene_prompts") or [f"Wide 16:9 cinematic film still scene {i+1}, no text" for i in range(8)])[:8],
        "short_narration": short_1_full,
        "short_1_narration": short_1_full,
        "short_2_narration": short_2_full,
        "cta_banner": channel_cfg["cta_banner"],
    }
