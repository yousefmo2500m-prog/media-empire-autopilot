# -*- coding: utf-8 -*-
"""
العقل الروائي السينمائي V2.0 (Binge-Worthy Netflix / Podcast Storytelling Brain)
- يكتب بالعامية المصرية الروائية الممتعة (أسلوب «ما وراء الطبيعة» و«أحمد يونس» و«سامح سند») — ممنوع نهائياً الفصحى المدرسية!
- يولّد لكل جملة لقطة سينمائية مستقلة بكاميرا 35mm (Close-Up / POV / Wide) + مؤثر صوتي تمثيلي متزامن (خبط باب، نبض قلب، كاسيت، رعد).
- يدير الروايات المتسلسلة (4 حلقات لكل رواية ثم رواية جديدة تلقائياً) ويحفظ الذاكرة لمدة سنتين بدون تكرار.
"""

import json
import re
import time
from pathlib import Path
from typing import Any, Dict

import requests

from channels_config import CHANNELS

GROQ_BASE = "https://api.groq.com/openai/v1"
PREFERRED_MODELS = [
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
]


def load_memory(memory_path: Path) -> Dict[str, Any]:
    if memory_path.exists():
        try:
            return json.loads(memory_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "ch1_novels": {"active_novel": None, "completed_novels": [], "genre_index": 0},
        "ch2_en_mystery": {"used_topics": []},
        "ch3_ar_history": {"used_topics": []},
        "ch4_riddles": {"used_topics": []},
    }


def save_memory(memory_path: Path, data: Dict[str, Any]) -> None:
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    memory_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


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
    except Exception:
        pass
    return PREFERRED_MODELS[0]


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


def call_groq_json(system_prompt: str, user_prompt: str, api_key: str) -> Dict[str, Any]:
    model = _pick_groq_model(api_key)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    last_err = None
    for attempt in range(3):
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.85,
                "max_tokens": 5000,
                "response_format": {"type": "json_object"},
            }
            resp = requests.post(f"{GROQ_BASE}/chat/completions", headers=headers, json=payload, timeout=75)
            if resp.status_code != 200:
                payload.pop("response_format", None)
                resp = requests.post(f"{GROQ_BASE}/chat/completions", headers=headers, json=payload, timeout=75)
            resp.raise_for_status()
            return _extract_json(resp.json()["choices"][0]["message"]["content"])
        except Exception as exc:
            last_err = exc
            time.sleep(2.0 * (attempt + 1))
    raise RuntimeError(f"فشل توليد القصة من Groq: {last_err}")


