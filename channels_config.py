# -*- coding: utf-8 -*-
"""
إعدادات القنوات الأربع V4.0 — إمبراطورية الفيديوهات الطويلة (15+ دقيقة) + شورتس وتيك توك التحويل السريع
لكل قناة من القنوات الأربع يتم إنتاج فيديوهين متكاملين في كل حلقة:
1) الفيديو الرئيسي الكامل (15–17 دقيقة أفقياً 16:9): يُنشر على يوتيوب + فيسبوك (تفعيل إعلانات الفواصل Mid-Roll Ads الأعلى ربحاً).
2) الشورت التشويقي الحماسي (60 ثانية رأسياً 9:16): يعرض أقوى لحظة حماسية من نفس الحلقة ويقف عند الذروة مع دعوة صريحة:
   «لسماع الفيديو كامل رابط الفيديو في أول تعليق» — يُنشر على YouTube Shorts + TikTok + Facebook Reels،
   ويضع رابط الفيديو الكامل تلقائياً في أول تعليق لتحويل المشاهدات المليونية السريعة إلى أرباح طويلة!
"""

from typing import Any, Dict

CHANNELS: Dict[str, Dict[str, Any]] = {
    "ch1_eg_karma": {
        "id": "ch1_eg_karma",
        "env_prefix": "CH1",
        "brand_name": "حكايات رد الاعتبار",
        "language": "ar",
        "niche": "eg_social_karma",
        "niche_label_ar": "قصص واقعية درامية ومواقف رد اعتبار ذكية بالعامية المصرية",
        "min_duration_sec": 920,  # 15 دقيقة و20 ثانية كحد أدنى مضمون
        "voice": {
            "engine": "voicetut_female",
            "voicetut_speaker": "Mariam",
            "edge_voice": "ar-EG-SalmaNeural",
            "edge_rate": "+4%",
        },
        "cta_spoken": "استنوا لحظة! اللي حصل بعد كده قلب القاعة كلها رأساً على عقب! عشان تسمعوا الحكاية كاملة وتعرفوا النهاية بالتفصيل، هتلاقوا رابط الفيديو الكامل في أول تعليق تحت الفيديو ده!",
        "cta_banner": "القصة لسه في أولها! 🔥 الفيديو الكامل (16 دقيقة) في أول تعليق 👇",
    },
    "ch2_eg_mystery": {
        "id": "ch2_eg_mystery",
        "env_prefix": "CH2",
        "brand_name": "خفايا وألغاز حقيقية",
        "language": "ar",
        "niche": "eg_detective_mystery",
        "niche_label_ar": "ألغاز واقعية محيّرة وتحقيقات ذكية تكشف المستور خطوة بخطوة بالعامية المصرية",
        "min_duration_sec": 920,
        "voice": {
            "engine": "voicetut_female",
            "voicetut_speaker": "Sarah",
            "edge_voice": "ar-EG-SalmaNeural",
            "edge_rate": "+3%",
        },
        "cta_spoken": "وهنا بالظبط المحقق لمح التفصيلة اللي قلبت القضية كلها! لو عايز تعرف مين اللي عملها وإزاي اتكشف السر بالكامل، ادخل دلوقتي على رابط الفيديو الكامل في أول تعليق!",
        "cta_banner": "سر اللغز الكامل في الفيديو الطويل! 🕵️‍♀️ الرابط في أول تعليق 👇",
    },
    "ch3_en_karma": {
        "id": "ch3_en_karma",
        "env_prefix": "CH3",
        "brand_name": "Karma Chronicles",
        "language": "en",
        "niche": "en_deep_karma",
        "niche_label_ar": "قصص كارما وعدالة درامية طويلة بالإنجليزية (أعلى عائد إعلانات Mid-Roll دولاري)",
        "min_duration_sec": 920,
        "voice": {
            "engine": "chatterbox_en",
            "edge_voice": "en-US-AndrewMultilingualNeural",
            "edge_rate": "+2%",
        },
        "cta_spoken": "Hold on, because what happened five seconds later left the entire room speechless! To hear the full sixteen-minute story and see how it all went down, tap the full video link in the first comment right now!",
        "cta_banner": "WATCH THE FULL 16-MIN STORY! 🔥 Link in the First Comment 👇",
    },
    "ch4_en_mystery": {
        "id": "ch4_en_mystery",
        "env_prefix": "CH4",
        "brand_name": "Untold True Mysteries",
        "language": "en",
        "niche": "en_detective_mystery",
        "niche_label_ar": "قضايا وألغاز غامضة حقيقية بأسلوب تشويقي عالمي بالإنجليزية (RPM دولاري مرتفع)",
        "min_duration_sec": 920,
        "voice": {
            "engine": "chatterbox_en",
            "edge_voice": "en-US-BrianMultilingualNeural",
            "edge_rate": "+2%",
        },
        "cta_spoken": "And right there was the one impossible detail nobody could explain! To hear how investigators cracked the entire mystery step by step, check the full video link pinned in the first comment!",
        "cta_banner": "HEAR THE FULL INVESTIGATION! 🕵️‍♂️ Full Video Link in First Comment 👇",
    },
}
