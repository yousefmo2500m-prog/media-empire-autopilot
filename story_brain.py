# -*- coding: utf-8 -*-
"""
العقل النفسي والخوارزمي V10.0 (Hyper-Realistic Psychological Suspense + 8-Second Visual Storyboard + 2026 Algorithm SEO)
1) قصص واقعية نفسية حديثة تحبس الأنفاس (مثل تجربة «رسالة 3 الفجر»): ممنوع تماماً الخيال الرخيص أو الفصحى المترجمة!
   كل جملة مكتوبة بإيقاع تنفس بشري طبيعي بالعامية المصرية القاهرية الحقيقية (مع فواصل تنفس قصيرة `..`) ليخرج صوت الراوية البشرية طبيعياً 100%.
2) حزمة الخوارزميات الكاملة 2026 (YouTube + TikTok + Facebook Algorithm Stack):
   - عنوان فجوة فضول عالية النقر (High-CTR Curiosity Gap) + عبارة غلاف كاملة من 3–4 كلمات صادمة.
   - أول سطرين خاطفين قبل زر «عرض المزيد» + ملخص غني بالكلمات البحثية + فصول مشاهد غير حارقة + سؤال تحدي ذكاء يفجّر التعليقات + 18 تاج بحثي.
3) مولّد اللقطات البصرية المتزامن كل 8 ثوانٍ (`generate_8sec_shot_prompts`):
   - يقرأ الكلمات المنطوقة فعلياً في كل نافذة 8 ثوانٍ ويولّد لها مشهداً بصرياً فريداً ومختلفاً في زاوية الكاميرا (صفر تكرار لأي صورة!).
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

EG_REALISTIC_THRILLERS = [
    "إثارة نفسية واقعية جداً داخل شقة أو عمارة سكنية بمصر: رسالة أو صورة على الواتساب الساعة 3 الفجر تكشف إن حد شايف البطل دلوقتي حالاً، وتتوالى المفاجآت الواقعية المرعبة التوتر لحد كشف خطة عاقلة مستحيل توقعها",
    "إثارة نفسية وخدعة دهاء بشري بارد: اكتشاف كاميرا خفية أو تسجيل صوتي بالصدفة في البيت أو المكتب يكشف إن أقرب الناس بيدبر لعبة نفسية محكمة بالورقة والقلم، وقلب الطاولة عليهم بذكاء يوقف القلب",
    "غموض نفسي واقعي حول شقة مقفولة أو جيرة مريبة أو عقد/وصية غريبة في القاهرة: تفصيلة صغيرة في فاتورة كهرباء أو كاميرا الأسانسير تفتح خيط سر مدفون يقلب حياة كل الشخصيات",
    "ليلة توتر نفسي حقيقية لا تُنسى (نوبتجية ليلية، توصيلة متأخرة، أو مكالمة بالغلط من رقم مسجل باسم البطل نفسه): كل دقيقة يظهر دليل مادي ملموس يناقض اللي قبله حتى الصدمة الكبرى في النهاية",
]

EG_CONAN_CASES = [
    "قضية غرفة مغلقة واقعية فائقة الذكاء على طريقة المحقق كونان في فيلا أو مكتب بالقاهرة: الباب والشبابيك مقفولين من جوه، 4 مشتبه بهم لكل واحد دافع قوي، وخدعة فيزيائية/زمنية عبقرية تكشفها تفصيلة صغيرة جداً",
    "قضية حجة الغياب المستحيلة بالكاميرات والتوقيت على طريقة المحقق كونان: الجاني ظهر في بث مباشر أو كاميرا مراقبة في مكان تاني وقت الحدث بالثانية، ودليل عبقري يكشف التلاعب بالتوقيت",
    "قضية العشاء المغلق أو الباخرة النيلية: اختفاء مستند خطير أو جوهرة نادرة وسط 4 أشخاص محدش فيهم خرج من القاعة، وكل شاهد بيكدب في تفصيلة واحدة بس لحد المواجهة الصاعقة",
]

EN_REALISTIC_THRILLERS = [
    "a grounded, hyper-realistic MrBallen-style modern psychological thriller starting at 3:14 AM with an impossible notification or photo from inside an ordinary apartment—zero supernatural clichés, 100% chilling human calculation",
    "a pulse-pounding psychological cat-and-mouse thriller where one tiny discrepancy on a doorbell camera or receipt exposes a jaw-dropping double life right next door",
    "a claustrophobic, realistic night-shift or rideshare psychological suspense story where small physical details stop adding up until a mind-bending real-world twist",
]

EN_DETECTIVE_CASES = [
    "a razor-sharp Detective Conan / Knives Out realistic locked-room investigation with 4 suspects, timestamped alibis, fair-play physical clues, and a brilliant step-by-step deduction",
    "an impossible CCTV & clockwork-alibi mystery where one tiny reflection, shadow, or audio delay exposes the mastermind everyone trusted",
]

CAMERA_ANGLES = [
    "Extreme close-up macro shot",
    "Tight dramatic portrait close-up on eyes and expression",
    "Over-the-shoulder POV shot",
    "Medium cinematic two-shot with deep shadows",
    "Low-angle suspense wide hallway shot",
    "High-angle surveillance-style dramatic shot",
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
                "temperature": 0.82,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            }
            resp = requests.post(f"{GROQ_BASE}/chat/completions", headers=headers, json=payload, timeout=115)
            if resp.status_code == 429:
                time.sleep(min(15.0, float(resp.headers.get("retry-after", 4.5))))
                continue
            if resp.status_code != 200:
                payload.pop("response_format", None)
                resp = requests.post(f"{GROQ_BASE}/chat/completions", headers=headers, json=payload, timeout=115)
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
                "أنتِ حكّاءة ألغاز وتحقيقات مصرية محترفة جداً (بأسلوب سامح سند وبيسوهات والمحقق كونان)، تتكلمين بالعامية المصرية القاهرية الحقيقية الدافئة 100%. "
                "ممنوع نهائياً الكلمات الفصحى المترجمة مثل (التي، الذي، حيث، فندق مهجور، رمز ميكانيكي، الانقلاب القاتل، الخاتمة النفسية)! "
                "اكتبي باللهجة اللي بنتكلم بيها في القاهرة بجد وبنفس بشري طبيعي مليان فواصل تشويق قصيرة `..` وتفاصيل واقعية ملموسة تخلي اللي بيسمع مش قادر يغمض عينه."
            )
        else:
            flavor = EG_REALISTIC_THRILLERS[ep_count % len(EG_REALISTIC_THRILLERS)]
            style_guide = (
                "أنتِ حكّاءة إثارة نفسية مصرية بارعة جداً (نفس روح تجربة «رسالة 3 الفجر» وأقوى حلقات بيسوهات وسامح سند)، تتكلمين بالعامية المصرية القاهرية الحقيقية السلسة 100%. "
                "ممنوع نهائياً الخيال الرخيص أو الأشباح أو الجمل المترجمة الركيكة مثل (التي توفت، الرمز الميكانيكي، في ليلة عاصفة)! "
                "القصة لازم تكون واقعية جداً لدرجة إن المستمع يحس إنها ممكن تحصله الليلة في شقته أو موبايله، مكتوبة بجمل قصيرة وإيقاع تنفس بشري طبيعي `..` وحلقات فضول مفتوحة كل دقيقة."
            )

        blueprint_prompt = f"""