def generate_novel_episode(api_key: str, memory: Dict[str, Any], mode: str = "full") -> Dict[str, Any]:
    ch_mem = memory.setdefault("ch1_novels", {"active_novel": None, "completed_novels": [], "genre_index": 0})
    active = ch_mem.get("active_novel")
    completed = ch_mem.get("completed_novels", [])[-40:]
    genres = CHANNELS["ch1_novels"]["genres_rotation"]

    if not active:
        genre = genres[ch_mem.get("genre_index", 0) % len(genres)]
        ep_num, total_eps = 1, 4
        arc_note = (
            f"دي الحلقة رقم 1 من 4 من رواية مصرية جديدة تماماً في عالم: ({genre}). "
            f"ابدأ فوراً بلحظة غامضة تحبس الأنفاس من أول ثانية بدون مقدمات، واختم الحلقة بمفاجأة صادمة تخلي المستمع ميقدرش يستنى الحلقة الجاية! "
            f"ممنوع تكرار العناوين دي: {completed}"
        )
    else:
        ep_num = int(active["next_episode"])
        total_eps = int(active.get("total_episodes", 4))
        finale = ep_num >= total_eps
        arc_note = (
            f"بنكمل رواية «{active['novel_title']}» — الحلقة {ep_num} من {total_eps}. "
            f"{'دي الحلقة الأخيرة: اكشف السر الكبير بذكاء ومفاجأة غير متوقعة واقفل القصة بنهاية عبقرية!' if finale else 'صعّد التوتر واكشف خيط جديد واختم بـ Cliffhanger ناري!'} "
            f"ملخص اللي فات: {active.get('story_so_far', '')}"
        )

    seg_count = "8 إلى 9 لقطات سينمائية متلاحقة ومكثفة جداً" if mode == "short" else "16 إلى 20 لقطة سينمائية متلاحقة"

    sys_prompt = (
        "أنت أعظم حكّاء وروائي غموض وإثارة في مصر (بأسلوب مسلسل ما وراء الطبيعة وحكايات أحمد يونس وسامح سند). "
        "قانون صارم جداً: اكتب بالعامية المصرية الطبيعية السلسة الممتعة اللي بنحكي بيها بالليل — "
        "ممنوع منعاً باتاً الفصحى المدرسية، وممنوع التنوين أو التشكيل المدرسي، وممنوع الجمل الإنشائية المملة! "
        "خلّي المستمع يحس إنه لابس سماعة وعايش جوه فيلم نتفليكس مصري مليان تشويق. أخرج JSON فقط."
    )

    usr_prompt = f"""
{arc_note}

اكتب الحلقة مكونة من {seg_count}.
مهم جداً: كل عنصر في `segments` له لقطة كاميرا سينمائية مستقلة خاصة به (`shot_prompt_en`) عشان المشاهد البصرية تتغير كل 5 ثواني زي الأفلام الحقيقية!

الأصوات المتاحة في `speaker`:
- `narrator`: الحكّاء المصري الرئيسي (بيحكي بضمير المتكلم كأنه بطل الحكاية اللي عاشها بنفسه!)
- `mystery_man`: صوت راجل غامض أو تسجيل شريط كاسيت أو مكالمة نص الليل
- `female_lead`: صوت بنت مصرية في القصة (صاحبة السر أو الشاهدة)

المؤثرات الصوتية المتاحة في `sfx` (ضعها في اللحظة المناسبة فقط وإلا اكتب `none`):
`knock` (خبط على باب بالليل)، `heartbeat` (نبضات قلب مرعوبة)، `thunder` (رعد ومطر)، `cassette` (تشغيل شريط كاسيت/تسجيل)، `reveal` (صدمة كشف مفاجأة).

أرجع JSON بالهيكل الدقيق التالي:
{{
  "novel_title": "اسم مصري مشوق للرواية (مثال: شريط الأوضة التالتة)",
  "episode_number": {ep_num},
  "total_episodes": {total_eps},
  "episode_title": "عنوان الحلقة بالعامية المشوقة",
  "youtube_title": "عنوان يوتيوب ناري يشد أي حد يدوس فوراً (أقل من 85 حرف)",
  "description": "وصف مشوق بالعامية المصرية + سؤال للمتابعين في الآخر",
  "first_comment": "سؤال تفاعلي بالعامية للمتابعين: تفتكروا مين اللي ساب الرسالة؟ اكتبوا توقعكم للحلقة الجاية 👇",
  "thumbnail_headline": "3 كلمات مصرية صادمة للصورة المصغرة",
  "updated_story_so_far": "ملخص 4 سطور للأحداث عشان ذاكرة الحلقة الجاية",
  "segments": [
    {{
      "speaker": "narrator",
      "sfx": "knock",
      "rain_fx": true,
      "camera_move": "push_in",
      "shot_prompt_en": "Photorealistic 35mm Netflix thriller film still, extreme close up of antique brass apartment door handle and peephole at 3 AM in old Cairo hallway, warm moody tungsten shadow, shallow depth of field, cinematic grain, no text",
      "text": "الساعة تلاتة وتلت الفجر بالظبط، صحيت مفزوع على تلات خبطات هاديين أوي على باب شقتي، مع إن العمارة كلها فاضية وباب الحديد تحت مقفول بالجنازير."
    }}
  ]
}}
"""
    res = call_groq_json(sys_prompt, usr_prompt, api_key)

    if ep_num >= total_eps:
        ch_mem.setdefault("completed_novels", []).append(res.get("novel_title", ""))
        ch_mem["active_novel"] = None
        ch_mem["genre_index"] = ch_mem.get("genre_index", 0) + 1
    else:
        ch_mem["active_novel"] = {
            "novel_title": res.get("novel_title", "شريط نص الليل"),
            "genre": active["genre"] if active else genres[ch_mem.get("genre_index", 0) % len(genres)],
            "total_episodes": total_eps,
            "next_episode": ep_num + 1,
            "story_so_far": res.get("updated_story_so_far", ""),
        }
    return res


