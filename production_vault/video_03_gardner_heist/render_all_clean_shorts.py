# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CACHE_DIR = Path("/home/user/.cache/shorts_temp")
SHORTS_DIR = Path("/home/user/shorts")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
SHORTS_DIR.mkdir(parents=True, exist_ok=True)

CAIRO_FONT = "/home/user/media-empire-autopilot/fonts/Cairo-Variable.ttf"
VID_SRC = "/home/user/.cache/pure_master_video.mp4"
DRONE_SRC = "/home/user/.cache/eng_drone.wav"

SHORTS_DATA = [
    {
        "id": 1,
        "slug": "short_01_the_midnight_blunder",
        "title": "أغبى خطأ أمني في التاريخ!",
        "subtitle": "سرقة الـ 500 مليون دولار | متحف جاردنر",
        "script": (
            "في ليلة واحدة، حارس أمن عمره 23 سنة ارتكب أغبى غلطة في تاريخ المتاحف، وكلفت العالم نصف مليار دولار! "
            "الساعة 1:24 فجر 18 مارس 1990، رن جرس الإنتركم في متحف جاردنر في بوسطن.. "
            "ضابطين شرطة قالوا للحارس: عندنا بلاغ شغب ولازم ندخل نفتش! "
            "الحارس كسر أول قاعدة أمنية وفتح الباب.. وأول ما دخلوا قالوله: انت مطلوب للقبض عليك! "
            "وقبل ما يستوعب، كان متكلبش في القبو وشريط لاصق على وشه! دي كانت بداية أكبر سرقة في التاريخ.. "
            "تفتكر الحارس كان متواطئ معاهم ولا غبي بجد؟"
        ),
        "video_start": 23.77,
    },
    {
        "id": 2,
        "slug": "short_02_the_250m_vermeer",
        "title": "أغلى لوحة مسروقة في العالم!",
        "subtitle": "لوحة فيرمير بقيمة ربع مليار دولار",
        "script": (
            "تخيل لوحة فنية مساحتها متعديش حجم شاشة لابتوب، تمنها لوحدها ربع مليار دولار! "
            "لوحة الحفلة الموسيقية للفنان يوهانس فيرمير، واحدة من أندر 34 لوحة سابهم فيرمير في تاريخه كله.. "
            "اللصين انتزعوها من متحف جاردنر في بوسطن واختفت تماماً من سنة 1990! "
            "الـ FBI أعلن إن اللوحة دي بالذات غير قابلة للبيع في أي سوق سوداء، لأن أي حد هيحاول يبيعها هيتم كشفه فوراً! "
            "الـ FBI حاطط مكافأة 10 مليون دولار لأي معلومة.. تفتكر اللوحة لسه سليمة ولا اتدمرت للأبد؟"
        ),
        "video_start": 108.90,
    },
    {
        "id": 3,
        "slug": "short_03_slashing_rembrandt",
        "title": "أبشع جريمة في تاريخ الفن!",
        "subtitle": "تمزيق تحفة رامبرانت النادرة بالمشرط",
        "script": (
            "في الليلة دي، اللصوص معندهمش أي احترام للفن.. ارتكبوا جريمة خلت مؤرخي الفن في العالم يبكوا دم! "
            "لوحة عاصفة على بحر الجليل للفنان رامبرانت.. اللوحة البحرية الوحيدة اللي رسمها في حياته كلها، وتمنها أكتر من 150 مليون دولار.. "
            "لأن البرواز كان تقيل ومش عارفين يفكوه بسرعة، طلعوا مشارط حادة ومزقوا القماش الخام وسابوا أطراف اللوحة مقطعة ومرمية في الأرض! "
            "جريمة دمرت تحفة تاريخية لا تعوض.. تفتكر كان فيه حد طلب منهم اللوحة دي بالاسم؟"
        ),
        "video_start": 82.00,
    },
    {
        "id": 4,
        "slug": "short_04_the_81_minute_ghost",
        "title": "لغز الـ 81 دقيقة الغامضة!",
        "subtitle": "سرقة بدون أثر وسر شريط الـ VHS",
        "script": (
            "أغرب حاجة في سرقة متحف جاردنر مش الفلوس.. أغرب حاجة هي الوقت والبرود العصبي! "
            "اللصين فضلوا جوه المتحف 81 دقيقة كاملة! بيتجولوا براحتهم بين الأدوار، بيختاروا اللوحات وينزعوها كأنهم بيتسوقوا في سوبرماركت! "
            "وقبل ما يهربوا، دخلوا غرفة الأمن وسحبوا كاسيت الفيديو الوحيد اللي سجل دخولهم وخروجهم! "
            "السؤال اللي حير المباحث الفيدرالية 34 سنة: إزاي لصين عادين عرفوا مكان كاسيت التسجيل الوحيد في مبنى ضخم زي ده؟"
        ),
        "video_start": 118.00,
    },
    {
        "id": 5,
        "slug": "short_05_morning_shock_fbi",
        "title": "صدمة الصباح: اختفاء الكنز!",
        "subtitle": "وصول الـ FBI وبراويز خاوية في كل مكان",
        "script": (
            "الساعة سبعة الصبح، وصل حراس الوردية الصباحية لمتحف جاردنر.. لكن الباب كان موارب، والصمت مرعب! "
            "الحراس دخلوا يجري على غرفة المراقبة.. مالقوش الحراس، وشاشات المراقبة مشوشة! "
            "لما نزلوا القبو، لقوا الحارسين متكلبشين في مواسير البخار وشريط لاصق على عيونهم بقالهم 6 ساعات! "
            "ولما طلعوا صالات العرض كانت الصدمة الكبرى: 13 تحفة فنية قيمتها 500 مليون دولار اختفت! "
            "لحظة أعلنت بداية أكبر تحقيق في تاريخ الـ FBI!"
        ),
        "video_start": 138.36,
    },
    {
        "id": 6,
        "slug": "short_06_mafia_murders",
        "title": "تصفيات المافيا الإيطالية!",
        "subtitle": "كل من حاول الكلام.. تمت تصفيته برصاصة",
        "script": (
            "سرقة متحف جاردنر مرتبطة بسلسلة اغتيالات غامضة حيرت أمريكا كلها! "
            "الـ FBI اكتشف إن كل خيط يقرب من اللوحات، بينتهي بجثة برصاصة في الرأس! "
            "بوبي دوناتي، عضو المافيا المشتبه الرئيسي، اتقتل بوحشية واترمى في شنطة عربية بعد السرقة بشهور.. "
            "روبرت جورانتي، اللي كان معاه اللوحات حسب شهود، مات في ظروف غامضة.. "
            "هل المافيا قتلت كل اللي يعرفوا السر علشان اللوحات تفضل مخفية للأبد؟"
        ),
        "video_start": 174.90,
    },
    {
        "id": 7,
        "slug": "short_07_empty_frames_curse",
        "title": "سر البراويز الفارغة للأبد!",
        "subtitle": "وصية إيزابيلا جاردنر التي تمنع لمس الجدران",
        "script": (
            "لو زرت متحف إيزابيلا جاردنر في بوسطن النهارده، هتشوف أغرب منظر في العالم: براويز دهبية ضخمة معلقة على الحيطان.. بس فارغة تماماً! "
            "السبب وصية حديدية كتبتها مؤسسة المتحف إيزابيلا جاردنر سنة 1924: "
            "لو اتغير مكان أي قطعة فنية أو اتشال أي برواز، المتحف يتقفل وتتباع كل محتوياته في باريس لصالح هارفارد! "
            "إدارة المتحف سايبة البراويز فارغة بقالها 34 سنة كرمز للأمل وإن اللوحات هترجع في يوم من الأيام! تفتكر هترجع؟"
        ),
        "video_start": 205.19,
    },
    {
        "id": 8,
        "slug": "short_08_10m_bounty",
        "title": "مكافأة 10 مليون دولار كاش!",
        "subtitle": "أكبر مكافأة مالية خاصة في تاريخ البشرية",
        "script": (
            "عشرة ملايين دولار كاش.. دي مش جايزة يانصيب، دي أكبر مكافأة خاصة رصدتها مؤسسة في تاريخ البشرية! "
            "متحف جاردنر والـ FBI حاطين 10 مليون دولار لأي شخص يقدم معلومة تؤدي لاستعادة الـ 13 لوحة، "
            "وبدون أي ملاحقة قضائية أو أسئلة عن هويتك! "
            "لو اللوحات دي مدفونة أو منسية في قبو، اللي هيلاقيها هيتحول لمليونير في ثانية واحدة.. "
            "لو انت لقيتهم، هتسلمهم ولا هتخاف من انتقام المافيا؟"
        ),
        "video_start": 210.00,
    },
    {
        "id": 9,
        "slug": "short_09_where_are_paintings",
        "title": "أين اختفت لوحات النصف مليار؟",
        "subtitle": "لغز القبو الخرساني وقصر الملياردير السري",
        "script": (
            "أين اختفت 13 تحفة فنية تساوي 500 مليون دولار بدون أي أثر طوال 34 سنة؟ "
            "الـ FBI فتش مئات البيوت في بوسطن وفلوريدا.. وفي سنة 2010 حفروا جنينة قصر رجل عصابات بالكامل برادارات تخترق الأرض "
            "بعد إشاعة إن اللوحات مدفونة في قبو خرساني تحت الأرض ضد الرطوبة! "
            "وفي فرضية تانية: إن اللوحات اتباعت في مزاد سري لملياردير غامض محتفظ بيها في قصر محصن! "
            "تفتكر اللوحات لسه تحت التراب ولا في قصر سري؟"
        ),
        "video_start": 160.00,
    },
    {
        "id": 10,
        "slug": "short_10_greatest_mystery",
        "title": "أعظم لغز في تاريخ البشرية!",
        "subtitle": "34 عاماً من التحقيقات بدون استعادة لوحة واحدة",
        "script": (
            "34 سنة كاملة مرت.. آلاف التحقيقات، ملايين الوثائق، وعشرات المشتبه بهم ماتوا أو اتقتلوا.. "
            "ومفيش خيط واحد قاد لاستعادة سنتيمتر واحد من اللوحات! "
            "سرقة متحف جاردنر مش مجرد جريمة.. دي اللغز الفني الأكبر في التاريخ المعاصر! "
            "هل هيجي يوم واللوحات تظهر فجأة؟ ولا السر مات مع اللصوص في القبور؟ "
            "اكتب رأيك في التعليقات واشترك لمتابعة أغرب قضايا العالم الغامضة!"
        ),
        "video_start": 0.00,
    },
]

