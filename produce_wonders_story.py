import sys
from pathlib import Path
import time
sys.path.insert(0, '/home/user/media-empire-autopilot')
import _env_loader
import sound_studio
import imageio_ffmpeg
import subprocess

ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()

scenes = {
    0: (
        "تخيل إنك واقف قدام فتحة بئر غامضة في وسط جبل صخري مهجور.. "
        "كل الأجهزة الحديثة بتعطل أول ما تقرب منها، وأي حبل بينزل بينقطع كأنه اتقص بليزر! "
        "خمس محاولات كاملة على مدار سنين من أذكى المستكشفين والعلماء، كلهم رجعوا بخفي حنين ومحدش عرف السر.. "
        "لحد المحاولة الأخيرة اللي حصل فيها شيء شل تفكير الكل وغير نظرتنا للعالم! "
        "ركز معايا في كل كلمة من أول ثانية، لأن أهم وأصدم حتة في الحكاية مستنياك في آخر الفيديو.. "
        "يلا نبدأ القصة من أولها!"
    ),
    1: (
        "الحكاية بدأت في وادي صخري معزول، لما مجموعة عمال بيحفروا لقوا فتحة دائرية محفورة في قلب الصخر الصلب بدقة هندسية مستحيل تكون شغل بشر بدائيين. "
        "الجدران ملساء زي الزجاج، ونازلة لعمق سحيق ملوش آخر. "
        "لما رموا حجر واستنوا يسمعوا صوته وهو بيخبط في القاع، الحجر مطلعش أي صوت نهائياً! "
        "وكأن البئر ده بيبتلع أي حاجة تنزل جواه.. ومن اللحظة دي، بدأت حمى الاستكشاف، وانتشر الخبر بين المغامرين والباحثين عن عجائب الأرض."
    ),
    2: (
        "أول محاولة حقيقية كانت من فريق جيولوجي، جابوا ونش ضخم وحبل فولاذي مربوط فيه كاميرا مصفحة وكشافات قوية جداً. "
        "الكاميرا نزلت أول تلاتين متر والصورة واضحة، وفجأة عند عمق خمسين متر، الكشافات طفت لوحدها والشاشة بدأت ترتعش، وظهر وميض أزرق غريب غطى العدسة! "
        "وقبل ما يسحبوا الكاميرا، الحبل الفولاذي انقطع فجأة كأنه اتداب في ثانية! "
        "في المحاولة التانية، نزلوا مجسات صوتية متطورة، الجهاز سجل نبضات منتظمة زي دقات قلب عملاقة بتطلع من قاع الصخر.. نبضة كل تلات ثواني بالثانية والدقيقة!"
    ),
    3: (
        "السنين عدت، وجت المحاولة التالتة والرابعة باستخدام روبوتات استكشاف متطورة معزولة ضد المغناطيسية ومزودة بحساسات حرارية. "
        "الروبوت قدر ينزل لحد تمانين متر تحت الأرض، وهنا الشاشات نقلت للفريق في غرفة التحكم مشهد وقف شعر راسهم: "
        "البئر مش مجرد فتحة عادية.. ده منتهي ببوابة دائرية ضخمة من معدن غريب مش بيصدي، وعليها سبع تروس متداخلة بتتحرك ببطء شديد وتناغم ميكانيكي عجيب، وفي نص البوابة تجويف محفور على شكل شمس بأشعة دقيقة!"
    ),
    4: (
        "هنا جه دور عالم آثار ورياضيات عبقري اسمه الدكتور رامي، اللي كرس عشر سنين من حياته يدرس حركة التروس دي من الصور. "
        "اكتشف إن التروس بتتحرك مع حركة تعامد الشمس في يوم محدد من السنة، وإن في مفتاح ضوئي لازم يتسلط بزاوية معينة علشان البوابة تفتح! "
        "جهز كبسولة أمان خاصة وقرر ينزل بنفسه في المحاولة الخامسة والأخيرة.. وسط حبس أنفاس الملايين اللي بيتابعوا البث المباشر. "
        "نزل رامي للأعماق، ووقف قدام البوابة، ومع دقة الساعة بالظبط، سلط الحزمة الضوئية في قلب التجويف.. "
        "وفجأة، التروس وقفت، وسمع صوت هدير تقيل، والبوابة بدأت تنزلق للداخل!"
    ),
    5: (
        "ودي بقى أهم لحظة في القصة كلها.. رامي خطى جوة الغرفة، واللي شافه شل لسانه عن الكلام: "
        "مكنش كنز دهب، ولا مقبرة.. كانت قاعة فلكية هائلة بتطفو في نصها كرة أرضية مجسمة من حجر بلوري شفاف، بتدور في الهوا بدون أي مغناطيس، ومسجل عليها قارات الأرض بدقة مرعبة بتفاصيل مكنتش معروفة إلا من كام سنة بس بالأقمار الصناعية! "
        "وجنبها لوح حجري منقوش عليه رسالة واضحة: الأرض مرت بحضارات أعظم منكم، وسايبين ليكم شفرات حمايتها في سبع مواقع تانية.. "
        "المحاولة نجحت، واللغز اتفتح، بس فتح وراه ألف باب وباب من علامات الاستفهام!"
    ),
    6: (
        "قصة بئر العجائب بتفكرنا دايماً إن كوكبنا لسه شايل أسرار أكبر بكتير من اللي بنعرفه، وإن كل محاولة فاشلة كانت مجرد خطوة بتوصلنا للحقيقة في الآخر.. "
        "لو وصلت معايا لحد اللحظة دي واستمتعت بالحكاية المليانة إثارة دي، متنساش تنزل دلوقتي تدوس لايك للفيديو، وتشترك في القناة وتفعل جرس التنبيهات علشان يوصلك كل لغز جديد بنحكيه أول بأول.. "
        "ويهمني جداً تكتبلي رأيك في التعليقات: تفتكر لو كشفنا باقي المواقع السبعة، هنلاقي إيه مستنينا؟ "
        "هستنى أقرأ تعليقاتكم كلها.. وأشوفكم في الدليل الأخير الجاي!"
    )
}

