# -*- coding: utf-8 -*-
"""
إمبراطورية الشورتس الفيروسية المريحة للأعصاب V3.0 (Viral Satisfying Karma Storytime Empire)
نفس الفورمولا المليونية المجربة 100%:
- فيديوهات حقيقية 1080p مريحة للأعصاب (بناء طوب مصغر، تزيين كيك، فخار، طبخ جريل، صابون) تتبدل كل 13 ثانية.
- قصص رد اعتبار ومواقف ذكية تفرّح القلب وتشد المشاهد لآخر ثانية عشان يسمع ضربة الذكاء في النهاية.
- القناة المصرية بصوت البنت المصرية الطبيعي السريع، والقناة الإنجليزية بصوت أمريكي طبيعي لأعلى ربح دولاري.
- كلمة بكلمة في نص الشاشة بالمللي ثانية عبر Groq Whisper-Large-V3-Turbo.
"""

CHANNELS = {
    "ch1_eg_karma": {
        "id": "ch1_eg_karma",
        "brand_name": "مواقف قلبت الترابيزة",
        "language": "ar",
        "story_type": "eg_clever_karma",
        "voice": {
            "engine": "voicetut",
            "speaker": "Mariam",
            "fallback_edge": "ar-EG-SalmaNeural",
            "speed": 1.08,
        },
        "env_prefix": "CH1",
    },
    "ch2_en_karma": {
        "id": "ch2_en_karma",
        "brand_name": "Instant Karma Stories",
        "language": "en",
        "story_type": "en_clever_karma",
        "voice": {
            "engine": "chatterbox",
            "exaggeration": 0.55,
            "fallback_edge": "en-US-AndrewNeural",
            "speed": 1.07,
        },
        "env_prefix": "CH2",
    },
    "ch3_eg_twists": {
        "id": "ch3_eg_twists",
        "brand_name": "حكايات متتصدقش",
        "language": "ar",
        "story_type": "eg_smart_twist",
        "voice": {
            "engine": "voicetut",
            "speaker": "Sarah",
            "fallback_edge": "ar-EG-SalmaNeural",
            "speed": 1.08,
        },
        "env_prefix": "CH3",
    },
    "ch4_en_workplace": {
        "id": "ch4_en_workplace",
        "brand_name": "Clever Comebacks",
        "language": "en",
        "story_type": "en_malicious_compliance",
        "voice": {
            "engine": "chatterbox",
            "exaggeration": 0.58,
            "fallback_edge": "en-US-BrianNeural",
            "speed": 1.07,
        },
        "env_prefix": "CH4",
    },
}