الأفكار المستعملة سابقاً (ممنوع تكرارها نهائياً): {used}

صمّمي حلقة إثارة نفسية واقعية / تحقيق ذكي لا يمكن التوقف عن سماعها (16–17 دقيقة، مقسمة لـ 12 مشهداً) من فئة:
«{flavor}»

قواعد الخوارزميات والجذب النفسي الصارمة:
1. عنوان اليوتيوب (`youtube_title`): عنوان فضول نفسي واقعي خارق بالعامية المصرية بدون حرق (مثل: «الساعة ٣ الفجر جتلي صورة لباب أوضتي.. من جوه شقتي!» أو «كاميرا الأسانسير سجلت دخوله.. بس عمره ما خرج!»).
2. نص الغلاف المصغّر (`thumbnail_hook_text`): **جملة مكتملة المعنى وصادمة من 3 أو 4 كلمات فقط** (مثل: «الصورة اتصورت من جوه!» أو «مين واقف ورا الباب؟» أو «غلطة واحدة فضحته!» — ممنوع جمل ناقصة مثل «صوت من بعد»!).
3. عناوين المشاهد الـ 12 (`scenes_outline`): لازم تكون عناوين مثيرة للفضول وغير حارقة للأحداث (ممنوع كتابة «الخاتمة» أو «الانقلاب»؛ اكتبي مثلاً: «المشهد ١١: تفصيلة الـ ٣ ثواني في التسجيل»).
4. نهاية **المشهد 2** = ذروة أدرينالين نارية أولى (لقطع الشورت الأول في عز الحماس!). ونهاية **المشهد 7** = ذروة صدمة منتصف القصة (لقطع الشورت الثاني قبل الكشف بثانية!).

