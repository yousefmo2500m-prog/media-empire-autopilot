# -*- coding: utf-8 -*-
"""
العقل القصصي والذاكرة الممتدة لسنتين (2-Year Autonomous Story & Novel Brain)
- يكتشف تلقائياً أفضل موديل نشط على Groq حتى لو تغيّرت أسماء الموديلات خلال السنتين.
- يدير الروايات المتسلسلة بحلقاتها (4 حلقات لكل رواية ثم يبدأ رواية جديدة تلقائياً).
- يحفظ سجل كافة المواضيع والروايات السابقة لمنع التكرار نهائياً على مدار 730+ يوماً.
"""

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from channels_config import CHANNELS

GROQ_BASE = "https://api.groq.com/openai/v1"
PREFERRED_MODELS = [
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b",
    "llama3-70b-8192",
]


def load_memory(memory_path: Path) -> Dict[str, Any]:
    if memory_path.exists():
        try:
            return json.loads(memory_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "ch1_novels": {
            "active_novel": None,
            "completed_novels": [],
            "genre_index": 0,
        },
        "ch2_en_mystery": {"used_topics": []},
        "ch3_ar_history": {"used_topics": []},
        "ch4_riddles": {"used_topics": []},
    }


def save_memory(memory_path: Path, data: Dict[str, Any]) -> None:
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    memory_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _pick_groq_model(api_key: str) -> str:
    try:
        r = requests.get(
            f"{GROQ_BASE}/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        if r.status_code == 200:
            avail = {m["id"] for m in r.json().get("data", [])}
            for cand in PREFERRED_MODELS:
                if cand in avail:
                    return cand
            for m_id in sorted(avail):
                if "whisper" not in m_id and "guard" not in m_id and "tts" not in m_id:
                    return m_id
    except Exception:
        pass
    return PREFERRED_MODELS[0]


def _extract_json(raw: str) -> Dict[str, Any]:
    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, flags=re.DOTALL)
    if fence:
        cleaned = fence.group(1)
    else:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def call_groq_json(system_prompt: str, user_prompt: str, api_key: str) -> Dict[str, Any]:
    model = _pick_groq_model(api_key)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    last_err = None
    for attempt in range(3):
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.82,
                "max_tokens": 4500,
                "response_format": {"type": "json_object"},
            }
            resp = requests.post(
                f"{GROQ_BASE}/chat/completions",
                headers=headers,
                json=payload,
                timeout=75,
            )
            if resp.status_code != 200:
                # محاولة بدون response_format في حال تغير خصائص الموديل مستقبلاً
                payload.pop("response_format", None)
                resp = requests.post(
                    f"{GROQ_BASE}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=75,
                )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return _extract_json(content)
        except Exception as exc:
            last_err = exc
            time.sleep(2.5 * (attempt + 1))
    raise RuntimeError(f"فشل توليد السكريبت عبر Groq بعد 3 محاولات: {last_err}")


