# -*- coding: utf-8 -*-
"""
العقل النفسي الروائي V9.0 (Neuro-Psychological Retention & 12-Scene 1:1 Storyboard Engine)
مبني على علم النفس السلوكي (Zeigarnik Open Loops + 0-Second Cognitive Dissonance + Escalating Visceral Stakes)
وأساليب أقوى صناع محتوى القصص والتحقيقات عالمياً وعربياً:
1) دخول صادم في أول 0.0 ثانية بتناقض مستحيل يخطف العقل فوراً (ممنوع المقدمات أو القصص العادية الباهتة).
2) تقسيم الحلقة الطويلة (+16 دقيقة) إلى 12 مشهداً متسلسلاً مسمّى، لكل مشهد:
   - عنوان مشهد درامي خاص به (للتقسيم الزمني بالدقيقة والثانية في يوتيوب وداخل الفيديو).
   - نص سردي مشحون بالتوتر النفسي والتفاصيل الحسية والحوارات الطبيعية.
   - وصف بصري سينمائي 16:9 مخصص حصرياً لما يُقال في هذا المشهد بالضبط (صورة واحدة لكل مشهد فقط — صفر تكرار!).
3) تصميم 2 شورتس عميقين (~105–135 ثانية لكل شورت) يغمران المستمع داخل القصة ثم يقطعان فجأة في أعلى لحظة ذروة وإثارة
   (نهاية المشهد 2 للشورت الأول، ونهاية المشهد 7 للشورت الثاني) مع 5 مشاهد رأسية كاملة 9:16 مخصصة لكل شورت بدون أي قص جانبي!
4) تصميم غلاف يوتيوب (Thumbnail 1280x720) فائق الجاذبية بتركيز بصري درامي وعبارة خطّافة قصيرة ترفع نسبة النقر (CTR).
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

# تنوع عوالم القناة الأولى مع الحفاظ 100% على الإثارة النفسية وحبس الأنفاس في كل حلقة (صفر قصص عادية أو باهتة!)
EG_PSYCH_WORLDS = [
    "إثارة نفسية وغموض عائلي صادم: سر مدفون منذ سنوات ينفجر ليلة واحدة بسبب رسالة أو تسجيل أو مفتاح لم يكن مفترضاً أن يراه أحد، وتنقلب فيه الأدوار بين الضحية والمخطط",
    "إثارة نفسية وخطة دهاء بارد: شخص يكتشف بالصدفة أنه واقع داخل لعبة نفسية محكمة دُبرت حوله بصمت في شقته أو عمله، فيبدأ بمجاراة اللعبة لكشف العقل المدبر في مواجهة تحبس الأنفاس",
    "تشويق نفسي وليلة مستحيلة في مكان معزول: سفرية ليلية أو عمارة هادئة أو فندق قديم يحدث فيه تفصيل غير منطقي يتكرر بالدقيقة، وكل محاولة للهرب أو الفهم تفتح سراً أخطر",
    "غموض نفسي وميراث أو أمانة مسمومة: وصية أو صندوق مغلق أو شقة مقفولة منذ عشرين سنة تفرض شرطاً غريباً، ومع تنفيذ الشرط تتكشف حقيقة مرعبة التوتر لا يتوقعها عقل",
    "إثارة نفسية ومفارقة قدرية حادة: مكالمة بالخطأ أو صورة التُقطت في الخلفية عند الساعة الثالثة فجراً تكشف خيطاً خفياً يربط غرباء ببعضهم في مفاجأة مدوية",
]

EG_CONAN_CASES = [
    "قضية الغرفة المغلقة المستحيلة على طريقة المحقق كونان: اختفاء أثر لا يُقدّر بثمن أو وقوع جريمة محيّرة داخل غرفة موصدة من الداخل بالكامل، و4 مشتبه بهم لكل منهم دافع قوي، وتفصيلة فيزيائية عبقرية تفضح الحيلة",
    "قضية حجة الغياب الساعية المستحيلة على طريقة المحقق كونان: المشتبه به الرئيسي ظهر أمام شهود وكاميرات في مكان يبعد ساعة كاملة وقت الحدث بالضبط، وخيط دقيق جداً يكشف الخدعة الزمنية والبصرية",
    "قضية القصر المنعزل أو الباخرة النيلية وسط العاصفة: انقطاع الاتصال، رسائل مشفرة متتالية، 4 أشخاص كل واحد منهم يخفي سراً خطيراً، واستنتاج منطقي صاعق في المواجهة الأخيرة",
    "قضية التبديل المستحيل والخدعة المزدوجة: كل الأدلة المادية تشير لإدانة شخص بريء بنسبة 100%، حتى يلاحظ المحقق تناقضاً واحداً في الإضاءة أو الصوت أو التوقيت يقلب الطاولة بالكامل",
]

EN_PSYCH_WORLDS = [
    "a pulse-pounding MrBallen-style psychological suspense thriller starting with an impossible 3 AM discovery inside an ordinary home that unravels a chilling hidden truth",
    "a high-stakes psychological cat-and-mouse mind-game where the protagonist quietly realizes someone close to them has staged an elaborate deception—and secretly turns the tables",
    "an eerie, claustrophobic night-shift or isolated-location psychological mystery where tiny physical details stop adding up until a jaw-dropping twist reframes every scene",
    "a gripping double-life & buried-secret psychological drama where one accidental photograph, voicemail, or locked drawer pulls the listener down an unforgettable rabbit hole",
]

EN_DETECTIVE_CASES = [
    "a high-tension Detective Conan / Knives Out locked-room mystery with 4 suspects, airtight alibis, fair-play physical clues, and a dazzling final deduction",
    "an impossible clockwork-alibi investigation where timestamped footage proves the culprit was miles away—until one tiny physical contradiction shatters the illusion",
    "an isolated luxury train, cliffside manor, or private vault mystery where every witness lies about one detail and the investigator exposes the master trick step by step",
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


def _groq_json(api_key: str, sys_prompt: str, usr_prompt: str, max_tokens: int = 6000) -> Dict[str, Any]:
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
            resp = requests.post(f"{GROQ_BASE}/chat/completions", headers=headers, json=payload, timeout=110)
            if resp.status_code == 429:
                time.sleep(min(14.0, float(resp.headers.get("retry-after", 4.5))))
                continue
            if resp.status_code != 200:
                payload.pop("response_format", None)
                resp = requests.post(f"{GROQ_BASE}/chat/completions", headers=headers, json=payload, timeout=110)
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
                "أنتِ كاتبة إثارة بوليسية وألغاز نفسية فائقة الذكاء على طريقة «المحقق كونان» وأجاثا كريستي وأشهر صناع محتوى الغموض مثل سامح سند وبيسوهات، "
                "تكتبين بالعامية المصرية القاهرية الطبيعية السلسة 100% بدون أي تشكيل وبدون أي جمل فصحى مدرسية وبدون مقدمات نهائياً. "
                "تطبّقين علم النفس السلوكي لجذب الانتباه: تبدئين في الثانية صفر بتناقض مستحيل يصدم العقل فوراً، وتزرعين في نهاية كل مشهد حلقة فضول مفتوحة "
                "(Zeigarnik Open Loop) تجعل المستمع عاجزاً عن إغلاق الفيديو، مع تفاصيل حسية دقيقة و4 مشتبه بهم وأدلة ذكية واستنتاج نهائي مذهل وآمن إعلانياً 100%."
            )
        else:
            flavor = EG_PSYCH_WORLDS[ep_count % len(EG_PSYCH_WORLDS)]
            style_guide = (
                "أنتِ كاتبة إثارة نفسية وتشويق درامي محترفة تتقنين علم نفس الجذب السمعي (مثل أقوى حلقات الغموض النفسي لـ MrBallen وبيسوهات وسامح سند)، "
                "تكتبين بالعامية المصرية القاهرية الطبيعية الحية 100% بدون أي تشكيل أو فصحى مدرسية وبدون أي مقدمات مثل «النهارده هحكيلكم». "
                "ممنوع تماماً القصص العادية أو الكوميدية البسيطة؛ كل ثانية يجب أن تكون مشحونة بالتوتر النفسي، الغموض، التفاصيل الحسية الدقيقة (صوت خطوات، "
                "توقيت رسالة مستحيل، نظرة مريبة، تفصيلة في صورة)، مع زرع سؤال معلق في نهاية كل مشهد وانقلاب صادم في المنتصف ونهاية عبقرية لا يمكن توقعها."
            )

        blueprint_prompt = f"""
