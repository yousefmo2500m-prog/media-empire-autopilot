# -*- coding: utf-8 -*-
"""
إعدادات القنوات الأربع V10.0 (Algorithm & 8-Second FLUX Cinema Masterpiece Edition):
- تثبيت الصوت البشري المتفق عليه بنسبة 100% (صوت الراوية المصرية الدافئة Kore للعربي، وتخصيص أصوات مميزة للإنجليزي) مع حظر الأصوات الآلية (edge_tts) نهائياً للأبد!
- تغيير المشهد البصري كل ~8 ثوانٍ بصورة FLUX سينمائية جديدة كلياً مطابقة للجملة المنطوقة في تلك اللحظة بدون تكرار أي صورة مرتين!
- تفعيل حزمة الخوارزميات الكاملة (SEO Hook + 18 Tags + فصول يوتيوب غير حارقة + سؤال جدلي للتعليقات + غلاف يوتيوب فائق الجاذبية).
"""

from typing import Any, Dict, List

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
        "min_duration_sec": 945,
        "shot_interval_sec": 8.0,
        "thumb_badge": "قصة حقيقية تحبس الأنفاس",
        "base_tags": [
            "قصص واقعية", "حكايات مصرية", "غموض نفسي", "قصص مثيرة", "دفتر راوي",
            "قصة حقيقية", "اسرار غامضة", "تشويق واثارة", "قصص قبل النوم", "روايات مسموعة",
        ],
        "voice": {
            "gemini_voice": "Kore",
            "mood": "thriller",
        },
        "cta_spoken_1": "ثانية واحدة بس! إنت متخيل اللي شافه أول ما فتح الباب في اللحظة دي؟ الصدمة اللي حصلت بعدها قلبت كل حاجة! ادخل حالاً اسمع القصة كاملة من الرابط المثبت في أول تعليق!",
        "cta_spoken_2": "اقف هنا! لأن التفصيلة اللي ظهرت بعد الجملة دي بالظبط نسفت كل اللي فات! كمل الحكاية كاملة دلوقتي من الرابط الموجود في أول تعليق!",
        "cta_banner": "القصة الكاملة (+16 دقيقة) في أول تعليق!",
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
        "min_duration_sec": 945,
        "shot_interval_sec": 8.0,
        "thumb_badge": "لغز مستحيل الحل",
        "base_tags": [
            "الغاز بوليسية", "قضايا غامضة", "الدليل الاخير", "تحقيقات ذكية", "لغز الغرفة المغلقة",
            "المحقق كونان", "قصص غموض", "الغاز للاذكياء", "كشف الجاني", "قصص تحقيقات",
        ],
        "voice": {
            "gemini_voice": "Kore",
            "mood": "mystery",
        },
        "cta_spoken_1": "استنى عند التفصيلة دي! تفتكر إزاي ده حصل والباب مقفول بالمفتاح من جوه؟ عشان تشوف التحقيق كامل وكشف الخدعة خطوة بخطوة، ادخل حالاً على رابط الفيديو الكامل في أول تعليق!",
        "cta_spoken_2": "لحظة واحدة! الغلطة الصغيرة دي هي اللي وقعت الجاني اللي محدش شك فيه! شوف الحل الكامل للقضية دلوقتي من الرابط في أول تعليق!",
        "cta_banner": "حل القضية الكامل (+16 دقيقة) في أول تعليق!",
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
        "min_duration_sec": 945,
        "shot_interval_sec": 8.0,
        "thumb_badge": "TRUE CHILLING TWIST",
        "base_tags": [
            "psychological thriller", "true scary stories", "mystery stories", "plot twist story",
            "storytime", "chilling stories", "velvet tales", "suspense audio story", "late night stories",
        ],
        "voice": {
            "gemini_voice": "Aoede",
            "orpheus_voice": "tara",
            "mood": "thriller",
        },
        "cta_spoken_1": "Stop right there—because what was waiting on the other side of that door shattered everything they believed! Watch the full sixteen minute story unfold right now from the link pinned in the first comment!",
        "cta_spoken_2": "Hold on—because the next ten seconds flipped the entire truth upside down! Hear the full sixteen minute story right now via the link in the first comment!",
        "cta_banner": "WATCH THE FULL 16-MIN STORY IN FIRST COMMENT!",
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
        "min_duration_sec": 945,
        "shot_interval_sec": 8.0,
        "thumb_badge": "IMPOSSIBLE ALIBI",
        "base_tags": [
            "detective mystery", "locked room mystery", "whodunit", "impossible crime",
            "mindlock cases", "murder mystery puzzle", "true detective story", "alibi riddle",
        ],
        "voice": {
            "gemini_voice": "Charon",
            "orpheus_voice": "daniel",
            "mood": "mystery",
        },
        "cta_spoken_1": "Freeze right at that clue—did you catch the one impossible contradiction inside that room? Watch the full sixteen minute investigation from the link pinned in the first comment!",
        "cta_spoken_2": "Wait right there—because that tiny detail just exposed the one suspect with an ironclad alibi! Solve the full case right now from the link in the first comment!",
        "cta_banner": "SOLVE THE FULL 16-MIN CASE IN FIRST COMMENT!",
    },
}
