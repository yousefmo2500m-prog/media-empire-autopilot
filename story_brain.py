# -*- coding: utf-8 -*-
"""
مؤلف قصص رد الاعتبار والمواقف الذكية الفيروسية V3.0 (Viral Clever Karma Story Brain)
يكتب قصص يومية سريعة وممتعة جداً بنفس تركيبة «الست الكبيرة وموظف البنك»:
1) دخول مباشر في الموقف من أول ثانية بدون أي مقدمات ("النهارده كنت واقفة في طابور...").
2) شخص متكبر أو مستفز بيعامل شخص طيب أو بسيط باستعلاء.
3) الشخص البسيط مبيتعصبش خالص — بيفكر بهدوء ويعمل حركة قانونية/ذكية عبقرية تقلب الترابيزة 180 درجة وتفرّح قلب المستمع!
4) حكمة سريعة من جملة واحدة في الآخر تخلي المتابعين يعملوا لايك وكومنت ومشاركة.
"""

import json
import re
import time
from pathlib import Path
from typing import Any, Dict

import requests

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
        "ch1_eg_karma": {"used_topics": []},
        "ch2_en_karma": {"used_topics": []},
        "ch3_eg_twists": {"used_topics": []},
        "ch4_en_workplace": {"used_topics": []},
    }


def save_memory(memory_path: Path, data: Dict[str, Any]) -> None:
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    memory_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _pick_groq_model(api_key: str) -> str:
    try:
        r = requests.get(f"{GROQ_BASE}/models", headers={"Authorization": f"Bearer {api_key}"}, timeout=15)
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


def generate_karma_story(channel_cfg: Dict[str, Any], api_key: str, memory: Dict[str, Any]) -> Dict[str, Any]:
    cid = channel_cfg["id"]
    used = memory.setdefault(cid, {"used_topics": []}).get("used_topics", [])[-75:]
    stype = channel_cfg["story_type"]

    if stype in ("eg_clever_karma", "eg_smart_twist"):
        sys_prompt = (
            "أنتِ حكّاءة مصرية بارعة بتحكي مواقف واقعية ذكية وممتعة جداً بالعامية المصرية البسيطة السلسة "
            "(بصيغة المتكلمة المؤنثة: «كنت واقفة»، «شفت بعيني»). "
            "ممنوع الفصحى المدرسية نهائياً! القصة بتبدأ فوراً في أول ثانية جوه مكان حقيقي "
            "(بنك، مطعم، طيارة، معرض عربيات، عيادة، سوبر ماركت، شركة، جامعة، فندق)، "
            "وفيها شخص متكبر بيستقل بشخص بسيط أو كبير في السن، فالشخص البسيط بكل هدوء وذكاء خارق بيقلب الترابيزة عليه بحركة عبقرية غير متوقعة! "
            "أخرج JSON صالح فقط."
        )
        usr_prompt = f"""
ممنوع تكرار أي فكرة من الأفكار السابقة: {used}

اكتبي قصة واحدة متصلة ومشوقة جداً من 165 إلى 210 كلمة بالعامية المصرية الطبيعية السريعة (مدتها حوالي 65 إلى 85 ثانية).
أرجعي JSON بالهيكل التالي:
{{
  "topic_key": "ملخص 4 كلمات للموقف لعدم تكراره",
  "youtube_title": "عنوان يوتيوب شورتس ناري بالعامية المصرية يشد الفضول فوراً + #shorts",
  "description": "وصف قصير مشوق للقصة + سؤال للمتابعين لو كنت مكانه هتعمل إيه؟ + هاشتاجات",
  "first_comment": "لو كنت مكان الموظف في اللحظة دي كان هيبقى رد فعلك إيه؟ 😂 اكتب رأيك في التعليقات!",
  "story_text": "النص الكامل للقصة بالعامية المصرية متصل وطبيعي بدون إيموجي وبدون أقواس"
}}
"""
    else:
        focus = (
            "everyday customer/stranger instant karma where a humble person calmly outsmarts an arrogant snob"
            if stype == "en_clever_karma"
            else "workplace malicious compliance where an employee follows a micromanaging boss's absurd rule to the letter with hilarious costly consequences"
        )
        sys_prompt = (
            "You are a viral YouTube Shorts & Reels storyteller specializing in satisfying clever karma stories. "
            "Hook the listener in the very first second ('Yesterday in first class...', 'Last week my new manager...'). "
            "Keep sentences conversational, vivid, punchy, and 100% advertiser-safe (no profanity, no violence, no medical/legal/financial advice). "
            "Output valid JSON only."
        )
        usr_prompt = f"""
Avoid all previously used premises: {used}

Write ONE continuous, deeply satisfying {focus} story (170 to 215 words, ~65-80 seconds spoken).
Return exact JSON:
{{
  "topic_key": "4-word unique summary",
  "youtube_title": "Punchy viral Shorts title with curiosity hook #shorts",
  "description": "Short engaging description + question for viewers + hashtags",
  "first_comment": "What would you have done in their shoes? Drop your thoughts below! 👇",
  "story_text": "Full continuous spoken story text in natural conversational American English, no stage directions, no emojis"
}}
"""

    model = _pick_groq_model(api_key)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    last_err = None
    for attempt in range(3):
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": usr_prompt},
                ],
                "temperature": 0.85,
                "max_tokens": 2500,
                "response_format": {"type": "json_object"},
            }
            resp = requests.post(f"{GROQ_BASE}/chat/completions", headers=headers, json=payload, timeout=60)
            if resp.status_code != 200:
                payload.pop("response_format", None)
                resp = requests.post(f"{GROQ_BASE}/chat/completions", headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            res = _extract_json(resp.json()["choices"][0]["message"]["content"])
            tk = res.get("topic_key", "")
            if tk:
                memory[cid].setdefault("used_topics", []).append(tk)
            return res
        except Exception as exc:
            last_err = exc
            time.sleep(2.0 * (attempt + 1))
    raise RuntimeError(f"فشل توليد القصة من Groq: {last_err}")