def generate_novel_episode(
    api_key: str,
    memory: Dict[str, Any],
    mode: str = "full",
) -> Dict[str, Any]:
    """
    توليد حلقة جديدة من مسرح الروايات الصوتية بتعدد الشخصيات والمشاهد البصرية.
    mode='full' -> حلقة يوتيوب رئيسية متعمقة (16-22 سطراً درامياً عبر 6 مشاهد)
    mode='short' -> حلقة تشويقية سريعة (8-10 أسطر عبر 4 مشاهد، مثالية لـ 60-75 ثانية)
    """
    ch_mem = memory.setdefault("ch1_novels", {"active_novel": None, "completed_novels": [], "genre_index": 0})
    active = ch_mem.get("active_novel")
    completed_titles = ch_mem.get("completed_novels", [])[-40:]
    genres = CHANNELS["ch1_novels"]["genres_rotation"]

    if not active:
        genre = genres[ch_mem.get("genre_index", 0) % len(genres)]
        ep_num = 1
        total_eps = 4
        novel_context = (
            f"هذه هي الحلقة رقم 1 (البداية الغامضة) من رواية جديدة كلياً من أصل {total_eps} حلقات.\n"
            f"نوع الرواية المطلوب: {genre}.\n"
            f"تجنب تماماً هذه العناوين السابقة: {completed_titles}."
        )
    else:
        ep_num = int(active["next_episode"])
        total_eps = int(active.get("total_episodes", 4))
        is_finale = ep_num >= total_eps
        novel_context = (
            f"نحن نكمل رواية قائمة بعنوان: «{active['novel_title']}» ({active['genre']}).\n"
            f"هذه هي الحلقة رقم {ep_num} من أصل {total_eps}"
            f"{' — وهي الحلقة الأخيرة الحاسمة لكشف السر الكبير وإغلاق كافة الخيوط!' if is_finale else ' — صعّد الأحداث واختم بمفاجأة تشويقية (Cliffhanger) للحلقة القادمة!'}\n"
            f"الشخصيات المعتمدة في الرواية: {json.dumps(active.get('characters', {}), ensure_ascii=False)}\n"
            f"ملخص ما حدث في الحلقات السابقة: {active.get('story_so_far', '')}"
        )

    lines_target = "8 إلى 10 مقاطع حوارية وسردية مكثفة ومشوقة جداً عبر 4 مشاهد" if mode == "short" else "18 إلى 22 مقطعاً سردياً وحوارياً متقناً عبر 6 مشاهد سينمائية"

    sys_prompt = (
        "أنت روائي عربي محترف وكاتب دراما إذاعية وسينمائية من الطراز الرفيع. "
        "تكتب بلغة عربية فصحى درامية سلسة وساحرة تخطف أنفاس المستمع من أول ثانية، "
        "وتلتزم تماماً بسياسات إعلانات يوتيوب (بدون دماء أو عنف صريح أو سياسة أو طب أو فتاوى مالية). "
        "أخرج النتيجة بصيغة JSON صالحة فقط."
    )

    usr_prompt = f"""
{novel_context}

المطلوب كتابة نص تمثيلي متكامل يحتوي على {lines_target}.
استخدم الأدوار الصوتية التالية حصراً في حقل `speaker`:
- `narrator` (الراوي الرئيسي لوصف الأجواء والمشاعر)
- `male_lead` (بطل الرواية الشاب)
- `detective` (المحقق أو الشخصية الغامضة الوقورة)
- `female_lead` (البطلة أو الشاهدة الرئيسية)

أرجع كائن JSON واحد بالهيكل الدقيق التالي:
{{
  "novel_title": "اسم الرواية الجذاب",
  "episode_number": {ep_num},
  "total_episodes": {total_eps},
  "episode_title": "عنوان هذه الحلقة",
  "youtube_title": "عنوان يوتيوب فائق الجاذبية لا يتجاوز 85 حرفاً يتضمن اسم الرواية ورقم الحلقة",
  "description": "وصف تشويقي للحلقة مع سؤال تفاعلي للجمهور في النهاية",
  "first_comment": "تعليق مثبت تفاعلي يسأل المتابعين عن توقعهم لسر الحلقة القادمة ويدعوهم للاشتراك",
  "thumbnail_headline": "3 أو 4 كلمات عربية نارية للصورة المصغرة فقط",
  "characters": {{
    "male_lead": "اسم البطل في الرواية",
    "detective": "اسم المحقق أو الرجل الغامض",
    "female_lead": "اسم البطلة"
  }},
  "updated_story_so_far": "ملخص دقيق من 4 جمل لكل ما حدث حتى نهاية هذه الحلقة لحفظه في ذاكرة الحلقات القادمة",
  "scenes": [
    {{
      "scene_id": 1,
      "visual_prompt_en": "Detailed cinematic English prompt for dark atmospheric illustration, dramatic lighting, moody shadows, NO text, NO letters, NO watermark, photorealistic cinema art",
      "location_caption": "المكان والزمان باختصار (مثال: قصر الزمالك القديم — منتصف الليل)"
    }}
  ],
  "segments": [
    {{
      "scene_id": 1,
      "speaker": "narrator",
      "speaker_name": "🎙️ الراوي",
      "text": "النص العربي المشكّل جزئياً عند اللزوم بوضوح وسلاسة درامية (من 12 إلى 26 كلمة في السطر الواحد)"
    }}
  ]
}}
"""
    result = call_groq_json(sys_prompt, usr_prompt, api_key)

    # تحديث ذاكرة الروايات المتسلسلة تلقائياً
    if ep_num >= total_eps:
        ch_mem.setdefault("completed_novels", []).append(result.get("novel_title", ""))
        ch_mem["active_novel"] = None
        ch_mem["genre_index"] = ch_mem.get("genre_index", 0) + 1
    else:
        ch_mem["active_novel"] = {
            "novel_title": result.get("novel_title", "رواية الليل"),
            "genre": active["genre"] if active else genres[ch_mem.get("genre_index", 0) % len(genres)],
            "total_episodes": total_eps,
            "next_episode": ep_num + 1,
            "characters": result.get("characters", {}),
            "story_so_far": result.get("updated_story_so_far", ""),
        }
    return result


