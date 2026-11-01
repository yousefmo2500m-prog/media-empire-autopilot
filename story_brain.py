# -*- coding: utf-8 -*-
"""
مؤلف الحلقات الدرامية الطويلة (15–17 دقيقة) + الشورتس التشويقية V4.0
يبني كل حلقة على 5 فصول متصاعدة التوتر (5 Escalating Acts) مع الترابط الكامل للشخصيات والأحداث:
- إجمالي الكلمات: 2,200 إلى 2,650 كلمة متصلة ومشوقة بدون حشو ممل (تضمن مدة 15.5 إلى 17 دقيقة).
- يولّد معها 8 أوصاف مشاهد سينمائية دقيقة (Scene Visual Prompts) تعبّر عما يحدث في القصة أمام عين المشاهد.
- يقتطع أو يصيغ الجزء الحماسي الأكثر تشويقاً (Cliffhanger Teaser ~50-60s) ليُنشر على YouTube Shorts و TikTok
  مع توجيه المشاهد صراحةً لفتح الفيديو الكامل من الرابط في أول تعليق!
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
    return {k: {"used_topics": []} for k in ("ch1_eg_karma", "ch2_eg_mystery", "ch3_en_karma", "ch4_en_mystery")}


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


def _groq_json(api_key: str, model: str, sys_prompt: str, usr_prompt: str, max_tokens: int = 4500) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    candidates = [model] + [m for m in PREFERRED_MODELS if m != model]
    last_err = None
    for attempt in range(9):
        cur_model = candidates[attempt % len(candidates)]
        try:
            payload = {
                "model": cur_model,
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": usr_prompt},
                ],
                "temperature": 0.82,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            }
            resp = requests.post(f"{GROQ_BASE}/chat/completions", headers=headers, json=payload, timeout=90)
            if resp.status_code == 429:
                wait_s = min(15.0, float(resp.headers.get("retry-after", 4.0)))
                time.sleep(wait_s)
                continue
            if resp.status_code != 200:
                payload.pop("response_format", None)
                resp = requests.post(f"{GROQ_BASE}/chat/completions", headers=headers, json=payload, timeout=90)
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
    forced_premise: str = "",
) -> Dict[str, Any]:
    """
    يبني مخطط الحلقة الكامل (5 فصول + 8 مشاهد بصرية + نص الشورت التشويقي)،
    ثم يكتب كل فصل بعمق روائي مشوق (450–550 كلمة لكل فصل = ~2,400+ كلمة إجمالاً) لضمان تجاوز 15 دقيقة بسهولة.
    """
    cid = channel_cfg["id"]
    used = memory.setdefault(cid, {"used_topics": []}).get("used_topics", [])[-60:]
    lang = channel_cfg["language"]
    niche = channel_cfg["niche"]
    model = _pick_groq_model(api_key)

    if lang == "ar":
        style_guide = (
            "أنتِ حكّاءة مصرية محترفة ومحبوبة جداً بتحكي قصص طويلة ومشوقة بالعامية المصرية الطبيعية السلسة الدافئة "
            "(بصيغة الراوية المؤنثة: «تعالوا أحكيلكم»، «شفتوا اللي حصل»، بدون أي فصحى مدرسية معقدة نهائياً!). "
            "القصة لازم تكون آمنة 100% لإعلانات يوتيوب وفيسبوك (بدون دموية أو عنف، بل ذكاء وتشويق وإنسانيات)."
        )
        niche_desc = (
            "قصة اجتماعية وإنسانية واقعية طويلة عن شخص مجتهد أو بسيط اتعرض لظلم وتكبر وطمع، "
            "فخطط بهدوء وصبر وذكاء قانوني خارق لحد ما قلب الترابيزة قدام الكل واسترد حقه مضاعف."
            if niche == "eg_social_karma"
            else "قصة لغز وتحقيق ذكي محيّر جداً (سرقة مستحيلة أو خدعة محكمة أو اختفاء محيّر بدون أي عنف دموي) "
                 "وإزاي المحقق الذكي كشف الخيوط خطوة بخطوة من تفصيلة صغيرة محدش انتبه ليها."
        )
        blueprint_prompt = f"""
