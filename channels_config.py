# -*- coding: utf-8 -*-
"""
إمبراطورية القنوات الترفيهية السينمائية V2.0 (Netflix-Style Audio-Visual Entertainment Studio)
- أصوات بودكاست وتمثيل مصري طبيعي 100% (VoiceTut-TTS المدرب على 380 ساعة بودكاست مصري) + Chatterbox الإنجليزي التمثيلي.
- مشاهد سينمائية واقعية 35mm متجددة مع كل جملة (FLUX.1-schnell بدون علامات مائية) + مطر وبرق وحركة كاميرا.
- بيانو درامي وتشيلو ومؤثرات صوتية حقيقية (خبط باب، نبض قلب، رعد، خطوات، كاسيت) — صفر إحساس مذاكرة!
"""

CHANNELS = {
    "ch1_novels": {
        "id": "ch1_novels",
        "brand_name": "الليلة التالتة — روايات مسموعة",
        "tagline": "حكايات غموض وإثارة مصرية بالعامية السينمائية — كل ليلة حلقة تشدك لآخر ثانية",
        "language": "ar_eg",
        "aspect_primary": "16:9",
        "also_render_short": True,
        "music_key": "thriller_piano",
        "subtitle_color": (255, 218, 68),  # أصفر سينمائي كلاسيكي مثل نتفليكس
        "voices": {
            "narrator": {
                "engine": "voicetut",
                "speaker": "Hassan",
                "speed": 1.02,
                "fallback_edge": "ar-EG-ShakirNeural",
            },
            "male_lead": {
                "engine": "voicetut",
                "speaker": "Yehia",
                "speed": 1.03,
                "fallback_edge": "ar-EG-ShakirNeural",
            },
            "mystery_man": {
                "engine": "voicetut",
                "speaker": "Tareq",
                "speed": 0.96,
                "tape_fx": True,  # فلتر شريط كاسيت/مكالمة غامضة عند اللزوم
                "fallback_edge": "ar-AE-HamdanNeural",
            },
            "female_lead": {
                "engine": "voicetut",
                "speaker": "Mariam",
                "speed": 1.02,
                "fallback_edge": "ar-EG-SalmaNeural",
            },
        },
        "genres_rotation": [
            "غموض وإثارة نفسية في شقة قديمة بوسط البلد — سر شريط كاسيت أو غرفة مغلقة",
            "جريمة ذكية ولغز اختفاء غامض في قطار الليل المتجه للإسكندرية",
            "حكاية فندق مهجور على البحر فيه أوضة رقمها ممسوح من السجلات",
            "خيال درامي مشوق: مكالمة تليفون بتوصلك من نفسك بعد 5 سنين",
        ],
        "env_prefix": "CH1",
    },
    "ch2_en_mystery": {
        "id": "ch2_en_mystery",
        "brand_name": "Dark File Stories",
        "tagline": "Gripping Midnight True Mysteries & Vanished Expeditions",
        "language": "en",
        "aspect_primary": "9:16",
        "also_render_short": False,
        "music_key": "dark_pulse_piano",
        "subtitle_color": (255, 230, 90),
        "voices": {
            "narrator": {
                "engine": "chatterbox",
                "exaggeration": 0.62,
                "fallback_edge": "en-US-ChristopherNeural",
            },
            "witness": {
                "engine": "voicetut_en",
                "speaker": "Karim",
                "speed": 0.98,
                "fallback_edge": "en-GB-RyanNeural",
            },
        },
        "env_prefix": "CH2",
    },
    "ch3_ar_history": {
        "id": "ch3_ar_history",
        "brand_name": "كواليس التاريخ الممنوع",
        "tagline": "قصص حقيقية مذهلة وأسرار مدن وكنوز اختفت في ظروف غامضة",
        "language": "ar_eg",
        "aspect_primary": "9:16",
        "also_render_short": False,
        "music_key": "ancient_mystery",
        "subtitle_color": (255, 218, 68),
        "voices": {
            "narrator": {
                "engine": "voicetut",
                "speaker": "Ahmed",
                "speed": 1.03,
                "fallback_edge": "ar-EG-ShakirNeural",
            },
            "witness": {
                "engine": "voicetut",
                "speaker": "Shaker",
                "speed": 0.97,
                "fallback_edge": "ar-SA-HamedNeural",
            },
        },
        "env_prefix": "CH3",
    },
    "ch4_riddles": {
        "id": "ch4_riddles",
        "brand_name": "مسرح الجريمة — مين الكداب؟",
        "tagline": "قضية في 60 ثانية وغلطه واحدة كشفت المجرم — تقدر تطلعها؟",
        "language": "ar_eg",
        "aspect_primary": "9:16",
        "also_render_short": False,
        "music_key": "crime_clock",
        "subtitle_color": (255, 230, 90),
        "voices": {
            "narrator": {
                "engine": "voicetut",
                "speaker": "Youssef",
                "speed": 1.05,
                "fallback_edge": "ar-EG-ShakirNeural",
            },
            "suspect_m": {
                "engine": "voicetut",
                "speaker": "Ramy",
                "speed": 1.02,
                "fallback_edge": "ar-AE-HamdanNeural",
            },
            "suspect_f": {
                "engine": "voicetut",
                "speaker": "Yara",
                "speed": 1.03,
                "fallback_edge": "ar-EG-SalmaNeural",
            },
        },
        "env_prefix": "CH4",
    },
}
