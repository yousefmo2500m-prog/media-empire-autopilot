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
            "facebook": "6ae7d69647d6313c024ad1f4",
            "tiktok": "6ae7da8c161bb07c0b158462",
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
            ],
        },
        "cta_spoken_1": "اقف عند اللحظة دي! لو انت مكانه دلوقتي: واحد تواجهه فوراً باللي شفته؟ ولا اتنين تسكت وتراقبه في السر لحد الفجر؟ اكتب واحد أو اتنين في التعليقات واسمع القصة كاملة على قناتنا!",
        "cta_spoken_2": "ثانية واحدة! التفصيلة دي قلبت كل حاجة! تفتكر واحد كانت صدفة مستحيلة؟ ولا اتنين فخ متخطط بدم بارد؟ اكتب واحد أو اتنين في التعليقات وكمل الحكاية كاملة دلوقتي!",
        "cta_spoken_3": "لو انت مكانه في الثانية دي: واحد تفتح الباب وتواجهه؟ ولا اتنين تهرب وتقفل على نفسك؟ اكتب رقمك في التعليقات!",
        "cta_spoken_4": "تفتكر مين اللي كدب فيهم: واحد أقرب صاحب ليه؟ ولا اتنين الشخص اللي محدش شك فيه؟ اكتب واحد أو اتنين في التعليقات!",
        "cta_banner": "اكتب ١ أو ٢ في التعليقات! القصة الكاملة على القناة",
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
            "facebook": "6ae7d786d515e74850277383",
            "tiktok": "6ae7dade79a3bd79b94be415",
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
            ],
        },
        "cta_spoken_1": "وقف الفيديو وفكر كمحقق! تفتكر الجاني دخل إزاي: واحد بمفتاح منسوخ من جوه البيت؟ ولا اتنين كان مستخبي قبل ما الباب يتقفل؟ اكتب واحد أو اتنين في التعليقات وشوف الحل الكامل على قناتنا!",
        "cta_spoken_2": "ركز في الغلطة الصغيرة دي! تفتكر مين صاحب الدليل المزيف: واحد الشاهد الأول؟ ولا اتنين صاحب البلاغ نفسه؟ اكتب واحد أو اتنين في التعليقات وكمل التحقيق كامل!",
        "cta_spoken_3": "شغّل عقلك في ثانية: واحد التسجيل ده متفبرك؟ ولا اتنين الساعة هي اللي متقدمة؟ اكتب واحد أو اتنين في التعليقات!",
        "cta_spoken_4": "قبل ما يتكشف الحل: واحد الجريمة متخططة من شهور؟ ولا اتنين حصلت في لحظة غضب؟ اكتب رقمك في التعليقات!",
        "cta_banner": "اكتب ١ أو ٢ في التعليقات! حل اللغز الكامل على القناة",
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
            "facebook": "6ae7d841df2a5a7ca0789146",
            "tiktok": "6ae7db62c5b7eb7a48c705db",
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
            ],
        },
        "cta_spoken_1": "Freeze right there! Put yourself in their shoes: type 1 in the comments if you open that door and confront them, or type 2 if you lock yourself in and call for help! Then catch the full sixteen minute story on our channel!",
        "cta_spoken_2": "Hold everything! Was that message a warning or a trap? Type 1 for warning or type 2 for trap in the comments, and watch the full twist unfold on our channel!",
        "cta_spoken_3": "Quick—what would you do in that second? Type 1 if you check the camera, or 2 if you run out the door!",
        "cta_spoken_4": "Who was lying the whole time? Type 1 for the neighbor, or type 2 for the person inside the house! Drop your pick below!",
        "cta_banner": "COMMENT 1 OR 2 BELOW! FULL 16-MIN STORY ON CHANNEL",
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
            "facebook": "6ae7d89168b951402ee910a9",
            "tiktok": "6ae7dbac97252a684ca5e37f",
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
            ],
        },
        "cta_spoken_1": "Pause and play detective! How was the room locked from inside? Type 1 if the alibi clock was rigged, or type 2 if someone never left the room! Comment 1 or 2 and solve the full case on our channel!",
        "cta_spoken_2": "Wait right at that clue! Which detail exposed the culprit? Type 1 for the timestamp, or type 2 for the missing key! Drop your answer below and watch the full investigation!",
        "cta_spoken_3": "Solve it in five seconds: type 1 if the witness lied, or type 2 if the recording was staged!",
        "cta_spoken_4": "Final detective test: type 1 for an inside job, or type 2 for a framed suspect! Comment 1 or 2 now!",
        "cta_banner": "TYPE 1 OR 2 IN COMMENTS! SOLVE FULL CASE ON CHANNEL",
    },
}
