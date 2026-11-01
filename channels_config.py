# -*- coding: utf-8 -*-
"""
إمبراطورية القنوات الأربع المستقلة (Autonomous 4-Channel Media Empire)
مصممة خصيصاً للتوافق مع سياسات ربح يوتيوب (تحديث يوليو 2026) وربح محتوى فيسبوك في مصر.
"""

CHANNELS = {
    "ch1_novels": {
        "id": "ch1_novels",
        "brand_name": "مسرح الروايات الصوتية",
        "tagline": "روايات غموض وتشويق أصلية — حلقات متسلسلة بأداء تمثيلي سينمائي",
        "language": "ar",
        "aspect_primary": "16:9",     # حلقات كاملة لتجميع 4000 ساعة مشاهدة بسرعة
        "also_render_short": True,    # مقطع تشويقي 9:16 لجلب المشتركين من الشورتس والريلز
        "sound_mood": "suspense_noir",
        "palette": {
            "bg_top": (12, 14, 26),
            "bg_bottom": (28, 16, 36),
            "accent": (234, 179, 8),      # ذهبي درامي
            "badge_bg": (20, 22, 38, 225),
            "text_main": (252, 250, 245),
        },
        "voices": {
            "narrator": {"voice": "ar-SA-HamedNeural", "rate": "-4%", "pitch": "-2Hz", "label": "🎙️ الراوي"},
            "male_lead": {"voice": "ar-EG-ShakirNeural", "rate": "-2%", "pitch": "+0Hz", "label": "🕯️ بطل القصة"},
            "detective": {"voice": "ar-AE-HamdanNeural", "rate": "-5%", "pitch": "-3Hz", "label": "🕵️ المحقق"},
            "female_lead": {"voice": "ar-JO-SanaNeural", "rate": "-2%", "pitch": "+1Hz", "label": "🌙 البطلة"},
        },
        "genres_rotation": [
            "غموض وجريمة في قصر معزول (بدون عنف دموي - تحقيق ذكي)",
            "تشويق نفسي ورسائل غامضة من الماضي",
            "مغامرة تاريخية ومخطوطة مفقودة في القاهرة القديمة",
            "خيال علمي درامي عن تجربة زمنية غير متوقعة",
        ],
        "env_prefix": "CH1",
        "synthetic_disclosure": True,
    },
    "ch2_en_mystery": {
        "id": "ch2_en_mystery",
        "brand_name": "Untold Science & Enigmas",
        "tagline": "Real Scientific Anomalies, Vanished Expeditions & Deep History",
        "language": "en",
        "aspect_primary": "9:16",     # High-RPM US/UK Shorts + Long compilations
        "also_render_short": False,
        "sound_mood": "dark_sci",
        "palette": {
            "bg_top": (8, 18, 30),
            "bg_bottom": (14, 34, 52),
            "accent": (56, 189, 248),     # Cyan documentary highlight
            "badge_bg": (10, 22, 38, 225),
            "text_main": (248, 250, 252),
        },
        "voices": {
            "narrator": {"voice": "en-US-ChristopherNeural", "rate": "+2%", "pitch": "-2Hz", "label": "🎙️ ARCHIVE HOST"},
            "quote": {"voice": "en-GB-RyanNeural", "rate": "-3%", "pitch": "-2Hz", "label": "📜 EYEWITNESS LOG"},
        },
        "env_prefix": "CH2",
        "synthetic_disclosure": True,
    },
    "ch3_ar_history": {
        "id": "ch3_ar_history",
        "brand_name": "أسرار الحضارات والخرائط",
        "tagline": "وثائقيات التاريخ المدهش والجغرافيا الغريبة والحضارات المفقودة",
        "language": "ar",
        "aspect_primary": "9:16",
        "also_render_short": False,
        "sound_mood": "epic_history",
        "palette": {
            "bg_top": (24, 18, 12),
            "bg_bottom": (44, 28, 16),
            "accent": (245, 158, 11),     # عنبر تاريخي فخم
            "badge_bg": (30, 20, 12, 225),
            "text_main": (254, 249, 239),
        },
        "voices": {
            "narrator": {"voice": "ar-AE-HamdanNeural", "rate": "-3%", "pitch": "-2Hz", "label": "🗺️ السجل التاريخي"},
            "quote": {"voice": "ar-SA-HamedNeural", "rate": "-6%", "pitch": "-3Hz", "label": "📜 وثيقة تاريخية"},
        },
        "env_prefix": "CH3",
        "synthetic_disclosure": True,
    },
    "ch4_riddles": {
        "id": "ch4_riddles",
        "brand_name": "ألغاز المحقق — تحدي الـ 60 ثانية",
        "tagline": "ألغاز ذكاء وتحقيق جنائي تفاعلي — هل تكتشف الخيط المفقود قبل انتهاء الوقت؟",
        "language": "ar",
        "aspect_primary": "9:16",
        "also_render_short": False,
        "sound_mood": "detective_tick",
        "palette": {
            "bg_top": (18, 12, 34),
            "bg_bottom": (38, 16, 52),
            "accent": (16, 185, 129),     # زمردي تفاعلي
            "badge_bg": (22, 14, 42, 230),
            "text_main": (250, 250, 255),
        },
        "voices": {
            "narrator": {"voice": "ar-EG-ShakirNeural", "rate": "+3%", "pitch": "+0Hz", "label": "🕵️ ملف القضية"},
            "witness": {"voice": "ar-EG-SalmaNeural", "rate": "+2%", "pitch": "+1Hz", "label": "💬 شهادة المشتبه"},
        },
        "env_prefix": "CH4",
        "synthetic_disclosure": True,
    },
}