أخرجي JSON صالح بالهيكل التالي:
{{
  "topic_key": "ملخص فريد 6 كلمات للفكرة الواقعية",
  "youtube_title": "عنوان يوتيوب واقعي ناري يرفع نسبة النقر CTR لأقصى درجة (أقل من 82 حرفاً)",
  "thumbnail_hook_text": "جملة صادمة مكتملة من 3 أو 4 كلمات للغلاف",
  "thumbnail_prompt": "Hyper-realistic 8k Netflix thriller YouTube thumbnail, 16:9 widescreen, dramatic split composition: on the RIGHT half an intense close-up of a terrified Egyptian person with wide shocked eyes illuminated by cold blue phone glow and crimson rim light, holding up a glowing smartphone showing a creepy hallway door photo, dark clean moody negative space on the LEFT 45% for bold text, ultra-detailed skin texture, ARRI Alexa 35mm cinema still, no text, no letters, no watermark",
  "short_1_title": "عنوان ناري للشورت الأول يخطف الانتباه فوراً + #shorts #قصص_واقعية #غموض",
  "short_2_title": "عنوان ناري مختلف للشورت الثاني من ذروة منتصف القصة + #shorts #تشويق #حكايات",
  "seo_hook_2lines": "سطران ناريان يظهران في أول سطرين بالوصف قبل زر عرض المزيد لجذب المشاهد وخوارزمية البحث فوراً بدون حرق النهاية",
  "seo_synopsis": "فقرة تشويقية غنية من 4 جمل تصف أجواء القصة وتدمج طبيعياً أقوى كلمات البحث (قصص واقعية مثيرة، غموض نفسي، حكايات مصرية تحبس الأنفاس، ألغاز وتحقيقات) لرفع اقتراحات يوتيوب",
  "engagement_question": "سؤال تحدي ذكي للمشاهدين يربط بدقيقة/مشهد معين في الحلقة ويدفعهم لكتابة توقعاتهم في التعليقات",
  "seo_tags": ["تاج 1", "تاج 2", "تاج 3", "تاج 4", "تاج 5", "تاج 6", "تاج 7", "تاج 8"],
  "hashtags": "#دفتر_راوي #قصص_واقعية #غموض_نفسي #حكايات_مصرية #قصص_مثيرة",
  "character_visual_anchor": "Consistent realistic English visual description of protagonist (e.g. 29-year-old Egyptian man/woman, exact hairstyle, wearing a dark navy zip hoodie over a grey t-shirt, modern Cairo apartment setting)",
  "scenes_outline": [
    {{"scene_num": 1, "scene_title": "عنوان فضولي للمشهد 1", "summary": "دخول فوري في الثانية صفر بواقعة ملموسة مرعبة التوتر"}},
    {{"scene_num": 2, "scene_title": "عنوان فضولي للمشهد 2", "summary": "تعمق وتصاعد حابس للأنفاس ينتهي عند قمة الذروة النارية الأولى (Peak Climax #1)"}},
    {{"scene_num": 3, "scene_title": "عنوان فضولي للمشهد 3", "summary": "ما ظهر فور فتح الباب/الرسالة وبداية الخيط الأخطر"}},
    {{"scene_num": 4, "scene_title": "عنوان فضولي للمشهد 4", "summary": "أول مواجهة مع جار/شخصية قريبة وتناقض غريب في كلامه"}},
    {{"scene_num": 5, "scene_title": "عنوان فضولي للمشهد 5", "summary": "فحص كاميرا أو إيصال أو تسجيل واكتشاف تفصيلة مستحيلة"}},
    {{"scene_num": 6, "scene_title": "عنوان فضولي للمشهد 6", "summary": "نصب فخ ذكي في نص الليل للتأكد من الشك"}},
    {{"scene_num": 7, "scene_title": "عنوان فضولي للمشهد 7", "summary": "تصاعد رهيب يقف قبل كشف الصدمة الكبرى بثانية واحدة (Peak Climax #2)"}},
    {{"scene_num": 8, "scene_title": "عنوان فضولي للمشهد 8", "summary": "انكشاف مفاجأة المنتصف التي تقلب كل التوقعات رأساً على عقب"}},
    {{"scene_num": 9, "scene_title": "عنوان فضولي للمشهد 9", "summary": "الخيط الخفي اللي بيربط كل التفاصيل ببعض"}},
    {{"scene_num": 10, "scene_title": "عنوان فضولي للمشهد 10", "summary": "الوصول للدليل المادي القاطع"}},
    {{"scene_num": 11, "scene_title": "عنوان فضولي للمشهد 11", "summary": "المواجهة الحاسمة وكشف الخطة خطوة بخطوة"}},
    {{"scene_num": 12, "scene_title": "عنوان فضولي للمشهد 12", "summary": "الحقيقة الكاملة المدهشة وسؤال يترك أثر نفسي عميق"}}
  ]
}}
"""
    else:
        flavor = (
            EN_DETECTIVE_CASES[ep_count % len(EN_DETECTIVE_CASES)]
            if niche == "en_detective_mystery"
            else EN_REALISTIC_THRILLERS[ep_count % len(EN_REALISTIC_THRILLERS)]
        )
        style_guide = (
            "You are an elite psychological suspense & mystery storyteller in the exact style of MrBallen's most viral realistic episodes. "
            "Zero supernatural clichés, zero stiff prose: write natural, breathy spoken American storytelling using subtle `...` dramatic pauses, "
            "hyper-specific everyday details, relentless Zeigarnik open loops, and 100% advertiser-safe realism."
        )
        blueprint_prompt = f"""
