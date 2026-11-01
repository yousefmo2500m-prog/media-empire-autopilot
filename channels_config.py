# -*- coding: utf-8 -*-
"""
إعدادات القنوات الأربع V7.5 — أسماء براندات جذابة ومحتوى متجدد غير متوقع يمنع ملل المشاهد نهائياً:
1) القناة 1 (شريط حكايات): روايات وحكايات مصرية كاملة ومتنوعة كل يوم (كوميدي ذكي، اجتماعي مشوق، مفاجآت غير متوقعة، إثارة، دراما إنسانية).
2) القناة 2 (الخيط الخفي): قصص ألغاز وتحقيقات بوليسية ذكية كاملة على طريقة «المحقق كونان وأجاثا كريستي» بالعامية المصرية (مشتبه بهم، حيل ذكية، أدلة خفية، واستنتاج مذهل).
3) القناة 3 (OffScript Stories): قصص وروايات إنجليزية متنوعة وممتعة (مواقف كوميدية ذكية، دراما، مفاجآت حياتية، تشويق) بـ RPM دولاري عالٍ.
4) القناة 4 (The Alibi Room): قصص تحقيقات وألغاز ذكية كاملة بالإنجليزية (Whodunit & Clever Mysteries) بـ RPM دولاري عالٍ.

كل قناة تنتج يومياً:
- فيلم حلقة كامل (+16 دقيقة، 16:9 HD) ليوتيوب وفيسبوك.
- 2 شورتس تشويقيين مختلفين (9:16 HD) لنفس الحلقة يومياً ليوتيوب شورتس وتيك توك مع رابط الفيلم الكامل في أول تعليق!
"""

from typing import Any, Dict

CHANNELS: Dict[str, Dict[str, Any]] = {
    "ch1_eg_thriller": {
        "id": "ch1_eg_thriller",
        "env_prefix": "CH1",
        "brand_name": "شريط حكايات",
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
        "brand_name": "الخيط الخفي",
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
        "brand_name": "OffScript Stories",
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
        "brand_name": "The Alibi Room",
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
