# -*- coding: utf-8 -*-
"""
إعدادات القنوات الأربع V6.0 — إمبراطورية الإثارة النفسية والألغاز الفيروسية (15+ دقيقة + شورتس وتيك توك)
كل قناة تنتج يومياً بشكل مستقل 100%:
1) فيلم حلقة كامل (16–18 دقيقة، 16:9 HD) ليوتيوب وفيسبوك (لتفعيل إعلانات الفواصل المتعددة Mid-Roll Ads).
2) فيديو شورت تشويقي ناري (60–75 ثانية، 9:16 HD) ليوتيوب شورتس وتيك توك، يقف في ذروة الصدمة
   ويوجّه المشاهد صوتياً وبصرياً إلى رابط الفيلم الكامل في أول تعليق!
"""

from typing import Any, Dict

CHANNELS: Dict[str, Dict[str, Any]] = {
    "ch1_eg_thriller": {
        "id": "ch1_eg_thriller",
        "env_prefix": "CH1",
        "brand_name": "أسرار الليل ورد الاعتبار",
        "language": "ar",
        "niche": "eg_psych_thriller",
        "min_duration_sec": 940,
        "voice": {
            "gemini_voice": "Kore",
            "voicetut_speaker": "Mariam",
            "edge_voice": "ar-EG-SalmaNeural",
            "edge_rate": "+4%",
        },
        "cta_spoken": "ثانية واحدة! إنتوا متخيلين مين اللي طلع ورا الباب وإزاي اتقلبت الترابيزة عليهم بالصوت والصورة؟ الصدمة اللي جاية مستحيل تخطر على بال بشر! عشان تسمعوا القصة كاملة من غير ما تاخدوا نفسكم، ادخلوا حالاً على رابط الفيديو الكامل في أول تعليق!",
        "cta_banner": "باقي القصة الصادمة في الفيديو الكامل! الرابط في أول تعليق",
    },
    "ch2_eg_mystery": {
        "id": "ch2_eg_mystery",
        "env_prefix": "CH2",
        "brand_name": "ملفات محيّرة لا تُصدّق",
        "language": "ar",
        "niche": "eg_impossible_mystery",
        "min_duration_sec": 940,
        "voice": {
            "gemini_voice": "Aoede",
            "voicetut_speaker": "Sarah",
            "edge_voice": "ar-EG-SalmaNeural",
            "edge_rate": "+4%",
        },
        "cta_spoken": "استنوا لحظة! اللغز اللي طلع مستخبي ورا التفصيلة دي صدم المهندسين والمباحث نفسهم! عشان تعرفوا السر الكامل خطوة بخطوة، ادخلوا حالاً على رابط الفيديو الكامل في أول تعليق!",
        "cta_banner": "سر اللغز الكامل في الفيديو الطويل! الرابط في أول تعليق",
    },
    "ch3_en_thriller": {
        "id": "ch3_en_thriller",
        "env_prefix": "CH3",
        "brand_name": "Midnight Twist Stories",
        "language": "en",
        "niche": "en_psych_thriller",
        "min_duration_sec": 940,
        "voice": {
            "gemini_voice": "Puck",
            "orpheus_voice": "troy",
            "edge_voice": "en-US-AndrewMultilingualNeural",
            "edge_rate": "+2%",
        },
        "cta_spoken": "Hold on, because how the entire trap snapped shut before sunrise left their own lawyers speechless! Watch the full sixteen minute story right now from the link pinned in the first comment!",
        "cta_banner": "FULL 16-MIN STORY IN THE FIRST COMMENT!",
    },
    "ch4_en_mystery": {
        "id": "ch4_en_mystery",
        "env_prefix": "CH4",
        "brand_name": "Unsolved & Impossible",
        "language": "en",
        "niche": "en_impossible_mystery",
        "min_duration_sec": 940,
        "voice": {
            "gemini_voice": "Charon",
            "orpheus_voice": "daniel",
            "edge_voice": "en-US-BrianMultilingualNeural",
            "edge_rate": "+2%",
        },
        "cta_spoken": "Wait until you hear what investigators uncovered next and how the entire impossible mystery unraveled! Tap the full sixteen minute investigation link in the first comment right now!",
        "cta_banner": "WATCH THE FULL 16-MIN INVESTIGATION IN FIRST COMMENT!",
    },
}