def generate_documentary_or_riddle(channel_id: str, api_key: str, memory: Dict[str, Any]) -> Dict[str, Any]:
    used = memory.setdefault(channel_id, {"used_topics": []}).get("used_topics", [])[-60:]

    if channel_id == "ch2_en_mystery":
        sys_prompt = (
            "You are a master late-night mystery storyteller like MrBallen and Lemmino. "
            "Write conversational, goosebump-inducing spoken English — NO textbook tone! "
            "Start with an instant hook in second 1. Never give medical, financial, legal, or political advice. Output JSON only."
        )
        usr_prompt = f"""
Avoid previous topics: {used}
Write an 8-shot gripping true mystery story (60-75 seconds). Every segment MUST have its own distinct 35mm cinematic `shot_prompt_en`.
Speakers: `narrator` or `witness`. SFX options: `knock`, `heartbeat`, `thunder`, `cassette`, `reveal`, `none`.
Return JSON:
{{
  "topic_key": "short id",
  "episode_title": "Title",
  "youtube_title": "Viral MrBallen-style YouTube title under 85 chars",
  "description": "Gripping description + hashtags",
  "first_comment": "Pinned question asking viewers their theory",
  "thumbnail_headline": "3 SHOCKING WORDS",
  "segments": [
    {{
      "speaker": "narrator",
      "sfx": "thunder",
      "rain_fx": true,
      "camera_move": "push_in",
      "shot_prompt_en": "35mm Netflix documentary film still, isolated lighthouse in stormy North Atlantic night, beam cutting through fog, photorealistic, no text",
      "text": "In December 1900, a supply ship arrived at a remote Scottish island, only to find all three lighthouse keepers had vanished mid-meal."
    }}
  ]
}}
"""
    elif channel_id == "ch3_ar_history":
        sys_prompt = (
            "أنت حكّاء مصري ممتع جداً بتحكي أغرب القصص والأسرار الحقيقية في التاريخ بالعامية المصرية الذكية الشائقة (زي الدحيح وسامح سند) — "
            "ممنوع الفصحى المدرسية المملة! ادخل في القصة الصادمة من أول ثانية. أخرج JSON فقط."
        )
        usr_prompt = f"""
تجنب المواضيع دي: {used}
اكتب حكاية تاريخية حقيقية مذهلة في 8 لقطات سينمائية متلاحقة، كل جملة ليها `shot_prompt_en` سينمائي واقعي خاص بيها.
الأصوات: `narrator` أو `witness`. المؤثرات: `knock`, `heartbeat`, `thunder`, `reveal`, `none`.
أرجع JSON:
{{
  "topic_key": "معرف",
  "episode_title": "عنوان الحكاية",
  "youtube_title": "عنوان يوتيوب يخطف العين بالعامية الذكية",
  "description": "وصف مشوق + هاشتاجات",
  "first_comment": "سؤال تفاعلي في أول تعليق",
  "thumbnail_headline": "3 كلمات نارية",
  "segments": [
    {{
      "speaker": "narrator",
      "sfx": "reveal",
      "rain_fx": false,
      "camera_move": "pan_right",
      "shot_prompt_en": "35mm epic cinema film still, secret underground torchlit chamber beneath ancient stone palace, dust particles in golden light, photorealistic, no text",
      "text": "تخيل تشتري بيت قديم وتيجي تهد حيطة في البدروم بالصدفة، فتلاقي وراها مدينة كاملة تحت الأرض كانت مستخبية بقالها ألفين سنة!"
    }}
  ]
}}
"""
    else:  # ch4_riddles
        sys_prompt = (
            "أنت صانع ألغاز جرائم وتحقيقات تفاعلية بالعامية المصرية المشوقة. "
            "احكِ جريمة ذكية في 60 ثانية فيها 3 مشتبه فيهم وغلطة واحدة كشفت الكداب، ومتقولش الحل أبداً عشان المتابعين يتحدوا بعض في الكومنتات! أخرج JSON فقط."
        )
        usr_prompt = f"""
تجنب الألغاز دي: {used}
اكتب قضية تحقيق تفاعلية من 8 لقطات سينمائية بالعامية المصرية السريعة الممتعة.
الأصوات: `narrator`، `suspect_m`، `suspect_f`. المؤثرات: `knock`, `heartbeat`, `thunder`, `reveal`, `none`.
أرجع JSON:
{{
  "topic_key": "معرف",
  "episode_title": "عنوان القضية",
  "youtube_title": "لغز جريمة 98% بيغلطوا فيه: مين الكداب؟",
  "description": "ركّز في كلام التلاتة واكتب مين المجرم في التعليقات!",
  "first_comment": "ها عرفت مين الكداب والغلطة اللي وقع فيها؟ اكتب تحليلك هنا وأذكى تعليق هيتثبت 👇🕵️",
  "thumbnail_headline": "غلطة واحدة كشفته!",
  "segments": [
    {{
      "speaker": "narrator",
      "sfx": "thunder",
      "rain_fx": true,
      "camera_move": "push_in",
      "shot_prompt_en": "35mm noir detective film still, luxury study room at night, broken vintage clock on carpet showing 2:15, rain on window, photorealistic, no text",
      "text": "الساعة اتنين وربع بالليل الكهربا قطعت في الفيلا كلها، ولما النور رجع كانت الخزنة مفتوحة، والتلاتة اللي في البيت كل واحد قال حجة أغرب من التاني!"
    }}
  ]
}}
"""
    res = call_groq_json(sys_prompt, usr_prompt, api_key)
    tk = res.get("topic_key") or res.get("episode_title", "")
    if tk:
        memory[channel_id].setdefault("used_topics", []).append(tk)
    return res
