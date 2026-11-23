# -*- coding: utf-8 -*-
"""
إعدادات القنوات الأربع V15.0 (Constitution-Locked Autonomous Channel Director + Viral Breakout Engine):
- دستور هوية ثابت وغير قابل للتعديل (Immutable Channel Constitution) لكل قناة يمنع انجراف المحتوى (Zero Niche Drift) نهائياً مهما تعلّم البوت من الإحصائيات.
- 6 ركائز قصصية معتمدة (Approved Pillars) داخل تخصص كل قناة ليديرها المدير الذكي بقاعدة (70% للركائز الأعلى مشاهدة واحتفاظاً + 30% استكشاف متجدد داخل نفس التخصص).
- تثبيت الصوت البشري المتفق عليه بنسبة 100% (Kore للعربي، و Aoede / Charon للإنجليزي) مع حظر الأصوات الآلية (edge_tts) نهائياً.
- دعم 1 فيلم كامل (>15 دقيقة) + 4 مقاطع شورتس يومياً لكل قناة (2 عميقة + 2 خاطفة <55 ثانية).
"""

from typing import Any, Dict, List

GLOBAL_BANNED_DRIFT_TERMS: List[str] = [
    # سياسة وأديان وطائفية وأخبار جارية
    "انتخابات", "برلمان", "حزب سياسي", "فتوى", "طائفي", "مذهبي",
    "election", "parliament", "partisan", "religious fatwa", "sectarian",
    # رياضة وكرة قدم ومشاهير وتريندات تافهة وعملات رقمية
    "مباراة كرة", "الدوري الممتاز", "كريستيانو", "ميسي", "بيتكوين", "فوركس", "مقلب مضحك",
    "soccer match", "premier league", "bitcoin trading", "forex signal", "prank compilation",
    # خوارق رخيصة وأشباح وفضائيين وأساطير خيالية (محجوزة لقنوات مستقبلية مستقلة!)
    "عفريت", "جني مسكون", "الشبح", "شبح", "أشباح", "مسكون", "مسكونة", "الجن", "جني", "جنّي", "روح شريرة",
    "تعويذة سحرية", "سحر خارق", "خارق للطبيعة", "ماورائي", "كائن فضائي", "طبق طائر", "تنين أسطوري", "مصاص دماء", "زومبي",
    "ghost", "ghosts", "ghostly", "haunted", "haunting", "paranormal", "supernatural", "demon", "demonic", "witchcraft", "poltergeist", "apparition", "occult", "curse", "cursed", "spell", "alien", "aliens", "ufo", "ghost possession", "demonic ritual", "alien abduction", "ufo spaceship", "vampire", "werewolf", "zombie apocalypse",
]