Avoid all previously used premises: {used}

Design a hyper-realistic, unputdownable 16-minute 12-Scene episode for:
"{flavor}"

Return exact valid JSON:
{{
  "topic_key": "6-word unique realistic premise",
  "youtube_title": "High-CTR viral realistic YouTube title under 80 chars (zero spoilers)",
  "thumbnail_hook_text": "Complete 3-to-4 word shocking hook (e.g. IT CAME FROM INSIDE! / CHECK THE REFLECTION! / NOT ALONE AT 3AM!)",
  "thumbnail_prompt": "Hyper-realistic 8k Netflix thriller YouTube thumbnail, 16:9 widescreen, dramatic split composition: on RIGHT half intense close-up of terrified protagonist with wide eyes lit by blue smartphone glow and red rim light, dark clean negative space on LEFT 45% for bold text, ARRI Alexa 35mm cinema film still, no text, no watermark",
  "short_1_title": "Viral hook title #1 + #shorts #storytime #thriller",
  "short_2_title": "Viral mid-story climax title #2 + #shorts #mystery #plotwist",
  "seo_hook_2lines": "Gripping 2-line hook above YouTube Show More fold packed with curiosity and search keywords",
  "seo_synopsis": "4-sentence SEO-rich story teaser weaving high-retention mystery/storytime keywords naturally",
  "engagement_question": "Specific clue/timestamp debate question compelling viewers to comment their theory",
  "seo_tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"],
  "hashtags": "#storytime #mystery #thriller #plotwist #truestories",
  "character_visual_anchor": "Consistent realistic protagonist English visual description (age, hair, exact hoodie/jacket color, modern setting)",
  "scenes_outline": [
    {{"scene_num": 1, "scene_title": "Curiosity Scene 1 Title", "summary": "0.0s realistic paradox hook"}},
    {{"scene_num": 2, "scene_title": "Curiosity Scene 2 Title", "summary": "Deep escalation ending on Explosive Peak Climax #1"}},
    {{"scene_num": 3, "scene_title": "Curiosity Scene 3 Title", "summary": "Immediate discovery behind Peak #1"}},
    {{"scene_num": 4, "scene_title": "Curiosity Scene 4 Title", "summary": "First suspect/neighbor contradiction"}},
    {{"scene_num": 5, "scene_title": "Curiosity Scene 5 Title", "summary": "Timestamp/camera physical anomaly"}},
    {{"scene_num": 6, "scene_title": "Curiosity Scene 6 Title", "summary": "Midnight verification trap"}},
    {{"scene_num": 7, "scene_title": "Curiosity Scene 7 Title", "summary": "Breathless buildup cutting 1s before mid-movie twist (Peak Climax #2)"}},
    {{"scene_num": 8, "scene_title": "Curiosity Scene 8 Title", "summary": "Mid-point twist flips every assumption"}},
    {{"scene_num": 9, "scene_title": "Curiosity Scene 9 Title", "summary": "Hidden motive & timeline connection"}},
    {{"scene_num": 10, "scene_title": "Curiosity Scene 10 Title", "summary": "Decisive physical clue"}},
    {{"scene_num": 11, "scene_title": "Curiosity Scene 11 Title", "summary": "High-stakes confrontation"}},
    {{"scene_num": 12, "scene_title": "Curiosity Scene 12 Title", "summary": "Full mind-blowing payoff"}}
  ]
}}
"""

    plan = _groq_json(api_key, style_guide, blueprint_prompt, max_tokens=5500)
    char_anchor = str(
        plan.get("character_visual_anchor")
        or "a 29-year-old protagonist wearing a dark navy zip hoodie over a charcoal t-shirt in a realistic modern apartment"
    ).strip()

    outlines = (plan.get("scenes_outline") or [])[:12]
    while len(outlines) < 12:
        idx = len(outlines) + 1
        outlines.append({"scene_num": idx, "scene_title": f"المشهد {idx}" if lang == "ar" else f"Scene {idx}", "summary": "Escalating realistic suspense"})

    scenes_full: List[Dict[str, Any]] = []
    prev_tail = ""
    for batch_idx in range(3):
        batch_slice = outlines[batch_idx * 4 : (batch_idx + 1) * 4]
        s_nums = [int(x["scene_num"]) for x in batch_slice]

        if lang == "ar":
            batch_prompt = f"""