الأفكار المستعملة سابقاً (ممنوع تكرارها): {used}
{f"الفكرة المطلوبة لهذه الحلقة تحديداً: {forced_premise}" if forced_premise else ""}

صمّمي مخطط حلقة كاملة مدتها 16 دقيقة من نوع: {niche_desc}
أخرجي JSON صالح بالهيكل التالي بالضبط:
{{
  "topic_key": "ملخص 5 كلمات للفكرة",
  "youtube_title": "عنوان يوتيوب طويل ناري بالعامية المصرية يشد الفضول لأقصى درجة",
  "short_title": "عنوان قصير ناري للشورتس والتيك توك + #shorts #حكايات",
  "description": "وصف مشوق للحلقة على يوتيوب وفيسبوك مع هاشتاجات",
  "acts_outline": [
    {{"act_num": 1, "act_title": "عنوان الفصل الأول", "summary": "ملخص تفصيلي لأحداث الفصل الأول والمواجهة الأولى"}},
    {{"act_num": 2, "act_title": "عنوان الفصل الثاني", "summary": "ملخص تفصيلي للخلفية السرية وبداية الخطة أو التحقيق"}},
    {{"act_num": 3, "act_title": "عنوان الفصل الثالث", "summary": "ملخص تفصيلي لتصاعد الأحداث وتعقيد الموقف"}},
    {{"act_num": 4, "act_title": "عنوان الفصل الرابع", "summary": "ملخص تفصيلي للحظة المواجهة الكبرى وكشف الحقيقة الصادمة"}},
    {{"act_num": 5, "act_title": "عنوان الفصل الخامس", "summary": "ملخص تفصيلي للنهاية الشافية والجزاء العادل والعبرة"}}
  ],
  "scene_prompts": [
    "Detailed English cinematic photorealistic film-still prompt for Scene 1 (no text in image, vivid faces, lighting, setting)",
    "Detailed English cinematic photorealistic film-still prompt for Scene 2",
    "Detailed English cinematic photorealistic film-still prompt for Scene 3",
    "Detailed English cinematic photorealistic film-still prompt for Scene 4",
    "Detailed English cinematic photorealistic film-still prompt for Scene 5",
    "Detailed English cinematic photorealistic film-still prompt for Scene 6",
    "Detailed English cinematic photorealistic film-still prompt for Scene 7",
    "Detailed English cinematic photorealistic film-still prompt for Scene 8"
  ],
  "cliffhanger_short_body": "نص حماسي سريع جداً بالعامية المصرية (حوالي 110 إلى 130 كلمة فقط) يحكي أقوى جزء مشوق من بداية القصة ويقف فجأة عند أخطر لحظة قبل كشف السر مباشرة بدون حرق النهاية!"
}}
"""
    else:
        style_guide = (
            "You are a master American long-form YouTube storyteller (in the gripping, vivid narrative style of MrBallen and top Karma story channels). "
            "Your storytelling is conversational, deeply immersive, rich in dialogue and concrete sensory details, and 100% advertiser-safe."
        )
        niche_desc = (
            "a deep, multi-twist family/business/inheritance betrayal & brilliant legal/financial karma story where quiet preparation leads to an unforgettable public reckoning"
            if niche == "en_deep_karma"
            else "a baffling, edge-of-your-seat true-style mystery & mastermind investigation unraveled clue by clue through brilliant deduction (zero gore, pure suspense)"
        )
        blueprint_prompt = f"""
Previously used premises (do NOT repeat): {used}
{f"Required episode premise: {forced_premise}" if forced_premise else ""}