def generate_documentary_or_riddle(
    channel_id: str,
    api_key: str,
    memory: Dict[str, Any],
) -> Dict[str, Any]:
    """توليد حلقة أصلية لقناة الغموض الإنجليزية، أو وثائقيات التاريخ العربية، أو ألغاز المحقق."""
    ch_cfg = CHANNELS[channel_id]
    used = memory.setdefault(channel_id, {"used_topics": []}).get("used_topics", [])[-60:]

    if channel_id == "ch2_en_mystery":
        sys_prompt = (
            "You are an Emmy-caliber documentary scriptwriter for a high-RPM US/UK science & history mystery channel. "
            "Never cover medical, financial, legal, or political advice (strictly comply with YouTube July 2026 monetization guidelines). "
            "Focus on astonishing real scientific anomalies, vanished historical expeditions, deep-ocean signals, or astronomical paradoxes. "
            "Output valid JSON only."
        )
        usr_prompt = f"""
Avoid all previously covered topics: {used}

Create a gripping 60-75 second multi-scene English documentary script (8-10 segments across 4 atmospheric scenes).
Allowed `speaker` keys: `narrator` (main host) and `quote` (historical log / scientist quote).

Return exact JSON:
{{
  "topic_key": "short unique topic identifier",
  "episode_title": "Gripping Documentary Title",
  "youtube_title": "High-CTR YouTube Title under 85 chars",
  "description": "Compelling English description with curiosity question + hashtags",
  "first_comment": "Engaging pinned question asking viewers their theory on this anomaly",
  "thumbnail_headline": "3-4 PUNCHY WORDS",
  "scenes": [
    {{
      "scene_id": 1,
      "visual_prompt_en": "Cinematic photorealistic documentary scene, atmospheric lighting, NO text, NO letters, NO words",
      "location_caption": "NORTH ATLANTIC — 1928 ARCHIVE"
    }}
  ],
  "segments": [
    {{
      "scene_id": 1,
      "speaker": "narrator",
      "speaker_name": "🎙️ ARCHIVE HOST",
      "text": "Punchy, vivid spoken English sentence (14-24 words)."
    }}
  ]
}}
"""
    elif channel_id == "ch3_ar_history":
        sys_prompt = (
            "أنت كاتب وثائقيات تاريخية وجغرافية محترف بأسلوب مشوّق يستهدف الجمهور العربي والخليجي والمصري. "
            "تتحدث عن أسرار الحضارات، المدن المفقودة، الخرائط العجيبة، والابتكارات التاريخية المذهلة الموثقة بدون أي سياسة معاصرة أو فتاوى. "
            "أخرج JSON صالحاً فقط."
        )
        usr_prompt = f"""
تجنب تماماً هذه المواضيع السابقة: {used}

اكتب حلقة وثائقية مشوقة (8-10 مقاطع عبر 4 مشاهد بصرية فخمة).
الأدوار المسموحة في `speaker`: `narrator` (الراوي الوثائقي) و `quote` (اقتباس رحالة أو وثيقة تاريخية).

أرجع JSON بالهيكل التالي:
{{
  "topic_key": "معرف مختصر للموضوع",
  "episode_title": "عنوان الحلقة الوثائقية",
  "youtube_title": "عنوان يوتيوب جذاب أقل من 85 حرفاً",
  "description": "وصف وثائقي مشوق مع سؤال للمتابعين وهاشتاجات",
  "first_comment": "سؤال تفاعلي مثبت في أول تعليق يفتح نقاشاً شيقاً بين المتابعين",
  "thumbnail_headline": "3 أو 4 كلمات قوية",
  "scenes": [
    {{
      "scene_id": 1,
      "visual_prompt_en": "Epic historical cinematic painting style, golden hour lighting, ancient architecture or map room, NO text, NO letters",
      "location_caption": "مكتبة بغداد الكبرى — القرن التاسع"
    }}
  ],
  "segments": [
    {{
      "scene_id": 1,
      "speaker": "narrator",
      "speaker_name": "🗺️ السجل التاريخي",
      "text": "جملة وثائقية عربية فصيحة وسلسة تخطف الانتباه (13 إلى 24 كلمة)."
    }}
  ]
}}
"""
    else:  # ch4_riddles
        sys_prompt = (
            "أنت مؤلف ألغاز بوليسية وتحديات ذكاء تفاعلية فائقة الذكاء مصممة لتفجير التعليقات على فيسبوك ويوتيوب. "
            "تضع لغز تحقيق ذكي يحتوي على تناقض خفي واحد في أقوال المشتبه بهم، ولا تكشف الحل في الفيديو بل تتحدى المشاهدين لكتابته في التعليقات! "
            "أخرج JSON صالحاً فقط."
        )
        usr_prompt = f"""
تجنب تماماً هذه الألغاز السابقة: {used}

اكتب حلقة لغز تحقيق تفاعلي مدتها حوالي 60 ثانية (7-9 مقاطع عبر 4 مشاهد).
الأدوار المسموحة في `speaker`: `narrator` (المحقق الذي يعرض القضية ويتحدى الجمهور) و `witness` (شهادة المشتبه به التي تحوي التناقض الذكي).
مهم جداً: لا تذكر الحل النهائي في المقاطع حتى يكتب المتابعون الحل في التعليقات!

أرجع JSON بالهيكل التالي:
{{
  "topic_key": "معرف مختصر للغز",
  "episode_title": "عنوان القضية الغامضة",
  "youtube_title": "لغز عبقري 97% يخطئون فيه: عنوان مشوق أقل من 85 حرفاً",
  "description": "وصف مشوق يطلب كتابة الخيط المفقود في التعليقات",
  "first_comment": "اكتب رقم المشتبه به والتناقض اللي كشفه في رد تحت التعليق ده 👇 أذكى إجابة هيتم تثبيتها!",
  "thumbnail_headline": "من يكذب فيهم؟ 97% يفشلون!",
  "scenes": [
    {{
      "scene_id": 1,
      "visual_prompt_en": "Moody detective investigation room, clues on wooden desk, warm lamp light, rain outside window, NO text, NO letters",
      "location_caption": "ملف القضية #409 — غرفة التحقيق"
    }}
  ],
  "segments": [
    {{
      "scene_id": 1,
      "speaker": "narrator",
      "speaker_name": "🕵️ ملف القضية",
      "text": "جملة عربية سلسة ومشوقة تعرض تفاصيل اللغز بوضوح (12 إلى 22 كلمة)."
    }}
  ]
}}
"""

    result = call_groq_json(sys_prompt, usr_prompt, api_key)
    topic_key = result.get("topic_key") or result.get("episode_title", "")
    if topic_key:
        memory[channel_id].setdefault("used_topics", []).append(topic_key)
    return result