عنوان الحلقة: {plan.get('youtube_title')}
المخطط الكامل: {json.dumps(outlines, ensure_ascii=False)}
آخر جملة من المشهد السابق (كمّلي بعدها فوراً كأنها حكاية واحدة متصلة بدون إعادة): "{prev_tail}"

اكتبي السرد الصوتي الكامل للمشاهد الأربعة التالية: {json.dumps(batch_slice, ensure_ascii=False)}

قواعد الأداء الصوتي البشري الطبيعي (مهمة جداً عشان الصوت يطلع طبيعي 100% زي الإنسان الحقيقي):
1. الطول لكل مشهد منفرد: **بين 235 و 270 كلمة كاملة** بالعامية المصرية القاهرية الطبيعية 100% بدون أي تشكيل أو شدّات.
2. **ممنوع نهائياً** أي كلمة فصحى أو مترجمة (ممنوع: التي، الذي، حيث، بينما، فندق مهجور، رمز ميكانيكي، مؤلم، قاتل)! اكتبي زي ما بنحكي في الحقيقة بالظبط: «بص بقى.. اللي حصل ساعتها خلّى قلبي يدق في وداني.. مسكت الموبايل بإيد بتترعش.. وكبّرت الصورة على الآخر..».
3. استعملي نقطتين `..` بين الجمل القصيرة لإعطاء الراوية نَفَساً بشرياً طبيعياً وتشويقاً هادئاً غير مسرحي.
4. لو المشهد رقم **2** موجود هنا: اختميه في أعلى لحظة صدمة وأدرينالين معلقة (قبل كشف اللي ورا الباب/الصورة بثانية!). ولو المشهد رقم **7** موجود هنا: اختميه قبل انكشاف سر منتصف القصة بثانية واحدة!