الأفكار المستعملة سابقاً (ممنوع تكرارها أو التشابه معها نهائياً): {used}

صمّمي حلقة إثارة نفسية / تحقيق غامض آسرة لا يستطيع المستمع تركها ثانية واحدة (مدتها 16–18 دقيقة مقسمة إلى 12 مشهداً متسلسلاً) من فئة:
«{flavor}»

قواعد هندسة الجذب النفسي الإلزامية:
1. الجملة الأولى من المشهد 1 لازم تبدأ فوراً في قلب الصدمة أو التناقض المستحيل (مثلاً: توقيت مستحيل، رسالة من شخص لا يمكن أن يرسلها، تفصيلة مرعبة التوتر داخل مكان مألوف).
2. نهاية **المشهد 2** لازم تكون **ذروة أدرينالين نارية أولى (Peak Climax #1)** بعد أن اندمج المستمع بعمق في القصة (لأن المشهدين 1 + 2 معاً سيشكّلان الشورت الأول بطول ~115 ثانية ثم يتوقف فجأة في عز الذروة!).
3. نهاية **المشهد 7** لازم تكون **ذروة الانقلاب الصادم بمنتصف الفيلم (Peak Climax #2)** قبل كشف السر بثانية واحدة (لأن المشهدين 6 + 7 معاً سيشكّلان الشورت الثاني بطول ~115 ثانية ثم يتوقف فجأة في قمة الحماس!).
4. حددي وصفاً بصرياً ثابتاً بالإنجليزية للبطل/الشخصية الرئيسية (`character_visual_anchor`) ليبقى شكله وملابسه متطابقين في جميع المشاهد.

أخرجي JSON صالح بالهيكل الدقيق التالي:
{{
  "topic_key": "ملخص فريد من 6 كلمات للفكرة والمكان",
  "youtube_title": "عنوان يوتيوب ناري بالعامية المصرية يخلق فضولاً نفسياً هائلاً بدون حرق النهاية (أقل من 85 حرفاً)",
  "thumbnail_hook_text": "كلمتان إلى 4 كلمات صادمة ومختصرة جداً لغلاف اليوتيوب (مثل: الرسالة المستحيلة! / مين في الأوضة؟ / غلطة واحدة فضحته!)",
  "thumbnail_prompt": "Extreme high-CTR YouTube thumbnail 16:9 cinematic close-up scene on the RIGHT side of frame: shocked expressive Egyptian character staring at a dramatic glowing mysterious clue/object in foreground, intense chiaroscuro rim lighting in warm amber and deep crimson shadows, clean dark atmospheric space on the LEFT 42% of frame for bold title text, photorealistic 8k movie poster quality, no text, no letters, no watermark",
  "short_1_title": "عنوان ناري للشورت الأول يثير الفضول الأقصى + #shorts #غموض #قصص",
  "short_2_title": "عنوان ناري مختلف للشورت الثاني من ذروة منتصف القصة + #shorts #تشويق #حكايات",
  "description_intro": "مقدمة وصفية مشوقة جداً من سطرين تشد القارئ لمشاهدة الحلقة كاملة بدون حرق النهاية",
  "hashtags": "#دفتر_راوي #قصص_واقعية #غموض #تشويق_نفسي #حكايات_مصرية",
  "character_visual_anchor": "Photorealistic consistent main character description in English (age, Egyptian features, hairstyle, exact clothing & colors)",
  "scenes_outline": [
    {{"scene_num": 1, "scene_title": "عنوان المشهد 1", "summary": "دخول صادم في الثانية صفر بتناقض مستحيل وبداية التوتر النفسي"}},
    {{"scene_num": 2, "scene_title": "عنوان المشهد 2", "summary": "تعمق سريع وتصاعد التوتر خطوة بخطوة حتى ينتهي بلحظة ذروة وصدمة نارية معلقة (Peak Climax #1)"}},
    {{"scene_num": 3, "scene_title": "عنوان المشهد 3", "summary": "ما حدث فور فتح الباب/الظرف واكتشاف الخيط الأخطر"}},
    {{"scene_num": 4, "scene_title": "عنوان المشهد 4", "summary": "ظهور الشخصية الثانية أو المشتبه الأول وتناقض غريب في كلامه"}},
    {{"scene_num": 5, "scene_title": "عنوان المشهد 5", "summary": "البحث السري واكتشاف تفصيلة مادية لا يلاحظها أحد"}},
    {{"scene_num": 6, "scene_title": "عنوان المشهد 6", "summary": "بداية مواجهة منتصف الليل أو فخ ذكي لكشف الحقيقة"}},
    {{"scene_num": 7, "scene_title": "عنوان المشهد 7", "summary": "تصاعد هائل ينتهي بثانية واحدة قبل الانقلاب الأكبر في القصة (Peak Climax #2)"}},
    {{"scene_num": 8, "scene_title": "عنوان المشهد 8", "summary": "انفجار مفاجأة المنتصف التي تقلب كل افتراضات المستمع 180 درجة"}},
    {{"scene_num": 9, "scene_title": "عنوان المشهد 9", "summary": "تضييق الخناق واكتشاف الدافع الحقيقي المدفون"}},
    {{"scene_num": 10, "scene_title": "عنوان المشهد 10", "summary": "ربط الخيوط المتناثرة والوصول للدليل القاطع"}},
    {{"scene_num": 11, "scene_title": "عنوان المشهد 11", "summary": "المواجهة النهائية الحابسة للأنفاس وكشف الخدعة كاملة"}},
    {{"scene_num": 12, "scene_title": "عنوان المشهد 12", "summary": "الخاتمة النفسية العميقة والأثر الباقي + سؤال تفاعلي ذكي للمشاهدين"}}
  ]
}}
"""
    else:
        if niche == "en_detective_mystery":
            flavor = EN_DETECTIVE_CASES[ep_count % len(EN_DETECTIVE_CASES)]
            style_guide = (
                "You are an elite psychological whodunit & mystery storyteller combining Agatha Christie, Detective Conan, Knives Out, and MrBallen's "
                "addictive retention pacing. Hook the listener in second 0.0 with an impossible contradiction, plant Zeigarnik open loops at the end of every "
                "single scene, weave sensory micro-clues and razor-sharp suspect psychology, and stay 100% advertiser-safe (zero gore)."
            )
        else:
            flavor = EN_PSYCH_WORLDS[ep_count % len(EN_PSYCH_WORLDS)]
            style_guide = (
                "You are a master psychological suspense storyteller in the exact mold of MrBallen's most addictive true-style thrillers. "
                "Zero slow intros, zero mundane filler: drop the listener straight into a chilling paradox in sentence one, escalate tension relentlessly "
                "with vivid sensory micro-details and open curiosity loops every 60 seconds, flip assumptions upside down mid-story, and land an unforgettable ending."
            )

        blueprint_prompt = f"""
Avoid all previously used premises: {used}

Design an unputdownable 16–18 minute 12-Scene psychological suspense / mystery episode for:
"{flavor}"

Mandatory Retention Rules:
1. Scene 1 sentence 1 MUST drop an immediate 0.0-second cognitive-dissonance hook.
2. The final sentence of **Scene 2** MUST hit **Explosive Peak Climax #1** after deep immersion (Scenes 1+2 form Short #1 ~115s, cutting abruptly at peak adrenaline!).
3. The final sentence of **Scene 7** MUST hit **Explosive Mid-Movie Climax #2** one second before the big twist (Scenes 6+7 form Short #2 ~115s, cutting abruptly at peak suspense!).
4. Define `character_visual_anchor` so the protagonist looks identical across all visual prompts.

Return exact valid JSON:
{{
  "topic_key": "6-word unique premise & setting",
  "youtube_title": "Click-magnet high-curiosity YouTube title under 85 chars (never spoil the ending)",
  "thumbnail_hook_text": "2 to 4 explosive ALL-CAPS curiosity words for thumbnail (e.g. IT WAS INSIDE! / 3:14 AM CALL / FAKE ALIBI!)",
  "thumbnail_prompt": "Extreme high-CTR YouTube thumbnail 16:9 close-up cinematic shot on RIGHT side of frame: terrified/intense protagonist staring at a glowing mysterious clue in foreground, dramatic warm amber and crimson rim lighting, dark clean atmospheric negative space on LEFT 42% of frame for bold text, photorealistic 8k film still, no text, no watermark",
  "short_1_title": "Viral psychological hook title #1 + #shorts #mystery #storytime",
  "short_2_title": "Viral mid-story climax hook title #2 + #shorts #thriller #plotwist",
  "description_intro": "2-line gripping teaser description that compels viewers to watch till the final reveal",
  "hashtags": "#mystery #thriller #storytime #suspense #plotwist",
  "character_visual_anchor": "Consistent protagonist English visual description (age, features, hair, exact jacket/shirt colors)",
  "scenes_outline": [
    {{"scene_num": 1, "scene_title": "Scene 1 Title", "summary": "0.0s paradox hook + eerie initial discovery"}},
    {{"scene_num": 2, "scene_title": "Scene 2 Title", "summary": "Deep immersion & escalating dread ending on Explosive Cliffhanger Peak #1"}},
    {{"scene_num": 3, "scene_title": "Scene 3 Title", "summary": "Immediate aftermath of Peak #1 opening a deeper mystery"}},
    {{"scene_num": 4, "scene_title": "Scene 4 Title", "summary": "Key witness/suspect encounter & subtle verbal contradiction"}},
    {{"scene_num": 5, "scene_title": "Scene 5 Title", "summary": "Hidden physical clue uncovered under tense pressure"}},
    {{"scene_num": 6, "scene_title": "Scene 6 Title", "summary": "High-stakes trap or midnight verification setup"}},
    {{"scene_num": 7, "scene_title": "Scene 7 Title", "summary": "Breathless escalation cutting 1 second before the mid-movie rug-pull (Peak #2)"}},
    {{"scene_num": 8, "scene_title": "Scene 8 Title", "summary": "Mid-point twist detonates, flipping every prior assumption"}},
    {{"scene_num": 9, "scene_title": "Scene 9 Title", "summary": "Uncovering the hidden motive & timeline manipulation"}},
    {{"scene_num": 10, "scene_title": "Scene 10 Title", "summary": "Connecting the final overlooked physical detail"}},
    {{"scene_num": 11, "scene_title": "Scene 11 Title", "summary": "Pulse-pounding final confrontation & step-by-step exposure"}},
    {{"scene_num": 12, "scene_title": "Scene 12 Title", "summary": "Chilling psychological resolution & comment-driving question"}}
  ]
}}
"""

    plan = _groq_json(api_key, style_guide, blueprint_prompt, max_tokens=5500)
    char_anchor = str(plan.get("character_visual_anchor") or "a 32-year-old protagonist in a dark olive jacket over a black crew-neck shirt").strip()
    outlines = plan.get("scenes_outline") or []
    while len(outlines) < 12:
        idx = len(outlines) + 1
        outlines.append({"scene_num": idx, "scene_title": f"المشهد {idx}" if lang == "ar" else f"Scene {idx}", "summary": "Escalating suspense beat"})
    outlines = outlines[:12]

    # نولّد الـ 12 مشهداً في 3 دفعات روائية مركّزة (4 مشاهد لكل دفعة) مع وصف بصري 16:9 مطابق 100% لكلام كل مشهد!
    scenes_full: List[Dict[str, Any]] = []
    prev_tail = ""
    for batch_idx in range(3):
        batch_slice = outlines[batch_idx * 4 : (batch_idx + 1) * 4]
        s_nums = [int(x["scene_num"]) for x in batch_slice]

        if lang == "ar":
            batch_prompt = f"""
عنوان الحلقة: {plan.get('youtube_title')}
الوصف الثابت لشكل البطل بالمشاهد (`character_visual_anchor`): {char_anchor}
المخطط الكامل للـ 12 مشهداً: {json.dumps(outlines, ensure_ascii=False)}
نهاية المشهد السابق (أكملي السرد بعدها فوراً بسلاسة وتوتر متصاعد بدون إعادة): "{prev_tail}"

اكتبي الآن المشاهد الأربعة التالية بالتفصيل الكامل: المشاهد رقم {s_nums} -> {json.dumps(batch_slice, ensure_ascii=False)}

شروط صارمة جداً لكل مشهد من المشاهد الأربعة:
1. طول السرد `narration` لكل مشهد منفرد: **بين 240 و 275 كلمة كاملة** بالعامية المصرية القاهرية الطبيعية السلسة (بدون أي تشكيل أو شدّات وبدون أي مقدمات أو حشو).
2. أسلوب السرد: توتر نفسي عالٍ جداً، تفاصيل حسية تجعل المستمع يعيش اللحظة (نبض، صمت غريب، توقيت بالساعة والدقيقة، حوار حي مقتضب ومشحون)، ونهاية كل مشهد تفتح سؤالاً معلقاً يخطف الأنفاس!
3. تذكير حاسم للشورتس:
   - إذا كان **المشهد 2** ضمن هذه الدفعة: اجعلي آخر جملة في المشهد 2 تقف في **أعلى قمة صدمة وذروة حماسية معلّقة** (لحظة فتح الباب/الظرف/سماع الصوت المستحيل قبل تفسيره بثانية!).
   - إذا كان **المشهد 7** ضمن هذه الدفعة: اجعلي آخر جملة في المشهد 7 تقف في **أعلى قمة ذروة وانقلاب في منتصف القصة** قبل نطق الاسم أو السر بثانية!
4. لكل مشهد اكتبي `visual_prompt_16x9` بالإنجليزية (40–55 كلمة) يصف **بالضبط وحصرياً اللقطة البصرية المطابقة للكلام الذي يُقال في هذا المشهد تحديداً** (المكان الدقيق، الحركة الفعلية، الغرض المذكور في النص، تعبير الوجه، الإضاءة الدرامية، مع تضمين وصف البطل `{char_anchor}`) بدون أي نص مكتوب داخل الصورة (`photorealistic 16:9 widescreen cinema still, dramatic chiaroscuro lighting, no text, no watermark`) وبحيث تختلف كل صورة جذرياً عن باقي المشاهد!

أخرجي JSON فقط بهذا الهيكل:
{{
  "scenes": [
    {{
      "scene_num": {s_nums[0]},
      "scene_title": "عنوان المشهد",
      "narration": "النص الكامل للمشهد (240-275 كلمة بالعامية المصرية المشوقة)",
      "visual_prompt_16x9": "Wide 16:9 photorealistic cinematic thriller film still showing EXACT action and objects described in this scene..."
    }}
  ]
}}
"""
        else:
            batch_prompt = f"""
Episode Title: {plan.get('youtube_title')}
Protagonist Visual Anchor: {char_anchor}
Full 12-Scene Outline: {json.dumps(outlines)}
Previous scene ending (continue seamlessly): "{prev_tail}"

Write the next 4 complete scenes in full detail: Scenes {s_nums} -> {json.dumps(batch_slice)}

Strict rules for EVERY scene:
1. `narration` length per individual scene: **between 245 and 280 words** of high-tension, sensory, natural American psychological storytelling with crisp dialogue and an open curiosity loop at the end of each scene.
2. Crucial Short Climax Peaks:
   - If **Scene 2** is in this batch: end Scene 2 on the **single most explosive high-adrenaline cliffhanger beat** right as the door opens / photo flips / impossible sound plays!
   - If **Scene 7** is in this batch: end Scene 7 **one heartbeat before the jaw-dropping mid-story reveal**!
3. For each scene, write `visual_prompt_16x9` (40–55 words in English) depicting **ONLY the exact action, room, props, and emotion spoken in THAT specific scene** (incorporating `{char_anchor}`), `Wide 16:9 photorealistic dark cinema film still, dramatic lighting, no text, no watermark`, completely distinct from every other scene.

Return valid JSON only:
{{
  "scenes": [
    {{
      "scene_num": {s_nums[0]},
      "scene_title": "Scene Title",
      "narration": "Full 245-280 word spoken scene text",
      "visual_prompt_16x9": "Wide 16:9 photorealistic dark cinema film still..."
    }}
  ]
}}
"""
        b_res = _groq_json(api_key, style_guide, batch_prompt, max_tokens=5800)
        got_scenes = b_res.get("scenes") or []
        for local_i, outline_item in enumerate(batch_slice):
            s_obj = got_scenes[local_i] if local_i < len(got_scenes) else {}
            s_num = int(outline_item["scene_num"])
            s_title = str(s_obj.get("scene_title") or outline_item["scene_title"]).strip()
            s_txt = re.sub(r"[\u064B-\u065F\u0670]", "", str(s_obj.get("narration") or "")).strip()
            v_p = str(
                s_obj.get("visual_prompt_16x9")
                or f"Wide 16:9 photorealistic dark psychological thriller film still of {char_anchor} in {outline_item['summary']}, dramatic chiaroscuro lighting, 35mm cinema lens, no text, no watermark"
            ).strip()
            if "no text" not in v_p.lower():
                v_p += ", photorealistic 35mm cinema film still, dramatic lighting, no text, no watermark"
            scenes_full.append({
                "scene_num": s_num,
                "scene_title": s_title,
                "narration": s_txt,
                "visual_prompt_16x9": v_p,
            })
            if s_txt:
                prev_tail = " ".join(s_txt.split()[-35:])

    # الآن نولّد 5 مشاهد رأسية كاملة 9:16 مخصصة للشورت الأول (المشهد 1 + 2) و5 مشاهد رأسية 9:16 مخصصة للشورت الثاني (المشهد 6 + 7)
    # بحيث تظهر كل صورة رأسية كاملة 100% على الموبايل بدون أي قص جانبي، وتطابق تطور الكلام لحظة بلحظة بدون تكرار!
    sh1_story_text = f"{scenes_full[0]['narration']} {scenes_full[1]['narration']}"
    sh2_story_text = f"{scenes_full[5]['narration']} {scenes_full[6]['narration']}"

    vert_prompt_req = f"""
Protagonist Visual Anchor: {char_anchor}

SHORT #1 SPOKEN STORY (~115s, ending at Peak Climax #1):
\"\"\"{sh1_story_text}\"\"\"

SHORT #2 SPOKEN STORY (~115s, ending at Peak Climax #2):
\"\"\"{sh2_story_text}\"\"\"

Split Short #1 chronologically into **5 distinct sequential beats** (Beat 1 = 0-20%, Beat 2 = 20-40%, Beat 3 = 40-60%, Beat 4 = 60-80%, Beat 5 = 80-100% Climax Peak) and write 5 dedicated **FULL VERTICAL 9:16 PORTRAIT** English AI image prompts (`short_1_vertical_prompts`).
Do the exact same for Short #2 (`short_2_vertical_prompts` — 5 completely new vertical 9:16 prompts matching Beats 1..5 of Short #2).

CRITICAL FRAMING RULE FOR ALL 10 PROMPTS:
- Every prompt MUST start with: `"Full vertical 9:16 portrait smartphone cinema frame, centered vertical composition with full subject head-to-waist inside frame, "`
- Every prompt MUST depict the EXACT spoken action/object at that specific 20% beat of the Short, with zero generic filler, zero repeated scenes, and end with `", dramatic chiaroscuro lighting, photorealistic, no text, no watermark"`.

Return valid JSON only:
{{
  "short_1_vertical_prompts": ["prompt1", "prompt2", "prompt3", "prompt4", "prompt5"],
  "short_2_vertical_prompts": ["prompt1", "prompt2", "prompt3", "prompt4", "prompt5"]
}}
"""
    vert_res = _groq_json(
        api_key,
        "You are a cinema storyboard director specializing in vertical 9:16 thriller framing where 100% of the subject fits cleanly inside a narrow vertical portrait screen.",
        vert_prompt_req,
        max_tokens=3000,
    )

    def _clean_vert_list(raw_list: Any, fallback_base: List[Dict[str, Any]]) -> List[str]:
        out_v: List[str] = []
        items = raw_list if isinstance(raw_list, list) else []
        for i in range(5):
            p = str(items[i]).strip() if i < len(items) and items[i] else ""
            if not p:
                ref = fallback_base[min(i // 3, len(fallback_base) - 1)]["visual_prompt_16x9"]
                p = f"Full vertical 9:16 portrait smartphone cinema frame, centered vertical composition, {ref}"
            if "9:16" not in p:
                p = "Full vertical 9:16 portrait smartphone cinema frame, centered vertical composition, " + p
            if "no text" not in p.lower():
                p += ", photorealistic, dramatic lighting, no text, no watermark"
            out_v.append(p)
        return out_v

    sh1_vprompts = _clean_vert_list(vert_res.get("short_1_vertical_prompts"), scenes_full[0:2])
    sh2_vprompts = _clean_vert_list(vert_res.get("short_2_vertical_prompts"), scenes_full[5:7])

    tk = str(plan.get("topic_key") or plan.get("youtube_title", cid))[:80]
    if tk:
        memory[cid].setdefault("used_topics", []).append(tk)

    yt_title = str(plan.get("youtube_title") or channel_cfg["brand_name"]).strip()
    sh1_title = str(plan.get("short_1_title") or f"{yt_title[:60]} #shorts").strip()
    sh2_title = str(plan.get("short_2_title") or f"{yt_title[:55]} - الذروة #shorts").strip()
    thumb_hook = re.sub(
        r"[\u064B-\u065F\u0670]",
        "",
        str(plan.get("thumbnail_hook_text") or " ".join(yt_title.split()[:4])),
    ).strip()

    return {
        "channel_id": cid,
        "topic_key": tk,
        "youtube_title": yt_title,
        "thumbnail_hook_text": thumb_hook,
        "thumbnail_badge_text": channel_cfg.get("thumb_badge", ""),
        "thumbnail_prompt": str(
            plan.get("thumbnail_prompt")
            or f"Extreme high-CTR YouTube thumbnail 16:9 close-up shot on RIGHT side of frame, shocked {char_anchor} staring at glowing mysterious clue, dark clean negative space on LEFT side, dramatic lighting, photorealistic, no text"
        ),
        "short_title": sh1_title,
        "short_1_title": sh1_title,
        "short_2_title": sh2_title,
        "description_intro": str(plan.get("description_intro") or yt_title).strip(),
        "hashtags": str(plan.get("hashtags") or "").strip(),
        "character_visual_anchor": char_anchor,
        "scenes": scenes_full,
        "scene_prompts": [s["visual_prompt_16x9"] for s in scenes_full],
        "short_1_scene_indices": [0, 1],  # المشهدان 1 + 2 (~115 ثانية تنتهي عند الذروة النارية الأولى!)
        "short_2_scene_indices": [5, 6],  # المشهدان 6 + 7 (~115 ثانية تنتهي عند ذروة منتصف القصة!)
        "short_1_vertical_prompts": sh1_vprompts,
        "short_2_vertical_prompts": sh2_vprompts,
        "cta_spoken_1": channel_cfg["cta_spoken_1"],
        "cta_spoken_2": channel_cfg["cta_spoken_2"],
        "cta_banner": channel_cfg["cta_banner"],
    }