def make_header_png(short_info):
    im = Image.new('RGBA', (1080, 220), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    bx, by, bw, bh = 50, 25, 980, 160
    d.rounded_rectangle([bx+4, by+4, bx+bw+4, by+bh+4], radius=20, fill=(0, 0, 0, 220))
    d.rounded_rectangle([bx, by, bx+bw, by+bh], radius=20, fill=(220, 20, 20), outline=(255, 215, 0), width=4)

    f_title = ImageFont.truetype(CAIRO_FONT, 46)
    t1 = short_info["title"]
    bbox1 = f_title.getbbox(t1, direction='rtl')
    tw1 = bbox1[2] - bbox1[0]
    d.text((bx + (bw - tw1)//2, by + 18), t1, fill=(255, 255, 255), font=f_title, direction='rtl')

    f_sub = ImageFont.truetype(CAIRO_FONT, 32)
    t2 = short_info["subtitle"]
    bbox2 = f_sub.getbbox(t2, direction='rtl')
    tw2 = bbox2[2] - bbox2[0]
    d.text((bx + (bw - tw2)//2, by + 92), t2, fill=(255, 225, 20), font=f_sub, direction='rtl')

    out_p = CACHE_DIR / f"{short_info['slug']}_hdr.png"
    im.save(out_p)
    return out_p

def split_text_into_cues(text):
    raw_parts = re.split(r'([!؟،\.\n]+)', text)
    cues = []
    current = ""
    for p in raw_parts:
        if not p.strip():
            continue
        if p in ["!", "؟", "،", ".", "\n"]:
            current += p
            if len(current.split()) >= 4:
                cues.append(current.strip())
                current = ""
        else:
            if current and len((current + " " + p).split()) > 8:
                cues.append(current.strip())
                current = p
            else:
                current = (current + " " + p).strip() if current else p
    if current.strip():
        cues.append(current.strip())
    return cues

def make_ass_subtitles(short_info, duration):
    cues = split_text_into_cues(short_info["script"])
    if not cues:
        cues = [short_info["script"]]
        
    line_dur = duration / max(1, len(cues))
    events = []
    curr_t = 0.0
    for s in cues:
        end_t = min(duration, curr_t + line_dur)
        m_s, sec_s = divmod(curr_t, 60)
        h_s, m_s = divmod(m_s, 60)
        t_start_str = f"{int(h_s)}:{int(m_s):02d}:{sec_s:05.2f}"
        
        m_e, sec_e = divmod(end_t, 60)
        h_e, m_e = divmod(m_e, 60)
        t_end_str = f"{int(h_e)}:{int(m_e):02d}:{sec_e:05.2f}"
        
        events.append(f"Dialogue: 0,{t_start_str},{t_end_str},Default,,0,0,0,,{s}")
        curr_t = end_t
        
    ass_text = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Cairo,58,&H000FEBF5,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,5,3,2,60,60,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(events) + "\n"

    ass_path = CACHE_DIR / f"{short_info['slug']}.ass"
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_text)
    return ass_path

def get_audio_dur(aud_path):
    proc = subprocess.run(["ffmpeg", "-i", str(aud_path)], capture_output=True, text=True)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", proc.stderr)
    if not m:
        return 35.0
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))

def render_short_video(short_info):
    aud_path = CACHE_DIR / f"{short_info['slug']}_kore.mp3"
    dur = get_audio_dur(aud_path)
    out_mp4 = SHORTS_DIR / f"{short_info['slug']}.mp4"
    
    hdr_path = make_header_png(short_info)
    ass_path = make_ass_subtitles(short_info, dur)
    
    start_sec = short_info["video_start"]
    
    filter_complex = (
        "[0:v]scale=135:240:force_original_aspect_ratio=increase,crop=135:240,boxblur=4:1,scale=1080:1920,eq=brightness=-0.15[bg];"
        "[0:v]scale=1080:608[fg];"
        "[fg]drawbox=x=0:y=0:w=1080:h=608:color=gold@0.8:t=3[fg_bordered];"
        "[bg][fg_bordered]overlay=0:656[vmid];"
        "[vmid][1:v]overlay=0:80[vhdr];"
        f"[vhdr]ass={ass_path}[vout];"
        "[2:a]volume=1.0[voice];"
        "[3:a]volume=0.18[drone];"
        "[voice][drone]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec), "-t", f"{dur:.2f}", "-i", VID_SRC,
        "-i", str(hdr_path),
        "-i", str(aud_path),
        "-ss", "10", "-t", f"{dur:.2f}", "-i", DRONE_SRC,
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        str(out_mp4)
    ]

    print(f"  [Rendering MP4] {short_info['slug']} ({dur:.1f}s)...")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"  [FFmpeg Error] {proc.stderr[-600:]}")
        raise RuntimeError("FFmpeg rendering failed")
    print(f"  [Done] Saved -> {out_mp4}")
    return out_mp4

if __name__ == "__main__":
    print("=== Re-rendering Clean Header 10 YouTube Shorts ===")
    for item in SHORTS_DATA:
        render_short_video(item)
    print("\n=== All 10 YouTube Shorts Re-rendered with Pristine Typography! ===")