Design a complete 16-minute 5-Act episode outline for: {niche_desc}.
Return exact valid JSON:
{{
  "topic_key": "5-word summary",
  "youtube_title": "High-CTR curiosity-driven YouTube long-form title",
  "short_title": "Viral hook title for Shorts & TikTok #shorts #storytime",
  "description": "Engaging YouTube/Facebook description + hashtags",
  "acts_outline": [
    {{"act_num": 1, "act_title": "Act 1 Title", "summary": "Detailed plot beats for Act 1"}},
    {{"act_num": 2, "act_title": "Act 2 Title", "summary": "Detailed plot beats for Act 2"}},
    {{"act_num": 3, "act_title": "Act 3 Title", "summary": "Detailed plot beats for Act 3"}},
    {{"act_num": 4, "act_title": "Act 4 Title", "summary": "Detailed plot beats for Act 4 (The Big Reveal)"}},
    {{"act_num": 5, "act_title": "Act 5 Title", "summary": "Detailed plot beats for Act 5 (Full Aftermath)"}}
  ],
  "scene_prompts": [
    "Detailed cinematic 16:9 photorealistic movie-still prompt for Scene 1 (vivid expressions, environment, dramatic lighting, no text)",
    "Detailed cinematic 16:9 photorealistic movie-still prompt for Scene 2",
    "Detailed cinematic 16:9 photorealistic movie-still prompt for Scene 3",
    "Detailed cinematic 16:9 photorealistic movie-still prompt for Scene 4",
    "Detailed cinematic 16:9 photorealistic movie-still prompt for Scene 5",
    "Detailed cinematic 16:9 photorealistic movie-still prompt for Scene 6",
    "Detailed cinematic 16:9 photorealistic movie-still prompt for Scene 7",
    "Detailed cinematic 16:9 photorealistic movie-still prompt for Scene 8"
  ],
  "cliffhanger_short_body": "Fast-paced, gripping 120-to-140-word hook telling the opening setup of this exact story and stopping RIGHT at the sharpest cliffhanger moment without spoiling the reveal!"
}}
"""

    plan = _groq_json(api_key, model, style_guide, blueprint_prompt, max_tokens=5000)
    if not plan.get("acts_outline") or len(plan.get("acts_outline", [])) < 5:
        plan = _groq_json(api_key, PREFERRED_MODELS[0], style_guide, blueprint_prompt, max_tokens=5500)

    # كتابة الفصول الخمسة بالتتابع لضمان وصول الحلقة لـ 2,350 - 2,750 كلمة ممتعة ومترابطة (15.5 - 17 دقيقة)
    acts_full: List[Dict[str, Any]] = []
    prev_tail = ""
    for act in plan["acts_outline"]:
        anum = act["act_num"]
        atitle = act["act_title"]
        asum = act["summary"]

        if lang == "ar":
            act_prompt = f"""
عنوان القصة: {plan['youtube_title']}
ملخص كل الفصول للترابط: {json.dumps(plan['acts_outline'], ensure_ascii=False)}
آخر جملتين من الفصل السابق (كمّلي بعدها بسلاسة بدون تكرار): "{prev_tail}"

اكتبي الآن النص الكامل المسموع لـ **الفصل رقم {anum} ({atitle})** بناءً على هذا الملخص: {asum}
الشروط الصارمة:
1. الطول المطلوب لهذا الفصل وحده: **بين 460 و 540 كلمة كاملة** بالعامية المصرية الطبيعية الحلوة الممتعة (بدون فصحى مدرسية وبدون إيموجي أو عناوين جانبية داخل النص).
2. غني بالتفاصيل البصرية والحوارات الطبيعية السريعة والمشاعر اللي تخلي المستمع شايف المشهد قدام عينيه ومشدود لكل ثانية.
3. لو ده الفصل الأول ابدئي فوراً بهوك ناري من أول ثانية، ولو الفصل الخامس اختمي القصة بسؤال تفاعلي للمشاهدين يكتبوا رأيهم في التعليقات.

