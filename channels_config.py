# -*- coding: utf-8 -*-
"""
إعدادات القنوات الأربع V8.0 (Production Locked — 12/12 Verified Zernio Account IDs):
1) القناة 1 (دفتر راوي — @daftarrawi): روايات وحكايات مصرية كاملة ومتنوعة كل يوم.
2) القناة 2 (الدليل الأخير — @eldalilelakhir): قصص ألغاز وتحقيقات بوليسية ذكية كاملة على طريقة «المحقق كونان».
3) القناة 3 (Velvet Tales — @velvettalesclub): قصص وروايات إنجليزية متنوعة وممتعة بـ RPM دولاري عالٍ.
4) القناة 4 (Mindlock — @mindlockcases): قصص تحقيقات وألغاز ذكية كاملة بالإنجليزية بـ RPM دولاري عالٍ.

كل قناة تنتج وتنشر يومياً بشكل مستقل 100%:
- فيلم حلقة كامل (+16 دقيقة، 16:9 HD) -> يوتيوب + فيسبوك.
- 2 شورتس تشويقيين مختلفين (9:16 HD) لنفس الحلقة يومياً -> يوتيوب شورتس + تيك توك (الأول فوراً والثاني بعد 3 ساعات) مع رابط الفيلم الكامل في أول تعليق!
"""

from typing import Any, Dict

CHANNELS: Dict[str, Dict[str, Any]] = {
    "ch1_eg_thriller": {
        "id": "ch1_eg_thriller",
        "env_prefix": "CH1",
        "brand_name": "دفتر راوي",
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
        "min_duration_sec": 940,
        "voice": {
            "gemini_voice": "Kore",
            "voicetut_speaker": "Mariam",
            "edge_voice": "ar-EG-SalmaNeural",
            "edge_rate": "+4%",
        },
        "cta_spoken": "ثانية واحدة! اللي حصل بعد اللحظة دي بالظبط محدش فيكم ممكن يتوقعه أبداً! عشان تسمعوا الرواية كاملة من أولها لآخرها، ادخلوا حالاً على رابط الفيديو الكامل في أول تعليق!",
        "cta_banner": "اسمع الرواية كاملة (+16 دقيقة)! الرابط في أول تعليق",
    },
    "ch2_eg_mystery": {
        "id": "ch2_eg_mystery",
        "env_prefix": "CH2",
        "brand_name": "الدليل الأخير",
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
        "min_duration_sec": 940,
        "voice": {
            "gemini_voice": "Aoede",
            "voicetut_speaker": "Sarah",
            "edge_voice": "ar-EG-SalmaNeural",
            "edge_rate": "+4%",
        },
        "cta_spoken": "استنوا لحظة! تفتكروا مين فيهم صاحب الخدعة وإيه التفصيلة الصغيرة اللي فضحت اللغز كله؟ عشان تشوفوا الحل العبقري للقضية كاملة، ادخلوا حالاً على رابط الفيديو الكامل في أول تعليق!",
        "cta_banner": "حل اللغز الكامل في الفيديو الطويل! الرابط في أول تعليق",
    },
    "ch3_en_thriller": {
        "id": "ch3_en_thriller",
        "env_prefix": "CH3",
        "brand_name": "Velvet Tales",
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
        "min_duration_sec": 940,
        "voice": {
            "gemini_voice": "Puck",
            "orpheus_voice": "troy",
            "edge_voice": "en-US-AndrewMultilingualNeural",
            "edge_rate": "+2%",
        },
        "cta_spoken": "Hold on, because nobody in that room saw what happened in the next five minutes coming! Watch the full sixteen minute story right now from the link pinned in the first comment!",
        "cta_banner": "FULL 16-MIN STORY IN THE FIRST COMMENT!",
    },
    "ch4_en_mystery": {
        "id": "ch4_en_mystery",
        "env_prefix": "CH4",
        "brand_name": "Mindlock",
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
        "min_duration_sec": 940,
        "voice": {
            "gemini_voice": "Charon",
            "orpheus_voice": "daniel",
            "edge_voice": "en-US-BrianMultilingualNeural",
            "edge_rate": "+2%",
        },
        "cta_spoken": "Freeze right there—can you spot the one tiny contradiction that shattered the alibi? Watch the full sixteen minute mystery unfold from the link in the first comment!",
        "cta_banner": "SOLVE THE FULL 16-MIN CASE IN FIRST COMMENT!",
    },
}