أرجعي JSON فقط:
{{
  "scenes": [
    {{"scene_num": {s_nums[0]}, "scene_title": "عنوان المشهد الفضولي", "narration": "النص الكامل للمشهد بالعامية المصرية الحية"}}
  ]
}}
"""
        else:
            batch_prompt = f"""
Episode Title: {plan.get('youtube_title')}
Full Outline: {json.dumps(outlines)}
Previous scene tail (continue seamlessly): "{prev_tail}"

Write the full spoken narration for these 4 scenes: {json.dumps(batch_slice)}

Human Voice Prosody Rules:
1. Length per scene: **240 to 275 words** of hyper-realistic, conversational spoken American storytelling.
2. Use short punchy clauses and occasional `...` breath pauses so the narrator sounds 100% human, intimate, and suspenseful.
3. End Scene 2 on Peak Climax #1, and end Scene 7 one heartbeat before the mid-story twist!

Return valid JSON only:
{{
  "scenes": [
    {{"scene_num": {s_nums[0]}, "scene_title": "Curiosity Scene Title", "narration": "Full spoken scene narration"}}
  ]
}}
"""
        b_res = _groq_json(api_key, style_guide, batch_prompt, max_tokens=5600)
        got_scenes = b_res.get("scenes") or []
        for local_i, outline_item in enumerate(batch_slice):
            s_obj = got_scenes[local_i] if local_i < len(got_scenes) else {}
            s_num = int(outline_item["scene_num"])
            s_title = str(s_obj.get("scene_title") or outline_item["scene_title"]).strip()
            s_txt = re.sub(r"[\u064B-\u065F\u0670]", "", str(s_obj.get("narration") or "")).strip()
            scenes_full.append({
                "scene_num": s_num,
                "scene_title": s_title,
                "narration": s_txt,
            })
            if s_txt:
                prev_tail = " ".join(s_txt.split()[-32:])

    tk = str(plan.get("topic_key") or plan.get("youtube_title", cid))[:80]
    if tk:
        memory[cid].setdefault("used_topics", []).append(tk)

    yt_title = str(plan.get("youtube_title") or channel_cfg["brand_name"]).strip()
    raw_hook = re.sub(r"[\u064B-\u065F\u0670]", "", str(plan.get("thumbnail_hook_text") or "")).strip()
    if len(raw_hook.split()) < 2:
        raw_hook = " ".join(yt_title.split()[:4])

    combined_tags: List[str] = []
    for t in [*(plan.get("seo_tags") or []), *(channel_cfg.get("base_tags") or [])]:
        ts = str(t).strip().lstrip("#")
        if ts and ts not in combined_tags:
            combined_tags.append(ts)

    return {
        "channel_id": cid,
        "topic_key": tk,
        "youtube_title": yt_title,
        "thumbnail_hook_text": raw_hook,
        "thumbnail_badge_text": channel_cfg.get("thumb_badge", ""),
        "thumbnail_prompt": str(
            plan.get("thumbnail_prompt")
            or f"Hyper-realistic 8k Netflix thriller YouTube thumbnail, 16:9 widescreen, RIGHT side intense close-up of terrified {char_anchor} lit by glowing phone and red rim light, LEFT 45% clean dark space for text, no text, no watermark"
        ),
        "short_title": str(plan.get("short_1_title") or f"{yt_title[:58]} #shorts").strip(),
        "short_1_title": str(plan.get("short_1_title") or f"{yt_title[:58]} #shorts").strip(),
        "short_2_title": str(plan.get("short_2_title") or f"{yt_title[:54]} - الجزء الأخطر #shorts").strip(),
        "seo_hook_2lines": str(plan.get("seo_hook_2lines") or yt_title).strip(),
        "seo_synopsis": str(plan.get("seo_synopsis") or "").strip(),
        "engagement_question": str(plan.get("engagement_question") or "").strip(),
        "seo_tags": combined_tags[:18],
        "hashtags": str(plan.get("hashtags") or "").strip(),
        "character_visual_anchor": char_anchor,
        "scenes": scenes_full,
        "cta_spoken_1": channel_cfg["cta_spoken_1"],
        "cta_spoken_2": channel_cfg["cta_spoken_2"],
        "cta_banner": channel_cfg["cta_banner"],
    }


def generate_8sec_shot_prompts(
    windows: List[Dict[str, Any]],
    character_visual_anchor: str,
    story_title: str,
    api_key: str,
    is_vertical: bool = False,
) -> List[str]:
    """
    يأخذ قائمة النوافذ الزمنية (كل نافذة ~8 ثوانٍ مع النص المنطوق فعلياً داخلها `spoken_text`)
    ويولّد لكل نافذة 8 ثوانٍ وصف صورة FLUX سينمائي فريد ومطابق 100% للكلام المنطوق في تلك الثواني الثماني بالضبط،
    مع تنويع زوايا الكاميرا ومنع تكرار أي لقطة مرتين!
    """
    frame_prefix = (
        "Full vertical 9:16 smartphone cinema portrait frame, entire subject centered head-to-waist inside vertical frame, "
        if is_vertical
        else "Wide 16:9 Netflix thriller 35mm ARRI Alexa cinema still, "
    )
    sys_msg = (
        "You are an elite Netflix thriller cinematographer. Convert each 8-second spoken narration snippet into ONE hyper-specific, "
        "realistic English visual prompt matching ONLY what is spoken in that exact 8-second window. Never repeat compositions; vary camera angles "
        "(close-up on object/phone, expressive face close-up, over-the-shoulder POV, tense corridor shot). Zero text/letters in images."
    )

    prompts_out: List[str] = []
    batch_sz = 24
    for start_i in range(0, len(windows), batch_sz):
        chunk = windows[start_i : start_i + batch_sz]
        items_desc = [
            {
                "idx": k,
                "angle_hint": CAMERA_ANGLES[(start_i + k) % len(CAMERA_ANGLES)],
                "spoken_8sec": w.get("text", "")[:220],
            }
            for k, w in enumerate(chunk)
        ]
        usr_msg = f"""