work_dir = Path("/tmp/eldalil_well_of_wonders")
work_dir.mkdir(parents=True, exist_ok=True)
out_dir = Path("/home/user/media-empire-autopilot/production_vault/video_eldalil_wonders")
out_dir.mkdir(parents=True, exist_ok=True)

print("=== 1. Synthesizing all scenes with Kore (Google AI Studio) ===")
for sc_num, text in sorted(scenes.items()):
    out_file = work_dir / f"scene_{sc_num:02d}.mp3"
    print(f"\n[Scene {sc_num}] Synthesizing...")
    success = sound_studio._try_gemini_tts_strict(
        text=text,
        is_arabic=True,
        out_mp3=out_file,
        gemini_voice="Kore",
        call_index=sc_num
    )
    if not success:
        print(f"FAILED on scene {sc_num}")
        sys.exit(1)
    dur = sound_studio.get_audio_duration(out_file)
    print(f"  -> Generated: {dur:.2f}s, size: {out_file.stat().st_size} bytes")
    time.sleep(1)

# Concatenation with natural 0.65s silence
pause_mp3 = work_dir / "pause.mp3"
subprocess.run(
    [
        ffmpeg_bin, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
        "-t", "0.65", "-c:a", "libmp3lame", "-b:a", "192k", "-loglevel", "error", str(pause_mp3)
    ],
    check=True
)

concat_list = work_dir / "concat_list.txt"
with open(concat_list, "w") as f:
    for i in sorted(scenes.keys()):
        sc_file = work_dir / f"scene_{i:02d}.mp3"
        f.write(f"file '{sc_file.resolve()}'\n")
        if i < max(scenes.keys()):
            f.write(f"file '{pause_mp3.resolve()}'\n")

raw_voice = out_dir / "audio_well_of_wonders_raw.mp3"
subprocess.run(
    [
        ffmpeg_bin, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c:a", "libmp3lame", "-b:a", "192k", "-loglevel", "error", str(raw_voice)
    ],
    check=True
)

# Background tension drone bed
tension_wav = sound_studio._build_psychological_tension_bed(work_dir / "tension_bed.wav", duration_sec=60.0)

master_mp3 = out_dir / "audio_well_of_wonders_kore_master.mp3"
subprocess.run(
    [
        ffmpeg_bin, "-y",
        "-i", str(raw_voice),
        "-stream_loop", "-1", "-i", str(tension_wav),
        "-filter_complex",
        "[0:a]acompressor=threshold=-16dB:ratio=2.8:attack=5:release=60,loudnorm=I=-16:TP=-1.5:LRA=9[v];"
        "[1:a]volume=0.08[bg];"
        "[v][bg]amix=inputs=2:duration=first:dropout_transition=2[out]",
        "-map", "[out]",
        "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k",
        "-loglevel", "error", str(master_mp3)
    ],
    check=True
)

dur = sound_studio.get_audio_duration(master_mp3)
print(f"\n Master Audio Created Successfully!")
print(f"Path: {master_mp3}")
print(f"Duration: {dur:.2f} seconds ({dur/60:.2f} minutes)")
print(f"Size: {master_mp3.stat().st_size} bytes ({master_mp3.stat().st_size / (1024*1024):.2f} MB)")