أرجعي JSON فقط: {{"narration": "النص الكامل المتصل للفصل بالعامية المصرية"}}
"""
        else:
            act_prompt = f"""
Story Title: {plan['youtube_title']}
Full 5-Act Outline: {json.dumps(plan['acts_outline'])}
Last lines of previous act (continue seamlessly without repeating): "{prev_tail}"

Write the full spoken narration for **Act {anum} ({atitle})** covering: {asum}
Strict rules:
1. Length for THIS single act MUST be **between 500 and 580 words** of vivid, gripping conversational American English storytelling (no stage directions, no emojis, no markdown headers inside narration).
2. Include realistic spoken dialogue, micro-details, tension, and pacing so the listener sees every scene playing out in their mind.
3. If Act 1, hook immediately in sentence one. If Act 5, deliver the full satisfying aftermath and end with an engaging question for the comments.

Return JSON only: {{"narration": "Full continuous spoken text for this act"}}
"""
        act_res = _groq_json(api_key, model, style_guide, act_prompt, max_tokens=3200)
        txt = str(act_res.get("narration", "")).strip()
        acts_full.append({
            "act_num": anum,
            "act_title": atitle,
            "narration": txt,
        })
        prev_tail = " ".join(txt.split()[-35:])

    # إذا كان مجموع الكلمات أقل من الهدف المطلوب لـ 15.5 دقيقة، نضيف فقرة تفصيلية غنية للفصل الرابع/الخامس
    total_words = sum(len(a["narration"].split()) for a in acts_full)
    min_words = 2150 if lang == "ar" else 2350
    if total_words < min_words:
        need = min_words - total_words + 180
        if lang == "ar":
            ext_p = (
                f"القصة بعنوان «{plan['youtube_title']}»، ونهاية الفصل الرابع كانت: «{acts_full[3]['narration'][-300:]}». "
                f"اكتبي مشهد إضافي مشوق جداً بالعامية المصرية بطول {need} كلمة يوضح تفاصيل ردود أفعال الحاضرين وكواليس خطة كشف الحقيقة قبل الانتقال للفصل الأخير. "
                f'أرجعي JSON فقط: {{"extra": "النص الإضافي بالعامية المصرية"}}'
            )
        else:
            ext_p = (
                f"In the story '{plan['youtube_title']}', Act 4 ended with: '{acts_full[3]['narration'][-300:]}'. "
                f"Write an additional {need}-word gripping scene expanding the exact reactions in the room and the hidden evidence breakdown right before Act 5. "
                f'Return JSON only: {{"extra": "additional spoken narration"}}'
            )
        ext_res = _groq_json(api_key, model, style_guide, ext_p, max_tokens=2500)
        acts_full[3]["narration"] = acts_full[3]["narration"] + "\n\n" + str(ext_res.get("extra", "")).strip()

    cliff_body = str(plan.get("cliffhanger_short_body") or " ".join(acts_full[0]["narration"].split()[:125])).strip()
    short_full_text = f"{cliff_body} {channel_cfg['cta_spoken']}"

    tk = str(plan.get("topic_key") or plan.get("youtube_title", cid))[:80]
    if tk:
        memory[cid].setdefault("used_topics", []).append(tk)

    return {
        "channel_id": cid,
        "topic_key": tk,
        "youtube_title": plan.get("youtube_title", channel_cfg["brand_name"]),
        "short_title": plan.get("short_title", f"{plan.get('youtube_title', '')[:60]} #shorts"),
        "description": plan.get("description", ""),
        "acts": acts_full,
        "scene_prompts": (plan.get("scene_prompts") or [f"Cinematic 16:9 dramatic film still for {plan.get('youtube_title', '')} scene {i+1}, no text" for i in range(8)])[:8],
        "short_narration": short_full_text,
        "cta_banner": channel_cfg["cta_banner"],
    }