Story: {story_title}
Consistent Protagonist Appearance: {character_visual_anchor}
Framing: {"Vertical 9:16 full portrait (no side crop)" if is_vertical else "Widescreen 16:9"}

For each of these {len(chunk)} sequential 8-second narration windows, write a vivid 28-40 word English photorealistic prompt matching `spoken_8sec` using `angle_hint` (incorporate protagonist appearance whenever the protagonist is visible; if `spoken_8sec` focuses on an object/door/phone/street, show a dramatic close-up of that exact object):
{json.dumps(items_desc, ensure_ascii=False)}

Return JSON only:
{{"prompts": ["prompt_0", "prompt_1", ...]}}
"""
        try:
            res = _groq_json(api_key, sys_msg, usr_msg, max_tokens=4500)
            got = res.get("prompts") or []
        except Exception:
            got = []

        for k, w in enumerate(chunk):
            raw_p = str(got[k]).strip() if (k < len(got) and got[k]) else ""
            angle = CAMERA_ANGLES[(start_i + k) % len(CAMERA_ANGLES)]
            if not raw_p:
                raw_p = f"{angle} of {character_visual_anchor} reacting in tense modern room during beat #{start_i + k + 1}"
            full_p = f"{frame_prefix}{raw_p}, realistic moody tungsten and teal shadows, sharp focus, 8k photorealistic film grain, no text, no watermark"
            prompts_out.append(full_p)

    return prompts_out