CHANNELS: Dict[str, Dict[str, Any]] = {
    "ch1_eg_thriller": {
        "id": "ch1_eg_thriller",
        "env_prefix": "CH1",
        "brand_name": "دفتر راوي",
        "handle": "@daftarrawi",
        "channel_url": "https://www.youtube.com/@daftarrawi",
        "main_profile_id": "6ae7d2dbc8f94352cff3f9a8",
        "tiktok_profile_id": "6ae7d2e1fa06d9df9c45dd49",
        "accounts": {
            "youtube": "6ae7d5c23b672b526b862ccc",
            "facebook": "6afdb80a43ad97b38144b894",
            "tiktok": "6b0109d545f3a06044979b84",
        },
        "language": "ar",
        "niche": "eg_diverse_novels",
        "target_utc_hour": 16,
        "target_utc_minute": 15,
        "min_duration_sec": 945,
        "shot_interval_sec": 9.0,
        "thumb_badge": "قصة واقعية تحبس الأنفاس",
        "base_tags": [
            "قصص واقعية", "قصة حقيقية كاملة", "حكايات مصرية", "غموض نفسي", "قصص مثيرة",
            "دفتر راوي", "اسرار غامضة", "تشويق واثارة", "قصص قبل النوم", "روايات مسموعة",
        ],
        "tiktok_hashtags": "#قصص_واقعية #حكايات #غموض #قصص_حقيقية #تشويق #مصر",
        "voice": {
            "gemini_voice": "Kore",
            "mood": "thriller",
        },
        "constitution": {
            "core_identity": (
                "قناة «دفتر راوي»: قصص إثارة نفسية وتشويق واقعي بشري 100% من قلب البيوت والشوارع المصرية "
                "بالعامية القاهرية الدافئة السلسة — بدون أي خرافات أو أشباح أو خروج عن الحكايات الواقعية المشوقة."
            ),
            "required_dialect": "عامية مصرية قاهرية حقيقية دافئة بدون تشكيل وبدون فصحى مترجمة",
            "title_suffixes": ["| قصة واقعية كاملة", "| حكاية واقعية تحبس الأنفاس", "| سر واقعي خطير"],
            "forbidden_drift_keywords": GLOBAL_BANNED_DRIFT_TERMS,
            "approved_pillars": [
                {
                    "id": "eg_thr_night_signal",
                    "label": "رسالة أو صورة الفجر المريبة",
                    "keywords": ["رسالة", "واتساب", "الفجر", "مكالمة", "تليفون", "صورة", "رقم"],
                    "prompt_seed": (
                        "إثارة نفسية واقعية جداً داخل شقة أو عمارة سكنية بمصر: صورة أو رسالة أو مكالمة غامضة الساعة 3 الفجر "
                        "تكشف إن شخصاً قريباً جداً يراقب البطل في نفس اللحظة، وتتوالى المفاجآت الواقعية العاقلة حتى كشف خطة بشرية مذهلة"
                    ),
                },
                {
                    "id": "eg_thr_apartment_secret",
                    "label": "سر الشقة أو الجيرة والعمارة",
                    "keywords": ["شقة", "عمارة", "دولاب", "عداد", "فاتورة", "أسانسير", "جار", "باب"],
                    "prompt_seed": (
                        "غموض نفسي واقعي حول شقة أو عمارة سكنية في القاهرة: تفصيلة ملموسة في فاتورة كهرباء أو دولاب مخفي "
                        "أو كاميرا الأسانسير تفتح خيط سر مدفون يقلب حياة السكان كلهم بدون أي خوارق"
                    ),
                },
                {
                    "id": "eg_thr_hidden_recording",
                    "label": "تسجيل أو كاميرا تفضح المؤامرة",
                    "keywords": ["تسجيل", "كاميرا", "مراقبة", "مؤامرة", "لعبة", "خيانة", "مكتب"],
                    "prompt_seed": (
                        "إثارة نفسية وخدعة دهاء بشري بارد: اكتشاف تسجيل صوتي أو لقطة كاميرا مراقبة بالصدفة في البيت أو الشغل "
                        "يكشف إن أقرب الناس بيدبر لعبة نفسية محكمة بالورقة والقلم، وقلب الطاولة عليهم بذكاء يوقف القلب"
                    ),
                },
                {
                    "id": "eg_thr_night_shift",
                    "label": "ليلة نوبتجية أو توصيلة متأخرة",
                    "keywords": ["توصيلة", "نوبتجية", "ليل", "طريق", "عربية", "موقف", "شنطة"],
                    "prompt_seed": (
                        "ليلة توتر نفسي حقيقية لا تُنسى (نوبتجية ليلية هادئة أو توصيلة متأخرة أو شنطة منسية): "
                        "كل عشر دقائق يظهر دليل مادي ملموس يناقض اللي قبله حتى الصدمة الواقعية الكبرى في النهاية"
                    ),
                },
                {
                    "id": "eg_thr_contract_inheritance",
                    "label": "فخ العقد أو الوصية والمفتاح القديم",
                    "keywords": ["عقد", "توكيل", "وصية", "مفتاح", "ميراث", "خزنة", "أوراق"],
                    "prompt_seed": (
                        "تشويق نفسي عائلي واجتماعي محكم في مصر: ظهور مفتاح قديم أو بند غامض في عقد أو وصية يكشف سر عائلي "
                        "مدفون من سنين وفخ متخطط بهدوء، والبطل يربط الخيوط قبل فوات الأوان"
                    ),
                },
                {
                    "id": "eg_thr_double_life",
                    "label": "تفصيلة صغيرة تكشف حياة مزدوجة",
                    "keywords": ["إيصال", "حياة مزدوجة", "سفر", "تذكرة", "كذبة", "هوية", "سر"],
                    "prompt_seed": (
                        "غموض نفسي واقعي يبدأ من تفصيلة يومية تافهة (إيصال بنكي، تذكرة مترو، أو إشعار توصيل لمكان غريب) "
                        "تجر البطل وراء خيط يكشف حياة مزدوجة مستحيلة لشخص كان يثق فيه ثقة عمياء"
                    ),
                },
                {
                    "id": "eg_thr_dark_comedy_heist",
                    "label": "حيل وذكاء بشري كوميدي غامض",
                    "keywords": ["حيلة", "نصب", "مفارقة", "ذكاء", "سرقة", "خطة", "مقلب"],
                    "prompt_seed": (
                        "قصة ذكاء بشري واحتيال عبقري ومفارقات ساخرة مليئة بالتشويق والضحك الأسود: "
                        "نصاب يقع في شر أعماله، أو خطة محكمة تنقلب على أصحابها بطريقة مضحكة وغامضة في نفس الوقت"
                    ),
                },
                {
                    "id": "eg_thr_historical_mystery",
                    "label": "أسرار وتاريخ مصر الغامض",
                    "keywords": ["تاريخ", "قصر", "وثيقة", "كنز", "مصر القديمة", "حارة", "مخطوطة"],
                    "prompt_seed": (
                        "غموض تاريخي واقعي حول وثيقة سرية أو قصر مهجور من زمن الباشوات أو لغز حقيقي "
                        "من تاريخ مصر تتشابك خيوطه مع أحداث معاصرة تكشف سراً لا يصدق"
                    ),
                },
                {
                    "id": "eg_thr_unbelievable_survival",
                    "label": "قصص بقاء ونجاة واقعية مستحيلة",
                    "keywords": ["نجاة", "صحراء", "بقاء", "خطر", "مأزق", "حادث", "مواجهة"],
                    "prompt_seed": (
                        "قصة حبس أنفاس حقيقية لشخص وجد نفسه في مأزق مميت ومستحيل في قلب الصحراء أو مكان معزول، "
                        "وقاتل من أجل النجاة بالصبر والذكاء حتى النهاية الصادمة"
                    ),
                },
                {
                    "id": "eg_thr_bizarre_true_events",
                    "label": "أغرب الحوادث والظواهر الواقعية المدهشة",
                    "keywords": ["حادثة", "غرابة", "لغز حقيقي", "صدمة", "واقعة", "تحقيق"],
                    "prompt_seed": (
                        "أحداث حقيقية واقعية أغرب من الخيال صدمت المحققين والرأي العام، "
                        "تفاصيلها لا يصدقها عقل وتثبت أن الواقع أحياناً أغرب بكثير من أي فيلم خيالي"
                    ),
                },
                {
                    "id": "eg_thr_fantasy_supernatural_realism",
                    "label": "غرائب الخيال والغموض والظواهر التي حيرت العلم",
                    "keywords": ["ظاهرة", "غموض", "علم", "حيرة", "تفسير", "إشارة", "صدفة مستحيلة"],
                    "prompt_seed": (
                        "قصة غموض وظواهر استثنائية واقعية حيرت العلماء والخبراء دون تفسير علمي حاسم، "
                        "مبنية على وقائع وشهادات موثقة تثير أقصى درجات الدهشة والخيال المشوق"
                    ),
                },
                {
                    "id": "eg_thr_psychological_mindgame",
                    "label": "ألعاب العقول والمطاردات النفسية المعقدة",
                    "keywords": ["ذكاء", "لعبة", "عقل", "مواجهة", "خطة", "خداع", "انقلاب"],
                    "prompt_seed": (
                        "مباراة شطرنج بشرية معقدة بين شخصين فائقين في الذكاء يحاول كل منهما توريط الآخر "
                        "دون ترك أي دليل، حتى اللحظة الأخيرة التي تكشف من كان يسيطر على اللعبة منذ اليوم الأول"
                    ),
                },
                {
                    "id": "eg_thr_closed_palace_secrets",
                    "label": "أسرار القصور المغلقة وصراعات العائلات الثرية",
                    "keywords": ["قصر", "وصية", "ثروة", "عائلة", "ميراث", "قفل", "خزينة خاصة"],
                    "prompt_seed": (
                        "أسرار غرف مغلقة في قصر تاريخي مهيب ونزاع صامت على ثروة غامضة ووصية مشفرة "
                        "تكشف وجوهاً مخيفة وتاريخاً سرياً لم يعرفه أحد لعقود"
                    ),
                },
                {
                    "id": "eg_thr_serial_mastermind",
                    "label": "أعقد قضايا الجرائم المتسلسلة ومطاردة الدهاء",
                    "keywords": ["بصمة", "شفرة", "مطاردة", "محقق", "توقيع", "ضحية", "لغز"],
                    "prompt_seed": (
                        "مطاردة بوليسية ونفسية حابسة للأنفاس لعقل إجرامي فائق الذكاء يترك توقيعاً غامضاً "
                        "في كل مكان، ومحقق عبقري يفك اللغز من خطأ نفسي خفي لم يحسب حسابه"
                    ),
                },
                {
                    "id": "eg_thr_digital_cyber_hunt",
                    "label": "مؤامرات العالم الرقمي وتجسس الهواتف والذكاء الاصطناعي",
                    "keywords": ["كاميرا", "هاتف", "تسريب", "قرصنة", "تتبع", "ذكاء اصطناعي", "ملف سري"],
                    "prompt_seed": (
                        "مؤامرة رقمية واقعية تبدأ بملف غير متوقع يظهر على هاتف بطل القصة أو كاميرا مراقبة ذكية "
                        "تسجل ما لا يجب رؤيته، وتتحول لمطاردة بقاء إلكترونية وواقعية تحبس الأنفاس"
                    ),
                },
                {
                    "id": "eg_thr_doomed_expeditions",
                    "label": "رحلات الطيران والسفن المنكوبة وألغاز المجهول",
                    "keywords": ["طائرة", "سفينة", "بحر", "نداء استغاثة", "رادار", "عاصفة", "اختفاء"],
                    "prompt_seed": (
                        "لغز رحلة حقيقية في أعالي البحار أو الأجواء انقطع اتصالها في ظروف محيرة "
                        "والتحقيقات المضنية التي قادت إلى العثور على أسرار تفوق الخيال وشهادات نجاة لا تصدق"
                    ),
                },
            ],
        },
        "cta_spoken_1": "لو عجبك المقطع متنساش تشترك في القناة وتعمل لايك علشان تشوف الحكايات الجاية أول بأول.. وقولنا رأيك وتوقعك في التعليقات تحت!",
        "cta_spoken_2": "اشترك في القناة وفعل الجرس واعمل لايك علشان تتابع باقي الحكاية كاملة أول بأول.. ومستني رأيك وتوقعك في التعليقات!",
        "cta_spoken_3": "دوس لايك واشترك في القناة علشان حكاياتنا الجديدة متفوتكش كل يوم.. وقولنا في التعليقات حسيت بإيه في اللحظة دي!",
        "cta_spoken_4": "اشترك في القناة واعمل لايك عشان تدعمنا في نشر حكايات أكتر.. واكتب توقعك للي حصل في الكومنتات تحت!",
        "cta_banner": "اشترك في القناة واعمل لايك! وشاركنا رأيك في التعليقات",
    },
    "ch2_eg_mystery": {
        "id": "ch2_eg_mystery",
        "env_prefix": "CH2",
        "brand_name": "الدليل الأخير",
        "handle": "@eldalilelakhir",
        "channel_url": "https://www.youtube.com/@eldalilelakhir",
        "main_profile_id": "6ae7d2ddb39b9e499c701e1e",
        "tiktok_profile_id": "6ae7d2e3c5e8b8157472e576",
        "accounts": {
            "youtube": "6ae7d71dd515e7485027735d",
            "facebook": "6afdb873c92019081e499fa1",
            "tiktok": "6b010a62a3ec26568132acb5",
        },
        "language": "ar",
        "niche": "eg_conan_detective",
        "target_utc_hour": 18,
        "target_utc_minute": 15,
        "min_duration_sec": 945,
        "shot_interval_sec": 9.0,
        "thumb_badge": "لغز جريمة مستحيل الحل",
        "base_tags": [
            "لغز جريمة", "الغاز بوليسية", "قضايا غامضة", "الدليل الاخير", "تحقيقات ذكية",
            "لغز الغرفة المغلقة", "المحقق كونان", "قصص غموض", "الغاز للاذكياء", "كشف الجاني",
        ],
        "tiktok_hashtags": "#الغاز #غموض #تحقيقات #قصص_واقعية #ذكاء #مصر",
        "voice": {
            "gemini_voice": "Kore",
            "mood": "mystery",
        },
        "constitution": {
            "core_identity": (
                "قناة «الدليل الأخير»: قضايا تحقيق بوليسي ذكي وألغاز غرفة مغلقة وحجج غياب مستحيلة على طريقة المحقق كونان "
                "بالعامية المصرية القاهرية المشوقة — منطق جنائي عادل 100% وأدلة مادية ذكية بدون عنف دموي أو خرافات."
            ),
            "required_dialect": "عامية مصرية قاهرية بوليسية شيقة وواضحة بدون تشكيل وبدون فصحى مترجمة",
            "title_suffixes": ["| لغز جريمة محير", "| قضية الغرفة المغلقة", "| تحقيق ذكي كامل"],
            "forbidden_drift_keywords": GLOBAL_BANNED_DRIFT_TERMS,
            "approved_pillars": [
                {
                    "id": "eg_mys_locked_room",
                    "label": "لغز الغرفة المغلقة من الداخل",
                    "keywords": ["غرفة مغلقة", "مقفول", "مفتاح", "فيلا", "مكتب", "شباك"],
                    "prompt_seed": (
                        "قضية غرفة مغلقة واقعية فائقة الذكاء على طريقة المحقق كونان في فيلا أو مكتب بالقاهرة: "
                        "الباب والشبابيك مقفولين من الداخل، 4 مشتبه بهم لكل واحد دافع قوي، وخدعة فيزيائية ذكية تكشفها تفصيلة صغيرة"
                    ),
                },
                {
                    "id": "eg_mys_impossible_alibi",
                    "label": "حجة الغياب المستحيلة والتوقيت المزيف",
                    "keywords": ["توقيت", "كاميرا", "حجة غياب", "ساعة", "بث", "ثانية"],
                    "prompt_seed": (
                        "قضية حجة الغياب المستحيلة بالكاميرات والتوقيت على طريقة المحقق كونان: الجاني ظهر في بث مباشر "
                        "أو كاميرا مراقبة في مكان بعيد وقت الحدث بالثانية، ودليل عبقري يكشف التلاعب بالتوقيت"
                    ),
                },
                {
                    "id": "eg_mys_closed_circle",
                    "label": "لغز الباخرة النيلية أو العشاء المغلق",
                    "keywords": ["مركب", "باخرة", "النيل", "عشاء", "ماسة", "قاعة", "اختفاء"],
                    "prompt_seed": (
                        "قضية العشاء المغلق أو الباخرة النيلية في القاهرة: اختفاء مستند خطير أو قطعة ثمينة وسط 4 أشخاص "
                        "لم يخرج أحدهم من القاعة، وكل شاهد يكذب في تفصيلة واحدة حتى المواجهة الحاسمة"
                    ),
                },
                {
                    "id": "eg_mys_framed_innocent",
                    "label": "الأثر العكسي وتبرئة المتهم المظلوم",
                    "keywords": ["بصمة", "انعكاس", "مراية", "ظل", "بريء", "تلفيق", "دليل"],
                    "prompt_seed": (
                        "قضية تلفيق متقنة كل الأدلة فيها تشير لشخص بريء، لكن المحقق يلاحظ تناقضاً فيزيائياً واحداً "
                        "(انعكاس في زجاج، زاوية ظل، أو ترتيب أشياء معكوس) يقلب القضية ويفضح المدبر الحقيقي"
                    ),
                },
                {
                    "id": "eg_mys_detective_trap",
                    "label": "مصيدة المحقق لكشف الجاني بنفسه",
                    "keywords": ["فخ", "مصيدة", "تحقيق", "اعتراف", "شاهد", "خطة"],
                    "prompt_seed": (
                        "تحقيق بوليسي ذكي يواجه فيه المحقق 3 مشتبه بهم هادئين بدون دليل مباشر، فينصب تجربة منطقية ذكية "
                        "تجعل الجاني الحقيقي يكشف نفسه بمعلومة يستحيل أن يعرفها غير الفاعل"
                    ),
                },
                {
                    "id": "eg_mys_cold_clue",
                    "label": "تفصيلة منسية تحل قضية قديمة",
                    "keywords": ["ملف", "قديمة", "سنين", "صورة قديمة", "سرقة", "خزنة"],
                    "prompt_seed": (
                        "إعادة فتح ملف لغز غامض حير الجميع بفضل صورة قديمة أو تفصيلة صغيرة لم ينتبه لها أحد وقت الحدث، "
                        "وربط الخيوط خطوة بخطوة حتى كشف الحقيقة الكاملة"
                    ),
                },
                {
                    "id": "eg_mys_historical_coldcase",
                    "label": "ألغاز تاريخية وقضايا قديمة محيرة",
                    "keywords": ["تاريخ", "اكتشاف", "بردية", "قبر", "أثر", "لغز قديم", "حضارة"],
                    "prompt_seed": (
                        "لغز تاريخي غامض مستند إلى أحداث وأدلة ووثائق حقيقية حيرت المؤرخين والمحققين، "
                        "وتتبع الخطوط العلمية والبوليسية لحل اللغز الممتد عبر القرون"
                    ),
                },
                {
                    "id": "eg_mys_mastermind_heist",
                    "label": "سرقات المتاحف والبنوك المستحيلة",
                    "keywords": ["سطو", "خزنة", "بنك", "متحف", "ألماس", "حيلة عبقرية", "إنذار"],
                    "prompt_seed": (
                        "أعقد وأذكى عمليات السطو والسرقات المستحيلة التي نفذها دهاة بدون إطلاق رصاصة واحدة "
                        "وسط أحدث أجهزة الإنذار وكيف أوقعهم المحققون بخطأ لا يرى بالعين المجردة"
                    ),
                },
                {
                    "id": "eg_mys_vanished_without_trace",
                    "label": "اختفاءات غامضة حيرت العالم",
                    "keywords": ["اختفاء", "أثر", "سراب", "سفينة", "مجهول", "بصمات"],
                    "prompt_seed": (
                        "قصة اختفاء غامضة لشخصية أو سفينة أو طائرة اختفت تماماً دون أن تترك أثراً واحداً "
                        "وتفاصيل رحلة البحث المضنية التي كشفت أسراراً تفوق الخيال"
                    ),
                },
                {
                    "id": "eg_mys_forensic_breakthrough",
                    "label": "ألغاز الطب الشرعي والاكتشافات المعملية الحاسمة",
                    "keywords": ["معمل", "أثر خفي", "عينة", "حمض نووي", "مجهر", "سم", "دليل قاطع"],
                    "prompt_seed": (
                        "قضية جنائية معقدة بدت وكأنها حادث عرضي أو انتحار محكم، لكن تفصيلة طبية أو كيميائية لا ترى بالعين المجردة "
                        "في تقرير المعمل الجنائي تقلب الموازين وتثبت جريمة قتل تم التخطيط لها بدهاء استثنائي"
                    ),
                },
                {
                    "id": "eg_mys_interpol_manhunt",
                    "label": "مطاردات الإنتربول الدولية للعقول المتنكرة بأسماء مزيفة",
                    "keywords": ["إنتربول", "مطار", "جواز سفر", "تنكر", "مطاردة", "هوية", "حدود"],
                    "prompt_seed": (
                        "مطاردة دولية شائقة عبر الحدود بين محقق عبقري وداهية ينتحل 5 شخصيات مختلفة "
                        "ويعيش حياة كاملة تحت هويات مزورة حتى أوقعه تفصيل لغوي أو سلوكي صغير كشف قناعه الحقيقي"
                    ),
                },
                {
                    "id": "eg_mys_theatre_crime",
                    "label": "جرائم المسارح والمعارض وحيل التمويه البصري",
                    "keywords": ["مسرح", "عرض", "خدعة بصرية", "ستارة", "تمويه", "جمهور", "غموض"],
                    "prompt_seed": (
                        "جريمة مستحيلة حدثت أمام أعين المئات في صالة عرض أو مسرح مغلق دون أن يلاحظ أحد كيف نُفذت، "
                        "وفك الشفرة الهندسية والتمويه البصري الذكي الذي استغله الجاني لتضليل الجميع"
                    ),
                },
            ],
        },
        "cta_spoken_1": "لو وصلت للغز ده متنساش تدوس لايك وتشترك في القناة علشان تتابع كشف أصعب القضايا أول بأول.. واكتبلنا رأيك وتوقعاتك في التعليقات!",
        "cta_spoken_2": "اشترك في القناة وفعل الجرس واعمل لايك علشان تشوف حل اللغز كامل.. ومستني تحليلك وتوقعك للجاني في التعليقات تحت!",
        "cta_spoken_3": "دوس لايك واشترك في القناة لتصلك أغرب الألغاز والتحقيقات يومياً.. وشاركنا برأيك في الكومنتات!",
        "cta_spoken_4": "اشترك في القناة واعمل لايك عشان تدعم المحتوى وتشوف الحلقات الجاية.. وقولنا مين المشتبه فيه الأقرب بالنسبة لك!",
        "cta_banner": "اشترك في القناة واعمل لايك! وشاركنا تحليلك في التعليقات",
    },
    "ch3_en_thriller": {
        "id": "ch3_en_thriller",
        "env_prefix": "CH3",
        "brand_name": "Velvet Tales",
        "handle": "@velvettalesclub",
        "channel_url": "https://www.youtube.com/@velvettalesclub",
        "main_profile_id": "6ae7d2dec8f94352cff3f9ab",
        "tiktok_profile_id": "6ae7d2e4fa06d9df9c45dd4b",
        "accounts": {
            "youtube": "6ae7d81a3a502a73a1634519",
            "facebook": "6afdc65779436b32ce49acb4",
            "tiktok": "6b010e0906a30b0ea8c82957",
        },
        "language": "en",
        "niche": "en_diverse_stories",
        "target_utc_hour": 21,
        "target_utc_minute": 15,
        "min_duration_sec": 945,
        "shot_interval_sec": 9.0,
        "thumb_badge": "TRUE CHILLING TWIST",
        "base_tags": [
            "true mystery story", "psychological thriller story", "true scary stories", "plot twist story",
            "storytime", "chilling true stories", "velvet tales", "suspense audio story", "full storytime",
        ],
        "tiktok_hashtags": "#storytime #truestory #mystery #plotwist #thriller #creepy",
        "voice": {
            "gemini_voice": "Aoede",
            "orpheus_voice": "tara",
            "mood": "thriller",
        },
        "constitution": {
            "core_identity": (
                "Velvet Tales: 100% grounded, hyper-realistic modern psychological thrillers & real-world plot twists "
                "(MrBallen-style human suspense) in conversational American English — zero supernatural ghosts, aliens, politics, or gore."
            ),
            "required_dialect": "Conversational, gripping American English storytelling",
            "title_suffixes": ["| True Mystery Story", "| Psychological Thriller Story", "| Chilling Plot Twist"],
            "forbidden_drift_keywords": GLOBAL_BANNED_DRIFT_TERMS,
            "approved_pillars": [
                {
                    "id": "en_thr_3am_notification",
                    "label": "3 AM Digital / Phone Anomaly",
                    "keywords": ["3 am", "2:47", "photo", "notification", "phone", "cloud", "monitor", "airtag"],
                    "prompt_seed": (
                        "a grounded, hyper-realistic MrBallen-style modern psychological thriller starting at 3:14 AM "
                        "with an impossible notification, AirTag alert, or photo from inside an ordinary home—zero supernatural clichés, 100% chilling human calculation"
                    ),
                },
                {
                    "id": "en_thr_doorbell_neighbor",
                    "label": "Doorbell Cam & Neighbor Double Life",
                    "keywords": ["doorbell", "camera", "neighbor", "receipt", "hallway", "next door", "apartment"],
                    "prompt_seed": (
                        "a pulse-pounding psychological cat-and-mouse thriller where one tiny discrepancy on a doorbell camera "
                        "or delivery receipt exposes a jaw-dropping double life right next door"
                    ),
                },
                {
                    "id": "en_thr_night_shift",
                    "label": "Night-Shift & Rideshare Suspense",
                    "keywords": ["night shift", "janitor", "delivery", "driver", "office", "highway", "late night"],
                    "prompt_seed": (
                        "a claustrophobic, realistic night-shift, security desk, or late-night delivery suspense story "
                        "where small physical details stop adding up until a mind-bending real-world twist"
                    ),
                },
                {
                    "id": "en_thr_hidden_sublet",
                    "label": "New Apartment / Utility Bill Anomaly",
                    "keywords": ["lease", "utility", "closet", "attic", "basement", "landlord", "wall", "key"],
                    "prompt_seed": (
                        "a realistic domestic suspense story where a tenant notices an unexplained spike in utility records "
                        "or a locked storage space that unravels a calculated real-world scheme"
                    ),
                },
                {
                    "id": "en_thr_inner_circle_sting",
                    "label": "Voice Memo / Trusted Circle Betrayal",
                    "keywords": ["voice memo", "dashcam", "partner", "contract", "alibi", "recording", "sting"],
                    "prompt_seed": (
                        "a taut psychological suspense story where an accidental dashcam clip or voice memo reveals "
                        "a coldly planned setup by someone trusted, forcing the protagonist to outsmart them quietly"
                    ),
                },
                {
                    "id": "en_thr_wrong_item_trail",
                    "label": "Misplaced Object / Stranger's Trail",
                    "keywords": ["ticket", "suitcase", "package", "locker", "receipt", "stranger", "envelope"],
                    "prompt_seed": (
                        "a gripping real-world mystery triggered by a swapped bag, misdelivered envelope, or lost locker key "
                        "that pulls an ordinary person into an intricately planned human puzzle"
                    ),
                },
                {
                    "id": "en_thr_dark_comedy_heist",
                    "label": "High-Stakes Heists & Dark Witty Con Artists",
                    "keywords": ["heist", "con artist", "witty", "scheme", "ironic", "reversal", "twist"],
                    "prompt_seed": (
                        "a fast-paced, darkly witty suspense story about a brilliant con artist or high-stakes heist "
                        "where an unexpected twist turns the hunters into the hunted in an unbelievable fashion"
                    ),
                },
                {
                    "id": "en_thr_extreme_survival",
                    "label": "Extreme Survival & Impossible Escapes",
                    "keywords": ["survival", "wilderness", "stranded", "escape", "endurance", "ordeal"],
                    "prompt_seed": (
                        "a breathless true-events survival thriller of an ordinary person pushed to the ultimate edge "
                        "in an isolated wilderness or trapped scenario, outsmarting death with sheer will and intellect"
                    ),
                },
            ],
        },
        "cta_spoken_1": "Make sure to subscribe and drop a like so you never miss our next psychological thriller.. and share your thoughts in the comments below!",
        "cta_spoken_2": "Hit that subscribe button and leave a like to catch the full story.. what would you have done? Let us know down in the comments!",
        "cta_spoken_3": "Subscribe for more chilling stories and hit like if this gave you goosebumps.. drop your thoughts in the comments!",
        "cta_spoken_4": "Don't forget to like and subscribe to stay tuned for our next episode.. leave your reaction down in the comments!",
        "cta_banner": "SUBSCRIBE & LIKE! SHARE YOUR THOUGHTS IN COMMENTS",
    },
    "ch4_en_mystery": {
        "id": "ch4_en_mystery",
        "env_prefix": "CH4",
        "brand_name": "Mindlock",
        "handle": "@mindlockcases",
        "channel_url": "https://www.youtube.com/@mindlockcases",
        "main_profile_id": "6ae7d2e0c8f94352cff3f9ae",
        "tiktok_profile_id": "6ae7d2e58b38647997f523b5",
        "accounts": {
            "youtube": "6ae7d871bdfac131ee354bcd",
            "facebook": "6afdc76147cc7214709c73ad",
            "tiktok": "6b010d8569dec8bf7030cd4a",
        },
        "language": "en",
        "niche": "en_detective_mystery",
        "target_utc_hour": 23,
        "target_utc_minute": 45,
        "min_duration_sec": 945,
        "shot_interval_sec": 9.0,
        "thumb_badge": "IMPOSSIBLE ALIBI",
        "base_tags": [
            "detective mystery story", "locked room mystery", "whodunit riddle", "impossible crime story",
            "mindlock cases", "murder mystery puzzle", "true detective story", "alibi mystery",
        ],
        "tiktok_hashtags": "#mystery #detective #riddle #whodunit #plotwist #truecrime",
        "voice": {
            "gemini_voice": "Charon",
            "orpheus_voice": "daniel",
            "mood": "mystery",
        },
        "constitution": {
            "core_identity": (
                "Mindlock: 100% fair-play detective investigations, locked-room puzzles, and impossible clockwork alibis "
                "(Knives Out / Detective Conan logic) in crisp American English — zero supernatural elements, politics, or graphic gore."
            ),
            "required_dialect": "Sharp, atmospheric American English investigative storytelling",
            "title_suffixes": ["| Locked-Room Detective Mystery", "| Impossible Alibi Case", "| Detective Whodunit"],
            "forbidden_drift_keywords": GLOBAL_BANNED_DRIFT_TERMS,
            "approved_pillars": [
                {
                    "id": "en_mys_locked_room",
                    "label": "Classic Locked-Room Mechanism",
                    "keywords": ["locked", "sealed", "study", "welded", "inside", "bolted", "key"],
                    "prompt_seed": (
                        "a razor-sharp Detective Conan / Knives Out realistic locked-room investigation with 4 suspects, "
                        "timestamped alibis, fair-play physical clues, and a brilliant step-by-step mechanical deduction"
                    ),
                },
                {
                    "id": "en_mys_clockwork_alibi",
                    "label": "Clockwork & CCTV Timestamp Paradox",
                    "keywords": ["alibi", "clock", "timestamp", "cctv", "reflection", "mirror", "remote"],
                    "prompt_seed": (
                        "an impossible CCTV & clockwork-alibi mystery where one tiny reflection, shadow angle, "
                        "or two-second audio delay exposes the mastermind everyone trusted"
                    ),
                },
                {
                    "id": "en_mys_closed_gala",
                    "label": "Closed-Circle Gala / Vessel Disappearance",
                    "keywords": ["gala", "museum", "diamond", "vessel", "yacht", "train", "guests"],
                    "prompt_seed": (
                        "a high-stakes closed-circle mystery at an isolated estate, private train, or midnight museum gala "
                        "where a priceless item vanishes among four witnesses and every witness hides exactly one lie"
                    ),
                },
                {
                    "id": "en_mys_staged_reversal",
                    "label": "Staged Evidence & Forensic Reversal",
                    "keywords": ["staged", "framed", "forensic", "footprint", "gloves", "reversed", "witness"],
                    "prompt_seed": (
                        "a clever investigative puzzle where every planted clue points to an innocent person until "
                        "the detective spots one physical impossibility in how the scene was staged"
                    ),
                },
                {
                    "id": "en_mys_logical_sting",
                    "label": "The Investigator's Logical Sting Trap",
                    "keywords": ["trap", "test", "experiment", "suspects", "confession", "bait"],
                    "prompt_seed": (
                        "a tense psychological deduction case where the detective lacks physical proof and designs "
                        "a brilliant fair-play logical test that tricks only the guilty mastermind into revealing hidden knowledge"
                    ),
                },
                {
                    "id": "en_mys_cold_cipher",
                    "label": "Contested Will / Cold-Case Timeline Clue",
                    "keywords": ["will", "safe", "cipher", "archive", "photograph", "decade", "ledger"],
                    "prompt_seed": (
                        "an intricate mystery centered on a contested safe, coded ledger, or archived photograph "
                        "whose tiny background detail solves an impossible disappearance step by step"
                    ),
                },
                {
                    "id": "en_mys_historical_enigma",
                    "label": "Historical Enigmas & Lost Artifacts",
                    "keywords": ["history", "artifact", "cipher", "ancient", "manuscript", "tomb", "expedition"],
                    "prompt_seed": (
                        "a baffling historical investigation into a real-world lost artifact or ancient secret "
                        "that baffled historians and detectives for generations, uncovered through brilliant logic"
                    ),
                },
                {
                    "id": "en_mys_vanished_in_thin_air",
                    "label": "Mysterious Vanishings & Unsolved Anomalies",
                    "keywords": ["vanished", "air", "ship", "disappearance", "anomaly", "search", "trace"],
                    "prompt_seed": (
                        "a chilling true-crime investigation into people or vessels that vanished in broad daylight "
                        "without leaving a single physical trace, and the mind-bending truth revealed decades later"
                    ),
                },
                {
                    "id": "en_mys_forensic_coldcase",
                    "label": "Forensic Cold-Cases & Microscopic Anomalies",
                    "keywords": ["forensic", "microscopic", "chemical", "fiber", "reconstruction", "verdict"],
                    "prompt_seed": (
                        "an apparently flawless cold case where a microscopic forensic inconsistency—a fiber, reflection, or chemical timestamp— "
                        "reconstructed the entire crime scene and exposed a cunning mastermind after decades of silence"
                    ),
                },
                {
                    "id": "en_mys_high_society_intrigue",
                    "label": "High-Society Secrets & Contested Dynastic Wills",
                    "keywords": ["estate", "dynasty", "will", "poison", "inheritance", "manor", "motive"],
                    "prompt_seed": (
                        "a razor-sharp closed-circle mystery inside a secluded historic manor where billions were at stake, "
                        "every family member possessed an airtight alibi, and one silent physical paradox solved the murder"
                    ),
                },
            ],
        },
        "cta_spoken_1": "Pause and play detective! Make sure to like and subscribe to solve the world's most impossible cases with us.. and drop your theory in the comments!",
        "cta_spoken_2": "Hit subscribe and leave a like to catch the full investigation.. which clue gave it away for you? Tell us down in the comments!",
        "cta_spoken_3": "Subscribe for daily impossible mysteries and hit like to support the channel.. who was your prime suspect? Let us know below!",
        "cta_spoken_4": "Don't forget to like and subscribe for more mind-bending investigations.. leave your thoughts down in the comments!",
        "cta_banner": "SUBSCRIBE & LIKE! SOLVE THE FULL CASE ON OUR CHANNEL",
    },
}
