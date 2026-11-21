# -*- coding: utf-8 -*-
"""
العقل القصصي V18 (Cold-Open Teaser + Gemini Key Failover + Visual-Beat Prompts)
1) مقدمة تشويقية إجبارية حابسة للأنفاس في أول 25–30 ثانية (`teaser_intro`) لكل فيديو طويل + مقدمة خاطفة (`short_hook_intro`) لكل شورت:
   - تبدأ بومضة نارية من أخطر لحظة قبل النهاية (Flash-Forward بدون حرق!) + تطابق 100% مع وعد العنوان والصورة المصغرة (أهم عامل في خوارزمية يوتيوب 2026!) + سؤال مفتوح يجبر المشاهد يكمل لآخر ثانية ليعرف النهاية!
2) جسور احتفاظ بالمشاهد (Retention Bridges) كل 3 دقائق لكسر الملل ومنع هبوط منحنى المشاهدة (AVD > 55%).
3) أوصاف بصرية واضحة ومضاءة درامياً لكل نافذة زمنية يمررها محرر الفيديو.
"""

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List

import os
import requests

try:
    import _env_loader
except Exception:
    pass

from channel_director import (
    build_director_prompt_injection,
    load_director_state,
    select_next_episode_strategy,
    validate_text_against_constitution,
)

GROQ_BASE = "https://api.groq.com/openai/v1"
PREFERRED_MODELS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
    "allam-2-7b",
]
GEMINI_JSON_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemini-3-flash-preview",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]

EG_REALISTIC_THRILLERS = [
    "إثارة نفسية واقعية جداً داخل شقة أو عمارة سكنية بمصر: صورة أو رسالة على الواتساب الساعة 3 الفجر تكشف إن حد شايف البطل دلوقتي حالاً، وتتوالى المفاجآت الواقعية المرعبة التوتر لحد كشف خطة عاقلة مستحيل توقعها",
    "إثارة نفسية وخدعة دهاء بشري بارد: اكتشاف تسجيل صوتي أو كاميرا مراقبة بالصدفة في البيت أو المكتب يكشف إن أقرب الناس بيدبر لعبة نفسية محكمة بالورقة والقلم، وقلب الطاولة عليهم بذكاء يوقف القلب",
    "غموض نفسي واقعي حول شقة مقفولة أو جيرة مريبة أو عقد غريب في القاهرة: تفصيلة صغيرة في فاتورة كهرباء أو كاميرا الأسانسير تفتح خيط سر مدفون يقلب حياة كل الشخصيات",
    "ليلة توتر نفسي حقيقية لا تُنسى (نوبتجية ليلية، توصيلة متأخرة، أو مكالمة من رقم مسجل باسم البطل نفسه): كل دقيقة يظهر دليل مادي ملموس يناقض اللي قبله حتى الصدمة الكبرى في النهاية",
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

SCENE_STAGING_MODES = [
    "Object & clue focus shot (show the exact physical object, phone, door lock, document, or clue mentioned—no face portrait)",
    "Medium cinema action shot (waist-up character in closed turtleneck sweater or zipped dark jacket actively performing the spoken action in the room)",
    "Hands-in-action POV shot (close view of hands holding/examining/opening the exact item mentioned in narration)",
    "Wide atmospheric location shot (establish the room, apartment hallway, office, or street scene described right now)",
    "Over-the-shoulder discovery shot (camera behind character's clothed shoulder looking directly at what they just noticed)",
    "Wide dramatic room staging (full scene environment showing the exact event or confrontation unfolding)",
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
    try:
        return json.loads(cleaned)
    except Exception:
        fixed = re.sub(r",\s*([\}\]])", r"\1", cleaned)
        return json.loads(fixed)


def _get_gemini_keys() -> List[str]:
    keys: List[str] = []
    for env_k in ("GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3", "GEMINI_API_KEY_4", "GEMINI_API_KEY_5"):
        v = os.environ.get(env_k, "").strip()
        if v and v not in keys:
            keys.append(v)
    return keys


def _get_groq_keys(priority_key: str = "") -> List[str]:
    keys: List[str] = []
    if priority_key and priority_key.strip():
        keys.append(priority_key.strip())
    for k in ("GROQ_API_KEY", "GROQ_API_KEY_1", "GROQ_API_KEY_2", "GROQ_API_KEY_3", "GROQ_API_KEY_4", "GROQ_API_KEY_5"):
        v = os.environ.get(k, "").strip()
        if v and v not in keys:
            keys.append(v)
    return keys


def _get_xkiro_keys() -> List[str]:
    keys: List[str] = []
    for k in [f"XKIRO_KEY_{i}" for i in range(1, 8)] + ["XKIRO_API_KEY"]:
        v = os.environ.get(k, "").strip()
        if v and v not in keys:
            keys.append(v)
    return keys


def _groq_json(api_key: str, sys_prompt: str, usr_prompt: str, max_tokens: int = 7500) -> Dict[str, Any]:
    last_err: Any = None

    # الطبقة الأولى الفائقة: تدوير مفاتيح Groq الخمسة بمعدل استجابة < 1 ثانية وحصة 72,000 طلب يومياً
    groq_keys = _get_groq_keys(api_key)
    for g_idx, g_key in enumerate(groq_keys):
        headers = {"Authorization": f"Bearer {g_key}", "Content-Type": "application/json"}
        for cur_model in PREFERRED_MODELS:
            try:
                payload: Dict[str, Any] = {
                    "model": cur_model,
                    "messages": [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": usr_prompt},
                    ],
                    "temperature": 0.80,
                    "max_tokens": max(max_tokens, 7500),
                    "response_format": {"type": "json_object"},
                }
                resp = requests.post(f"{GROQ_BASE}/chat/completions", headers=headers, json=payload, timeout=60)
                if resp.status_code == 429:
                    print(f"[Groq JSON] المفتاح #{g_idx + 1} مع الموديل {cur_model} وصل للحد (429) — تدوير المفتاح...", flush=True)
                    break
                if resp.status_code != 200:
                    payload.pop("response_format", None)
                    resp = requests.post(f"{GROQ_BASE}/chat/completions", headers=headers, json=payload, timeout=60)
                    if resp.status_code == 429:
                        break
                if resp.status_code == 200:
                    msg_content = (resp.json()["choices"][0]["message"].get("content") or "").strip()
                    if msg_content:
                        return _extract_json(msg_content)
            except Exception as exc:
                last_err = exc
                continue

    # الطبقة الثانية الاحتياطية: مفاتيح Gemini الخمسة
    gem_keys = _get_gemini_keys()
    for gi, gkey in enumerate(gem_keys):
        mdl = GEMINI_JSON_MODELS[gi % len(GEMINI_JSON_MODELS)]
        try:
            g_url = f"https://generativelanguage.googleapis.com/v1beta/models/{mdl}:generateContent?key={gkey}"
            g_payload = {
                "systemInstruction": {"parts": [{"text": sys_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": usr_prompt}]}],
                "generationConfig": {
                    "temperature": 0.82,
                    "maxOutputTokens": max(max_tokens, 8192),
                    "responseMimeType": "application/json",
                },
            }
            gr = requests.post(g_url, json=g_payload, timeout=60)
            if gr.status_code == 429:
                last_err = RuntimeError(f"Gemini key #{gi + 1} rate-limited (HTTP 429)")
                continue
            if gr.status_code == 200:
                cands = gr.json().get("candidates") or []
                if cands:
                    parts = cands[0].get("content", {}).get("parts") or []
                    txt_chunks = [p.get("text", "") for p in parts if not p.get("thought") and p.get("text")]
                    raw_txt = "\n".join(txt_chunks).strip()
                    if raw_txt:
                        return _extract_json(raw_txt)
        except Exception as exc:
            last_err = exc

    # الطبقة الثالثة الاحتياطية: مفاتيح XKiro السبعة
    xkiro_keys = _get_xkiro_keys()
    xkiro_models = ["mistralai/ministral-14b", "sensenova/sensenova-6.8-flash-lite", "cohere/aya-vision-32b"]
    for xk_idx, xk_key in enumerate(xkiro_keys):
        x_headers = {"Authorization": f"Bearer {xk_key}", "Content-Type": "application/json"}
        for xmdl in xkiro_models:
            try:
                x_payload = {
                    "model": xmdl,
                    "messages": [
                        {"role": "system", "content": sys_prompt + "\nReturn strictly JSON format."},
                        {"role": "user", "content": usr_prompt},
                    ],
                    "temperature": 0.7,
                }
                xr = requests.post("https://api.xkiro.com/v1/chat/completions", headers=x_headers, json=x_payload, timeout=60)
                if xr.status_code == 200:
                    content = xr.json()["choices"][0]["message"].get("content", "")
                    if content:
                        return _extract_json(content)
            except Exception as exc:
                last_err = exc

    # الطبقة الرابعة الاحتياطية: Hugging Face Serverless Router
    hf_tokens = [os.environ.get(f"HF_TOKEN_{i}", "") for i in range(1, 11)] + [os.environ.get("HF_TOKEN", "")]
    hf_tokens = [t.strip() for t in hf_tokens if t.strip()]
    for hf_t in hf_tokens:
        try:
            hf_headers = {"Authorization": f"Bearer {hf_t}", "Content-Type": "application/json"}
            hf_payload = {
                "model": "Qwen/Qwen2.5-72B-Instruct",
                "messages": [
                    {"role": "system", "content": sys_prompt + "\nRespond with valid JSON only."},
                    {"role": "user", "content": usr_prompt},
                ],
                "max_tokens": 4096,
                "temperature": 0.7,
            }
            hr = requests.post("https://api-inference.huggingface.co/v1/chat/completions", headers=hf_headers, json=hf_payload, timeout=60)
            if hr.status_code == 200:
                h_content = hr.json()["choices"][0]["message"].get("content", "")
                if h_content:
                    return _extract_json(h_content)
        except Exception as exc:
            last_err = exc

    raise RuntimeError(f"LLM JSON generation failed across all providers: {last_err}")


def _sanitize_modest_action_prompt(p: str) -> str:
    banned_patterns = [
        r"\bno\s+hijab\b", r"\bwithout\s+hijab\b", r"\bhijab\b", r"\bheadscarf\b", r"\bniqab\b",
        r"\bsleeveless\b", r"\btank\s*top\b", r"\bstrap\s*top\b", r"\bcamisole\b", r"\bcrop\s*top\b",
        r"\bcleavage\b", r"\blow[- ]cut\b", r"\bv[- ]neck\b", r"\bopen\s+blazer\b", r"\bblouse\b",
        r"\blingerie\b", r"\bbikini\b", r"\bunderwear\b",
        r"\bseductive\b", r"\bglamour\b", r"\bsensual\b", r"\bportrait\s+close[- ]up\b",
    ]
    out = p
    for pat in banned_patterns:
        out = re.sub(pat, "", out, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", out).strip(" ,.-")


def scout_viral_trends_and_angles(
    channel_cfg: Dict[str, Any],
    api_key: str,
    used_topics: List[str],
) -> Dict[str, Any]:
    """
    محرك استكشاف التريندات والميكانيكيات الفيروسية الأكثر بحثاً على يوتيوب:
    يقوم بتحليل أكثر زوايا القصص والعناوين التي تحقق ملايين المشاهدات واقتطاف أفضل تركيبة نفسية
    تضمن أعلى نسبة نقر (CTR) وأطول مدة احتفاظ بالمشاهد (Retention) قبل صياغة السيناريو!
    """
    lang = channel_cfg.get("language", "ar")
    brand = channel_cfg.get("brand_name", "")
    pillars = channel_cfg.get("constitution", {}).get("approved_pillars", [])
    pillars_labels = [p.get("label", "") for p in pillars]

    if lang == "ar":
        sys_p = "أنت خبير خوارزميات يوتيوب وصانع المحتوى الفيروسي الأقوى في الشرق الأوسط (متخصص في قصص الجريمة والغموض والتحقيقات النفسية الواقعية مثل سامح سند وبيسوهات ومستر بالن)."
        usr_p = f"""
حلل أحدث صيحات البحث الفيروسي وميكانيكيات التفاعل الأعلى مشاهدة على يوتيوب حالياً.
القناة: {brand}
التصنيفات المعتمدة المتنوعة للقناة: {json.dumps(pillars_labels, ensure_ascii=False)}
المواضيع التي استهلكت مؤخراً (ممنوع تكرارها): {used_topics[-15:]}

المطلوب استكشاف زاوية قصة فيروسية مبتكرة وغير مسبوقة تكسر النمطية والتكرار تماماً (يمكن أن تكون: غموض نفسي معقد، أو لغز تاريخي غامض، أو عملية احتيال وذكاء ساخر مذهلة، أو قصة نجاة مستحيلة، أو واقعة غريبة لا يصدقها عقل)، وصياغة عناصر الجذب الفيروسي:

أخرج JSON فقط:
{{
  "trend_angle": "وصف الزاوية الفيروسية الاستثنائية الأكثر إثارة للفضول",
  "high_ctr_hook_title": "عنوان يوتيوب فضولي عالي النقر والنفاذ في خوارزميات الاقتراح",
  "thumbnail_shock_element": "عنصر الصدمة البصري الرئيسي للغلاف الذي يجبر المشاهد على التوقف والنقر",
  "curiosity_gap_secret": "السر المدفون أو المفارقة العقلية التي لا يمكن معرفتها إلا بمشاهدة الحلقة للنهاية"
}}
"""
    else:
        sys_p = "You are an elite YouTube Algorithm Director specializing in viral crime, mystery, and thriller content (like MrBallen and Coffeehouse Crime)."
        usr_p = f"""
Analyze current high-CTR YouTube search trends and viral triggers in true crime, psychological suspense, and unbelievable mysteries.
Channel: {brand}
Recent used topics (do not repeat): {used_topics[-15:]}

Discover an unprecedented viral story angle that shatters monotony (psychological twist, bizarre survival, high-IQ heist, or forgotten historical enigma).

Return valid JSON only:
{{
  "trend_angle": "The unique, irresistible viral curiosity angle",
  "high_ctr_hook_title": "High-CTR search-optimized YouTube title",
  "thumbnail_shock_element": "The shocking visual focal hook for the thumbnail",
  "curiosity_gap_secret": "The jaw-dropping twist or hidden revelation"
}}
"""
    try:
        res = _groq_json(api_key, sys_p, usr_p, max_tokens=1200)
        if res and res.get("trend_angle"):
            return res
    except Exception as exc:
        print(f"[{channel_cfg.get('id')}][SCOUT-WARN] تعذر استكشاف التريند مؤقتاً ({exc})", flush=True)

    return {
        "trend_angle": "غموض نفسي واقعي وتحقيق غير مسبوق في سر اختفاء مفاجئ",
        "high_ctr_hook_title": "سر الحادث الذي صدم الجميع | القصة الكاملة",
        "thumbnail_shock_element": "باب مفتوح في الظلام مع ضوء ساطع وبطل مصدوم من المفاجأة",
        "curiosity_gap_secret": "خيط صغير متناقض في الأدلة يقلب القضية رأساً على عقب"
    }


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

    director_state = load_director_state()
    chosen_pillar_id = "default_pillar"
    chosen_pillar_label = ""
    director_brief = ""
    selected_flavor = ""
    if (channel_cfg.get("constitution") or {}).get("approved_pillars"):
        try:
            strategy = select_next_episode_strategy(channel_cfg, memory, director_state)
            pillar_obj = strategy["pillar"]
            chosen_pillar_id = str(pillar_obj["id"])
            chosen_pillar_label = str(pillar_obj.get("label", chosen_pillar_id))
            selected_flavor = str(pillar_obj["prompt_seed"])
            director_brief = build_director_prompt_injection(channel_cfg, strategy)
            print(
                f"[{cid}][AI-DIRECTOR] وضع التحسين={strategy['mode']} | الركيزة المختارة=«{chosen_pillar_label}» ({chosen_pillar_id})",
                flush=True,
            )
        except Exception as dir_exc:
            print(f"[{cid}][AI-DIRECTOR-WARN] استخدام التناوب الافتراضي الآمن ({dir_exc})", flush=True)

    # استكشاف التريندات الفيروسية الأكثر بحثاً قبل بناء أي حلقة
    viral_scout = scout_viral_trends_and_angles(channel_cfg, api_key, used)
    print(f"[{cid}][VIRAL-SCOUT] 🔥 استكشاف التريند الفيروسي: {viral_scout.get('trend_angle', '')[:80]}...", flush=True)

    if lang == "ar":
        if niche == "eg_conan_detective":
            flavor = selected_flavor or EG_CONAN_CASES[ep_count % len(EG_CONAN_CASES)]
            style_guide = (
                "أنتِ حكّاءة ألغاز وتحقيقات مصرية محترفة جداً (بأسلوب سامح سند وبيسوهات والمحقق كونان)، تتكلمين بالعامية المصرية القاهرية الحقيقية الدافئة 100%. "
                "ممنوع نهائياً الكلمات الفصحى المترجمة مثل (التي، الذي، حيث، فندق مهجور، رمز ميكانيكي، الانقلاب القاتل، الخاتمة النفسية)! "
                "اكتبي باللهجة اللي بنتكلم بيها في القاهرة بجد وبنفس بشري طبيعي مليان فواصل تشويق قصيرة `..` وتفاصيل واقعية ملموسة."
            )
        else:
            flavor = selected_flavor or EG_REALISTIC_THRILLERS[ep_count % len(EG_REALISTIC_THRILLERS)]
            style_guide = (
                "أنتِ حكّاءة إثارة نفسية مصرية بارعة جداً (نفس روح أقوى حلقات سامح سند وبيسوهات)، تتكلمين بالعامية المصرية القاهرية الحقيقية السلسة 100%. "
                "ممنوع نهائياً الخيال الرخيص أو الأشباح أو الجمل المترجمة الركيكة! "
                "القصة لازم تكون واقعية جداً لدرجة إن المستمع يحس إنها ممكن تحصله الليلة في شقته أو موبايله، مع مقدمة نارية في أول 25 ثانية تخليه مستحيل يقفل قبل ما يعرف النهاية."
            )

        blueprint_prompt = f"""
{director_brief}

تحليل الاستكشاف الفيروسي المسبق لليوم (Viral Intelligence):
- زاوية الصدمة الفيروسية: {viral_scout.get('trend_angle')}
- مقترح العنوان الأكثر نقراً: {viral_scout.get('high_ctr_hook_title')}
- عنصر الغلاف الفيروسي: {viral_scout.get('thumbnail_shock_element')}
- اللغز المحير: {viral_scout.get('curiosity_gap_secret')}

الأفكار المستعملة سابقاً (ممنوع تكرارها نهائياً): {used}

صمّمي حلقة إثارة نفسية واقعية / تحقيق ذكي لا يمكن التوقف عن سماعها (+16 دقيقة، تبدأ بمقدمة تشويقية نارية + 12 مشهداً متصلة كفيلم سينمائي متكامل) من فئة:
«{flavor}»

قواعد الخوارزميات والجذب النفسي لعام 2026:
1. **المقدمة التشويقية الإجبارية (`teaser_intro` — 80 إلى 95 كلمة بالعامية المصرية بدون تشكيل)**:
   - تبدأ في الثانية صفر بومضة نارية من أخطر لحظة صادمة قرب نهاية القصة (بدون حرق الحل!) وتطابق وعد العنوان والغلاف تماماً.
   - ثم تطرح اللغز المستحيل وتوعد المستمع بمفاجأة في آخر دقيقتين تقلب كل توقعاته، وتختم بـ: «ركز معايا في كل تفصيلة من أول ثانية.. لأن النهاية مستحيل تخطر على بالك.. يلا نبدأ الحكاية من أولها!».
2. **مقدمات خطف الـ 4 شورتس اليومية**:
   - `short_1_hook_intro` و `short_2_hook_intro`: جملة خطف نارية في أول 4 ثوانٍ (15–20 كلمة بالعامية المصرية) للشورتين العميقين.
   - `short_3_hook_intro` و `short_4_hook_intro`: جملة صدمة خاطفة سريعة جداً في أول 3 ثوانٍ (10–13 كلمة بالعامية المصرية) للشورتين الخاطفين (<55 ثانية).
   - `short_1_banner_top` إلى `short_4_banner_top`: شريط عنوان علوي من **5 إلى 7 كلمات فقط** يوقف المشاهد الكاتم للصوت في الثانية صفر!
   - `short_1_debate_cta` إلى `short_4_debate_cta`: دعوة تفاعل بشرية ذكية وطبيعية تحث المشاهد على الاشتراك واللايك وكتابة رأيه في التعليقات بدون أي أسئلة روبوتية!
3. عنوان اليوتيوب (`youtube_title`): **عنوان يجمع الإثارة العالية + كلمات البحث الأكثر طلباً على يوتيوب** (ينتهي بـ `| قصة واقعية كاملة` أو `| لغز جريمة محير` — أقل من 85 حرفاً بدون حرق الحل) + نص الغلاف المصغّر (`thumbnail_hook_text`: **جملة صادمة مكتملة من 3 أو 4 كلمات فقط**).
4. نهاية **المشهد 2** = ذروة أدرينالين أولى (الشورت 1). نهاية **المشهد 5** = صدمة الدليل الغريب (الشورت الخاطف 3). نهاية **المشهد 7** = ذروة منتصف القصة (الشورت 2). نهاية **المشهد 10** = لحظة المواجهة قبل كشف الحل (الشورت الخاطف 4).

أخرجي JSON صالح بالهيكل التالي:
{{
  "topic_key": "ملخص فريد 6 كلمات للفكرة الواقعية",
  "youtube_title": "عنوان يوتيوب ناري يدمج كلمة بحث قوية مثل: قصة واقعية كاملة / لغز جريمة غامض (أقل من 85 حرفاً)",
  "thumbnail_hook_text": "جملة صادمة مكتملة من 3 أو 4 كلمات للغلاف",
  "thumbnail_banner_top": "مقتطف من ذروة الأحداث — تابع للنهاية!",
  "thumbnail_prompt": "Hyper-realistic 8k 35mm thriller movie frame, 16:9 widescreen single continuous camera shot: a shocked protagonist illuminated by eerie atmospheric door glow and dramatic crimson rim light in a dark mystery hallway at night, rich cinematic contrast, ARRI Alexa cinema still, zero text, zero letters, zero logos",
  "teaser_intro": "النص الكامل للمقدمة التشويقية النارية (80–95 كلمة بالعامية المصرية الحية مع فواصل .. بدون حرق الحل، تجبر المشاهد يكمل للنهاية)",
  "short_1_hook_intro": "جملة خطف نارية في أول 4 ثوانٍ للشورت الأول (16 كلمة بالعامية المصرية)",
  "short_2_hook_intro": "جملة خطف نارية في أول 4 ثوانٍ للشورت الثاني (16 كلمة بالعامية المصرية)",
  "short_3_hook_intro": "جملة صدمة خاطفة في أول 3 ثوانٍ للشورت الثالث السريع (11 كلمة بالعامية المصرية)",
  "short_4_hook_intro": "جملة صدمة خاطفة في أول 3 ثوانٍ للشورت الرابع السريع (11 كلمة بالعامية المصرية)",
  "short_1_banner_top": "شريط عنوان علوي صادم من 6 كلمات للشورت الأول",
  "short_2_banner_top": "شريط عنوان علوي صادم من 6 كلمات للشورت الثاني",
  "short_3_banner_top": "شريط عنوان علوي صادم من 6 كلمات للشورت الثالث",
  "short_4_banner_top": "شريط عنوان علوي صادم من 6 كلمات للشورت الرابع",
  "short_1_debate_cta": "لو عجبك المقطع متنساش تشترك في القناة وتعمل لايك علشان تشوف الحكايات الجاية أول بأول.. وقولنا رأيك وتوقعك في التعليقات تحت!",
  "short_2_debate_cta": "اشترك في القناة وفعل الجرس واعمل لايك علشان تتابع باقي الحكاية كاملة أول بأول.. ومستني رأيك وتوقعك في التعليقات!",
  "short_3_debate_cta": "دوس لايك واشترك في القناة علشان حكاياتنا الجديدة متفوتكش كل يوم.. وقولنا في التعليقات حسيت بإيه!",
  "short_4_debate_cta": "اشترك في القناة واعمل لايك عشان تدعمنا في نشر حكايات أكتر.. واكتب توقعك للي حصل في الكومنتات تحت!",
  "short_1_title": "عنوان ناري للشورت الأول يخطف الانتباه فوراً + #shorts #قصص_واقعية #غموض",
  "short_2_title": "عنوان ناري مختلف للشورت الثاني من ذروة منتصف القصة + #shorts #تشويق #حكايات",
  "short_3_title": "عنوان صاعق قصير للشورت الثالث السريع + #shorts #قصة_حقيقية #مفاجأة",
  "short_4_title": "عنوان لغز محير للشورت الرابع السريع + #shorts #الغاز #تشويق",
  "seo_hook_2lines": "سطران ناريان يظهران في أول سطرين بالوصف قبل زر عرض المزيد لجذب المشاهد وخوارزمية البحث فوراً",
  "seo_synopsis": "فقرة تشويقية غنية من 4 جمل تدمج طبيعياً أقوى كلمات البحث (قصص واقعية مثيرة، غموض نفسي، حكايات مصرية تحبس الأنفاس، ألغاز وتحقيقات)",
  "engagement_question": "سؤال تحدي ذكي للمشاهدين يربط بتفصيلة في الحلقة ويدفعهم لكتابة توقعاتهم في التعليقات",
  "seo_tags": ["تاج 1", "تاج 2", "تاج 3", "تاج 4", "تاج 5", "تاج 6", "تاج 7", "تاج 8"],
  "hashtags": "#دفتر_راوي #قصص_واقعية #غموض_نفسي #حكايات_مصرية #قصص_مثيرة",
  "character_visual_anchor": "Consistent realistic English visual description of protagonist in modest everyday attire (e.g. a 30-year-old Egyptian man wearing a dark zipped jacket over a grey crewneck sweater, OR if female: uncovered shoulder-length dark hair wearing a closed black high-neck turtleneck sweater and dark winter coat—never revealing clothes and never write the word hijab)",
  "scenes_outline": [
    {{"scene_num": 1, "scene_title": "عنوان فضولي للمشهد 1", "summary": "بداية الحكاية من أول لحظة بتفاصيل واقعية ملموسة"}},
    {{"scene_num": 2, "scene_title": "عنوان فضولي للمشهد 2", "summary": "تصاعد حابس للأنفاس ينتهي عند قمة الذروة النارية الأولى (Peak Climax #1)"}},
    {{"scene_num": 3, "scene_title": "عنوان فضولي للمشهد 3", "summary": "ما ظهر فور فتح الباب/الرسالة وبداية الخيط الأخطر"}},
    {{"scene_num": 4, "scene_title": "عنوان فضولي للمشهد 4", "summary": "أول مواجهة وتناقض مريب + جسر تشويق يعيد شد الانتباه"}},
    {{"scene_num": 5, "scene_title": "عنوان فضولي للمشهد 5", "summary": "فحص كاميرا أو إيصال أو تسجيل واكتشاف تفصيلة مستحيلة"}},
    {{"scene_num": 6, "scene_title": "عنوان فضولي للمشهد 6", "summary": "نصب فخ ذكي في نص الليل للتأكد من الشك"}},
    {{"scene_num": 7, "scene_title": "عنوان فضولي للمشهد 7", "summary": "تصاعد رهيب يقف قبل كشف الصدمة الكبرى بثانية واحدة (Peak Climax #2)"}},
    {{"scene_num": 8, "scene_title": "عنوان فضولي للمشهد 8", "summary": "انكشاف مفاجأة المنتصف التي تقلب كل التوقعات رأساً على عقب"}},
    {{"scene_num": 9, "scene_title": "عنوان فضولي للمشهد 9", "summary": "الخيط الخفي اللي بيربط كل التفاصيل ببعض"}},
    {{"scene_num": 10, "scene_title": "عنوان فضولي للمشهد 10", "summary": "الوصول للدليل المادي القاطع + جسر تشويق قبل المواجهة"}},
    {{"scene_num": 11, "scene_title": "عنوان فضولي للمشهد 11", "summary": "المواجهة الحاسمة وكشف الخطة خطوة بخطوة"}},
    {{"scene_num": 12, "scene_title": "عنوان فضولي للمشهد 12", "summary": "الحقيقة الكاملة المدهشة وإجابة السؤال المفتوح من المقدمة"}}
  ]
}}
"""
    else:
        flavor = selected_flavor or (
            EN_DETECTIVE_CASES[ep_count % len(EN_DETECTIVE_CASES)]
            if niche == "en_detective_mystery"
            else EN_REALISTIC_THRILLERS[ep_count % len(EN_REALISTIC_THRILLERS)]
        )
        style_guide = (
            "You are an elite psychological suspense & mystery storyteller in the exact style of MrBallen's most viral realistic episodes. "
            "Open every episode with an explosive 25-second Cold-Open Climax Teaser that matches the title/thumbnail promise and forces viewers to watch until the final minute."
        )
        blueprint_prompt = f"""
{director_brief}

Pre-Scouted YouTube Viral Intelligence:
- Viral Angle: {viral_scout.get('trend_angle')}
- Suggested High-CTR Hook Title: {viral_scout.get('high_ctr_hook_title')}
- High-Tension Thumbnail Element: {viral_scout.get('thumbnail_shock_element')}
- Core Psychological Mystery: {viral_scout.get('curiosity_gap_secret')}

Avoid all previously used premises: {used}

Design a hyper-realistic, unputdownable 16-minute continuous movie episode (25-second Cold-Open Teaser Intro + 12 Scenes) for:
"{flavor}"

Return exact valid JSON:
{{
  "topic_key": "6-word unique realistic premise",
  "youtube_title": "High-CTR + High-Search YouTube title ending with '| True Mystery Story' or '| Locked-Room Detective Mystery' (under 85 chars, zero spoilers)",
  "thumbnail_hook_text": "Complete 3-to-4 word shocking hook (e.g. IT CAME FROM INSIDE! / CHECK THE REFLECTION!)",
  "thumbnail_banner_top": "CLIMAX TEASER — WATCH TILL THE END!",
  "thumbnail_prompt": "Hyper-realistic 8k 35mm thriller movie frame, 16:9 widescreen single continuous camera shot: shocked protagonist centered in the upper middle of the frame illuminated by vivid electric-blue phone glow and crimson rim light, atmospheric lit hallway behind them, rich cinematic contrast, ARRI Alexa cinema film still, zero text, zero letters, zero logos",
  "teaser_intro": "85-word breathless Cold-Open Flash-Forward Teaser Intro hinting at the most shocking climax moment without spoiling the answer, ending with: Stay with me until the very last minute—let's rewind to how this nightmare started...",
  "short_1_hook_intro": "16-word explosive 3-second opening hook question/paradox for Deep Short #1",
  "short_2_hook_intro": "16-word explosive 3-second opening hook question/paradox for Deep Short #2",
  "short_3_hook_intro": "11-word punchy instant shock hook for Fast Viral Short #3",
  "short_4_hook_intro": "11-word punchy instant shock hook for Fast Viral Short #4",
  "short_1_banner_top": "6-word shocking uppercase top hook banner #1",
  "short_2_banner_top": "6-word shocking uppercase top hook banner #2",
  "short_3_banner_top": "6-word shocking uppercase top hook banner #3",
  "short_4_banner_top": "6-word shocking uppercase top hook banner #4",
  "short_1_debate_cta": "Make sure to subscribe and drop a like so you never miss our next psychological thriller.. and share your thoughts in the comments below!",
  "short_2_debate_cta": "Hit that subscribe button and leave a like to catch the full story.. what would you have done? Let us know down in the comments!",
  "short_3_debate_cta": "Subscribe for more chilling stories and hit like if this gave you goosebumps.. drop your thoughts in the comments!",
  "short_4_debate_cta": "Don't forget to like and subscribe to stay tuned for our next episode.. leave your reaction down in the comments!",
  "short_1_title": "Viral hook title #1 + #shorts #storytime #thriller",
  "short_2_title": "Viral mid-story climax title #2 + #shorts #mystery #plotwist",
  "short_3_title": "Fast viral cliffhanger title #3 + #shorts #truestory #creepy",
  "short_4_title": "Detective clue cliffhanger title #4 + #shorts #whodunit #mystery",
  "seo_hook_2lines": "Gripping 2-line hook above YouTube Show More fold packed with curiosity and search keywords",
  "seo_synopsis": "4-sentence SEO-rich story teaser weaving high-retention mystery/storytime keywords naturally",
  "engagement_question": "Specific clue/timestamp debate question compelling viewers to comment their theory",
  "seo_tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"],
  "hashtags": "#storytime #mystery #thriller #plotwist #truestories",
  "character_visual_anchor": "Consistent realistic protagonist English visual description in modest everyday attire (e.g. 30-year-old man in charcoal zipped jacket over crewneck sweater, OR if female: uncovered wavy brown hair wearing a closed navy turtleneck sweater and zipped winter coat—never revealing clothes and never write the word hijab)",
  "scenes_outline": [
    {{"scene_num": 1, "scene_title": "Curiosity Scene 1 Title", "summary": "How the night began with concrete everyday detail"}},
    {{"scene_num": 2, "scene_title": "Curiosity Scene 2 Title", "summary": "Deep escalation ending on Explosive Peak Climax #1"}},
    {{"scene_num": 3, "scene_title": "Curiosity Scene 3 Title", "summary": "Immediate discovery behind Peak #1"}},
    {{"scene_num": 4, "scene_title": "Curiosity Scene 4 Title", "summary": "First suspect contradiction + retention bridge"}},
    {{"scene_num": 5, "scene_title": "Curiosity Scene 5 Title", "summary": "Timestamp/camera physical anomaly"}},
    {{"scene_num": 6, "scene_title": "Curiosity Scene 6 Title", "summary": "Midnight verification trap"}},
    {{"scene_num": 7, "scene_title": "Curiosity Scene 7 Title", "summary": "Breathless buildup cutting 1s before mid-movie twist (Peak Climax #2)"}},
    {{"scene_num": 8, "scene_title": "Curiosity Scene 8 Title", "summary": "Mid-point twist flips every assumption"}},
    {{"scene_num": 9, "scene_title": "Curiosity Scene 9 Title", "summary": "Hidden motive & timeline connection"}},
    {{"scene_num": 10, "scene_title": "Curiosity Scene 10 Title", "summary": "Decisive physical clue + final retention bridge"}},
    {{"scene_num": 11, "scene_title": "Curiosity Scene 11 Title", "summary": "High-stakes confrontation"}},
    {{"scene_num": 12, "scene_title": "Curiosity Scene 12 Title", "summary": "Full mind-blowing payoff answering the teaser"}}
  ]
}}
"""

    plan: Dict[str, Any] = {}
    prompt_to_send = blueprint_prompt
    for const_attempt in range(3):
        plan = _groq_json(api_key, style_guide, prompt_to_send, max_tokens=5600)
        check_blob = " \n ".join([
            str(plan.get("youtube_title") or ""),
            str(plan.get("teaser_intro") or ""),
            str(plan.get("short_1_title") or ""),
            str(plan.get("short_3_title") or ""),
            json.dumps(plan.get("scenes_outline") or [], ensure_ascii=False),
        ])
        is_valid, reason = validate_text_against_constitution(check_blob, channel_cfg, require_language_match=True)
        if is_valid:
            break
        print(f"[{cid}][CONSTITUTION-GATE] رفض مسودة مخالفة لدستور القناة ({reason}) — إعادة التوليد #{const_attempt + 1}...", flush=True)
        prompt_to_send = (
            f"CRITICAL CONSTITUTION CORRECTION: Your previous draft violated '{reason}'. "
            "Stay 100% strictly inside the realistic channel identity with zero forbidden drift words!\n\n"
            + blueprint_prompt
        )
    char_anchor = str(
        plan.get("character_visual_anchor")
        or "a 29-year-old protagonist wearing a dark navy zip hoodie over a charcoal t-shirt in a realistic modern apartment"
    ).strip()

    teaser_intro = re.sub(r"[\u064B-\u065F\u0670]", "", str(plan.get("teaser_intro") or "")).strip()
    if len(teaser_intro.split()) < 25:
        if lang == "ar":
            teaser_intro = (
                f"تخيل إنك تصحى في نص الليل على تفصيلة مستحيل تحصل في الواقع.. {plan.get('youtube_title', '')}.. "
                "كل دليل يظهر قدامك يكذّب اللي قبله.. وغلطة واحدة صغيرة في آخر دقيقتين هي اللي قلبت الترابيزة وكشفت الحقيقة الصادمة.. "
                "ركز معايا في كل ثانية لحد النهاية.. ويلا نبدأ الحكاية من أولها!"
            )
        else:
            teaser_intro = (
                f"Imagine waking up in the dead of night to one detail that shouldn't physically exist—{plan.get('youtube_title', '')}... "
                "Every clue contradicted the last until one tiny mistake in the final two minutes exposed the shocking truth. "
                "Stay with me until the very end—let's start right from the beginning."
            )

    outlines = (plan.get("scenes_outline") or [])[:12]
    while len(outlines) < 12:
        idx = len(outlines) + 1
        outlines.append({"scene_num": idx, "scene_title": f"المشهد {idx}" if lang == "ar" else f"Scene {idx}", "summary": "Escalating realistic suspense"})

    scenes_full: List[Dict[str, Any]] = []
    prev_tail = teaser_intro[-160:]
    for batch_idx in range(3):
        batch_slice = outlines[batch_idx * 4 : (batch_idx + 1) * 4]
        s_nums = [int(x["scene_num"]) for x in batch_slice]

        if lang == "ar":
            batch_prompt = f"""
عنوان الحلقة: {plan.get('youtube_title')}
المقدمة التشويقية التي سمعها المشاهد للتو: "{teaser_intro}"
المخطط الكامل: {json.dumps(outlines, ensure_ascii=False)}
نهاية المقطع السابق (كمّلي بعدها بسلاسة كحكاية متصلة): "{prev_tail}"

اكتبي السرد الصوتي الكامل للمشاهد الأربعة التالية: {json.dumps(batch_slice, ensure_ascii=False)}

قواعد الأداء الصوتي والاحتفاظ بالمشاهد (Retention Engineering):
1. الطول لكل مشهد منفرد: **بين 225 و 260 كلمة كاملة** بالعامية المصرية القاهرية الطبيعية 100% بدون أي تشكيل أو شدّات.
2. ممنوع أي كلمة فصحى أو مترجمة (التي، الذي، حيث، فندق مهجور، رمز ميكانيكي)! احكي بالعامية القاهرية الحية السلسة مع فواصل تنفس قصيرة `..`.
3. في المشهد 4 والمشهد 10 ضعي **جسر تشويق طبيعي** يشد انتباه المشاهد عشان ميكسلش أو يخرج (مثلاً: «بس استنى.. لأن اللي حصل بعد دقيقتين بالظبط هو اللي قلب الموازين كلها..»).
4. لو المشهد رقم **2** موجود هنا: اختميه في قمة الذروة النارية المعلقة! ولو المشهد رقم **7** موجود هنا: اختميه قبل انكشاف مفاجأة المنتصف بثانية واحدة!
5. في المشهد رقم **11** أو **12** (قرب نهاية القصة): ادمجي في سياق الكلام جملة تفاعل بشرية دافئة جداً: «لو وصلت معايا للنقطة دي من الحكاية وعجبتك.. متنساش تدوس لايك وتشترك في القناة وتفعل الجرس علشان الحكايات الجاية متفوتكش.. ودلوقتي جه الوقت اللي نكشف فيه السر اللي دوّخ الجميع..» واختمي المشهد 12 بدعوة حماسية لكتابة آرائهم وتوقعاتهم في التعليقات!

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
Cold-Open Teaser just heard: "{teaser_intro}"
Full Outline: {json.dumps(outlines)}
Previous tail (continue seamlessly): "{prev_tail}"

Write the full spoken narration for these 4 scenes: {json.dumps(batch_slice)}

Retention Rules:
1. Length per scene: **260 to 295 words** of hyper-realistic, conversational spoken American storytelling with subtle `...` pauses.
2. Add a natural spoken retention bridge in Scene 4 and Scene 10 ("But hold on—because what showed up two minutes later changed everything...").
3. End Scene 2 on Peak Climax #1, and end Scene 7 one heartbeat before the mid-story twist!
4. In Scene 11 or 12: Naturally weave in a warm, direct spoken CTA: 'If you made it this far and enjoyed the story, don't forget to hit like and subscribe with notifications on so you catch our upcoming cases.. now let's reveal the shocking truth..' and invite viewer theories in the comments at the very end!

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
    if chosen_pillar_id != "default_pillar":
        memory[cid]["last_pillar_id"] = chosen_pillar_id
        tp_map = memory[cid].setdefault("title_pillar_map", {})
        clean_key = re.sub(r"#\S+", "", yt_title).strip(" -—|")[:48]
        if clean_key:
            tp_map[clean_key] = chosen_pillar_id
        if len(tp_map) > 80:
            keep_keys = list(tp_map.keys())[-80:]
            memory[cid]["title_pillar_map"] = {k: tp_map[k] for k in keep_keys}
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
        "teaser_banner_text": str(plan.get("thumbnail_banner_top") or ("مقتطف من ذروة الأحداث — تابع للنهاية!" if lang == "ar" else "CLIMAX PREVIEW — WATCH TILL THE END!")).strip(),
        "thumbnail_prompt": _sanitize_modest_action_prompt(
            str(
                plan.get("thumbnail_prompt")
                or f"Dramatic 16:9 thriller movie still: shocked {char_anchor} wearing modest buttoned jacket on right third looking at glowing blue smartphone screen, shadowy open apartment door behind, dark clean space on left third, 35mm cinema lighting"
            )
        ),
        "teaser_intro": teaser_intro,
        "short_1_hook_intro": re.sub(r"[\u064B-\u065F\u0670]", "", str(plan.get("short_1_hook_intro") or "")).strip(),
        "short_2_hook_intro": re.sub(r"[\u064B-\u065F\u0670]", "", str(plan.get("short_2_hook_intro") or "")).strip(),
        "short_3_hook_intro": re.sub(r"[\u064B-\u065F\u0670]", "", str(plan.get("short_3_hook_intro") or "")).strip(),
        "short_4_hook_intro": re.sub(r"[\u064B-\u065F\u0670]", "", str(plan.get("short_4_hook_intro") or "")).strip(),
        "short_1_banner_top": re.sub(r"[\u064B-\u065F\u0670]", "", str(plan.get("short_1_banner_top") or "")).strip(),
        "short_2_banner_top": re.sub(r"[\u064B-\u065F\u0670]", "", str(plan.get("short_2_banner_top") or "")).strip(),
        "short_3_banner_top": re.sub(r"[\u064B-\u065F\u0670]", "", str(plan.get("short_3_banner_top") or "")).strip(),
        "short_4_banner_top": re.sub(r"[\u064B-\u065F\u0670]", "", str(plan.get("short_4_banner_top") or "")).strip(),
        "short_title": str(plan.get("short_1_title") or f"{yt_title[:58]} #shorts").strip(),
        "short_1_title": str(plan.get("short_1_title") or f"{yt_title[:58]} #shorts").strip(),
        "short_2_title": str(plan.get("short_2_title") or f"{yt_title[:52]} - الجزء الأخطر #shorts").strip(),
        "short_3_title": str(plan.get("short_3_title") or f"{yt_title[:52]} - صدمة غير متوقعة #shorts").strip(),
        "short_4_title": str(plan.get("short_4_title") or f"{yt_title[:52]} - الدليل المخفي #shorts").strip(),
        "seo_hook_2lines": str(plan.get("seo_hook_2lines") or yt_title).strip(),
        "seo_synopsis": str(plan.get("seo_synopsis") or "").strip(),
        "engagement_question": str(plan.get("engagement_question") or "").strip(),
        "seo_tags": combined_tags[:18],
        "hashtags": str(plan.get("hashtags") or "").strip(),
        "character_visual_anchor": _sanitize_modest_action_prompt(char_anchor),
        "scenes": scenes_full,
        "cta_spoken_1": re.sub(r"[\u064B-\u065F\u0670]", "", str(plan.get("short_1_debate_cta") or channel_cfg["cta_spoken_1"])).strip(),
        "cta_spoken_2": re.sub(r"[\u064B-\u065F\u0670]", "", str(plan.get("short_2_debate_cta") or channel_cfg["cta_spoken_2"])).strip(),
        "cta_spoken_3": re.sub(r"[\u064B-\u065F\u0670]", "", str(plan.get("short_3_debate_cta") or channel_cfg.get("cta_spoken_3") or channel_cfg["cta_spoken_1"])).strip(),
        "cta_spoken_4": re.sub(r"[\u064B-\u065F\u0670]", "", str(plan.get("short_4_debate_cta") or channel_cfg.get("cta_spoken_4") or channel_cfg["cta_spoken_2"])).strip(),
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
    يولّد لكل نافذة زمنية مشهداً سينمائياً يجسد الحدث/الموقف الفعلي المنطوق في تلك الثانية بالضبط:
    - الأشياء والأماكن والأفعال الحركية تأتي في أول الجملة (ليلتقطها النموذج البصري بدقة 100%).
    - ممنوع صور استعراض الوجوه أو صور السيدات العشوائية! كل لقطة تمثل ما يُحكى في الرواية بالضبط.
    - التزام صارم بملابس يومية محترمة ومحتشمة بدون حجاب (جاكيت/بليزر/قميص بأكمام عادية، صفر عري).
    """
    clean_anchor = _sanitize_modest_action_prompt(character_visual_anchor)
    sys_msg = (
        "You are an elite thriller movie storyboard director. Convert each spoken narration beat (`spoken`) into ONE vivid, "
        "concrete 28-38 word English cinema scene prompt depicting the EXACT physical event, action, object, or room situation happening in `spoken`.\n"
        "STRICT RULES:\n"
        "1. ACTION & SITUATION FIRST: Put the exact action, props, and setting in the VERY FIRST WORDS (e.g. 'Close-up of a hand holding a glowing smartphone showing a message at 3 AM beside a bedroom lamp...', 'Medium movie shot of a man in a navy jacket cautiously opening a wooden apartment door into a dim hallway...').\n"
        "2. STORY-FIRST COMPOSITION: Never generate generic face portraits or random women! At least 55% of shots must focus on story objects, clues, doors, phones, rooms, or wide scenes; avoid close-up faces and hands unless the spoken beat truly requires them.\n"
        "3. NATURAL HUMAN APPEARANCE: If a person is visible, use lifelike anatomy and natural body proportions, a coherent realistic face, natural eyes, and correctly formed hands; avoid extra/fused fingers, duplicated limbs, warped faces, or distorted teeth. Prefer medium-wide, profile, or over-the-shoulder framing when a close-up is not essential.\n"
        "4. MODEST NON-HIJAB EVERYDAY WARDROBE: Whenever any woman appears in the story, describe her with 'uncovered natural hair' wearing 'a closed high-neck turtleneck sweater or crewneck long-sleeve sweater and zipped winter coat'. NEVER write blazers, v-necks, sleeveless, straps, cleavage, or shorts, and NEVER write the word 'hijab' or 'headscarf'.\n"
        "5. Bright dramatic cinema lighting (warm lamp + cool window/screen light, never pitch black), photorealistic detail, zero text/letters."
    )

    prompts_out: List[str] = []
    batch_sz = 25
    for start_i in range(0, len(windows), batch_sz):
        chunk = windows[start_i : start_i + batch_sz]
        items_desc = [
            {
                "idx": k,
                "staging_mode": SCENE_STAGING_MODES[(start_i + k) % len(SCENE_STAGING_MODES)],
                "spoken": w.get("text", "")[:220],
            }
            for k, w in enumerate(chunk)
        ]
        usr_msg = f"""
Story Title: {story_title}
Main Character Reference (use ONLY when the character is actively performing an action in the beat): {clean_anchor}
Composition: {"Vertical 9:16 centered movie scene" if is_vertical else "Widescreen 16:9 movie scene"}

Write {len(chunk)} distinct 28-38 word English movie-scene prompts where EACH prompt illustrates the exact event/situation in `spoken` following `staging_mode`:
{json.dumps(items_desc, ensure_ascii=False)}

Return JSON only:
{{"prompts": ["prompt_0", "prompt_1", ...]}}
"""
        try:
            res = _groq_json(api_key, sys_msg, usr_msg, max_tokens=5000)
            got = res.get("prompts") or []
        except Exception:
            got = []

        for k, w in enumerate(chunk):
            raw_p = _sanitize_modest_action_prompt(str(got[k]).strip()) if (k < len(got) and got[k]) else ""
            if not raw_p or len(raw_p.split()) < 8:
                fallback_actions = [
                    "Close-up movie shot of a glowing smartphone lying beside keys on a wooden table under a warm desk lamp in a dim apartment",
                    f"Medium movie shot of {clean_anchor} cautiously checking a locked wooden apartment door in a quiet hallway, dramatic cinema lighting",
                    "Over-the-shoulder movie shot of hands examining printed documents and a brass key on a desk under a warm lamp",
                    "Wide atmospheric cinema shot of a dimly lit apartment living room at night with blue window light and shadows across the doorway",
                ]
                raw_p = fallback_actions[(start_i + k) % len(fallback_actions)]
            framing_tail = "centered vertical 9:16 movie still, 35mm cinema lighting, sharp focus" if is_vertical else "widescreen 16:9 35mm movie still, dramatic cinema lighting, sharp focus"
            full_p = f"{raw_p}, {framing_tail}"
            prompts_out.append(full_p)

    return prompts_out
