import sys
import os
import requests
import base64
import subprocess
import time
from pathlib import Path

sys.path.insert(0, '/home/user/media-empire-autopilot')
import _env_loader
import sound_studio

k3 = os.getenv('GEMINI_API_KEY_3')
k4 = os.getenv('GEMINI_API_KEY_4')
active_keys = [k for k in [k3, k4] if k]

# 100% PURE Egyptian Dialect
scenes = {
    0: (
        "يا سيدي تعال أحكيلك أغرب لغز ممكن تسمعه في حياتك.. "
        "تخيل إنك واقف قدام فتحة بئر غامضة في بطن جبل صخري مقطوع، "
        "كل الأجهزة الإلكترونية بتهنج وتبوظ أول ما تقرب منها، "
        "وأتخن واير حديد ينزل جواه يتقطع كأنه اتلسع بليزر! "
        "خمس محاولات كاملة على مدار سنين من أذكى المغامرين والعلماء.. "
        "كلهم رجعوا مكسوفين ومحدش قدر يعرف إيه اللي مستخبي جوه.. "
        "لحد المحاولة الخامسة والأخيرة اللي غيرت كل حساباتنا عن العالم! "
        "اسمع معايا الفيديو وركز في كل تفصيلة من أول ثانية، "
        "لأن أهم وأصدم حتة في الحكاية كلها مستنياك في آخر الفيديو.. "
        "يلا بينا نبدأ الحكاية من أولها!"
    ),
    1: (
        "الحكاية بدأت لما شوية عمال بيحفروا في منطقة جبلية مقطوعة، "
        "وفجأة تحت الصخر لقوا فتحة مدورة زي ما تكون معمولة ببرجل هندسي مظبوط بالسنتي! "
        "الجدران ناعمة جداً ومستحيل تكون حفر يدوي عادي، ونازلة لتحت في ضلمة كحل مفيش آخرها.. "
        "الرجالة وقفوا مذهولين، واحد منهم جاب طوبة كبيرة ورماها علشان يسمع هترزع في القاع بعد كام ثانية.. "
        "فضلوا واقفين دقيقة واتنين وتلاتة، ومفيش أي صوت طلع نهائياً! "
        "كأن البئر ده شفط الطوبة ومسح أثرها من الوجود.. "
        "من هنا الخبر ولع في المنطقة، والعلماء والمغامرين قرروا إنهم لازم يعرفوا سر الخرم العجيب ده."
    ),
    2: (
        "أول محاولة جابوا فيها ونش عملاق وسلك واير حديد متين جداً، "
        "وربطوا في آخره كاميرا مصفحة بكشافات ليد بتنور زي الشمس. "
        "نزلت الكاميرا أول عشرين متر وشايفين الصخر تمام.. "
        "فجأة، عند عمق خمسين متر، الكشافات طفت لوحدها، وشاشة الكنترول شوشت، "
        "وظهر وميض أزرق غريب ملا الشاشة في ثانية! "
        "وقبل ما يلحقوا يشدوا الواير، اتقطع فجأة وكأنه اتداب في لمحة بصر! "
        "في المحاولة التانية بعدها بكام شهر، نزلوا مايكات حساسة وحساسات صوتية.. "
        "والمايك لقط صوت وقف الدم في عروق المهندسين: "
        "تكة.. وراها تكة.. وراها تكة منتظمة بالثانية، "
        "كأن في قلب ميكانيكي عملاق شغال وبيدق جوه بطن الجبل!"
    ),
    3: (
        "المحاولات التالتة والرابعة كانت بروبوتات صغيرة بتمشي بجنازير ومجهزة بحساسات ضد التشويش. "
        "الروبوت نزل واتحرك لحد عمق تمانين متر.. "
        "وهنا الكاميرا نقلت مشهد شل تفكير الكل: "
        "البئر مش آخره صخر، ده بينتهي عند بوابة دائرية ضخمة من معدن غريب بيلمع ومفيش فيه ذرة صدى واحدة! "
        "وعالبوابة في سبع تروس متداخلة بيلفوا براحة شديدة وبحركة هندسية عبقرية زي ساعة فلكية متصنعة بمهارة تخطف العقل، "
        "وفي نص البوابة في تجويف محفور بدقة على شكل عين شمس طالع منها خيوط دقيقة!"
    ),
    4: (
        "هنا بقى يظهر بطل حكايتنا، الدكتور رامي، باحث ومهندس مصري عبقري، "
        "قعد عشر سنين كاملة حابس نفسه بين الصور والمعادلات يحلل في حركة التروس دي. "
        "رامي اكتشف إن التروس دي مش شغالة عشوائي، دي مربوطة بحركة زاوية الشمس في يوم محدد في السنة، "
        "وإن في مفتاح ضوئي بنبضة معينة لازم يتسلط في قلب التجويف علشان القفل يفتح! "
        "قرر إنه ينزل بنفسه في كبسولة مصفحة في المحاولة الخامسة والأخيرة.. "
        "كل القنوات العالمية كانت فاتحة بث مباشر والناس حابسة أنفاسها.. "
        "رامي وصل للبوابة، وبحسبة رياضية دقيقة سلط حزمة الضوء.. "
        "وفجأة، التروس وقفت، وسمع صوت تكة تقيلة هزت المكان، والبوابة اتسحبت لجوه بهدوء!"
    ),
    5: (
        "ودي بقى اللحظة اللي عشانه قولتلك اسمع الفيديو للآخر.. "
        "رامي دخل جوه القاعة، واللي شافه مكنش في أي فيلم خيال علمي في الدنيا: "
        "مكنش في كنز ولا دهب ولا مقابر.. "
        "القاعة كانت واسعة جداً وطاير في نصها كوكب الأرض مجسم من كريستال نقي بيلمع، "
        "بيلف في الهوا لوحده من غير أي سلك ولا قاعدة ولا مغناطيس! "
        "ومرسوم عليه قارات الأرض وتضاريسها بدقة ميكروسكوبية مكنش حد يعرفها إلا لما طلعنا الفضاء بالأقمار الصناعية! "
        "وجنب الكوكب في لوح صخري مكتوب عليه بحروف غريبة فكوها بعدين: "
        "إحنا حضارة عمرت الأرض قبلكم بآلاف السنين، وسايبين ليكم شفرات إنقاذ كوكبكم في سبع أماكن تانية مدفونة في العالم! "
        "المحاولة نجحت واللغز اتفتح، بس ساب وراه صدمة تاريخية لكل علماء الكوكب!"
    ),
    6: (
        "شفت بقى إن كوكبنا ده لسه شايل أسرار أعظم بكتير من اللي بنشوفه، "
        "وإن كل محاولة فاشلة كانت مجرد خطوة بتفتح عيوننا عالحقيقة في الآخر؟ "
        "لو وصلت معايا لحد الدقيقة دي والحكاية دخلت دماغك وعجبتك، "
        "متنساش تنزل دلوقتي حالا تخبط اللايك المتين، وتشترك في القناة وتفعل جرس التنبيهات "
        "علشان الألغاز اللي جاية هتقلب موازين تفكيرك أكتر وأكتر.. "
        "ويهمني جداً تكتبلي رأيك في التعليقات تحت: "
        "تفتكر لو رحنا للمكان التاني من السبعة، هنلاقي إيه مستنينا؟ "
        "هستنى أقرأ رأي كل واحد فيكم.. وأشوفكم في الدليل الأخير الجاي!"
    )
}

work_dir = Path("/tmp/eldalil_pure_egyptian_kore")
work_dir.mkdir(parents=True, exist_ok=True)

# Strict SINGLE model: gemini-3.8-flash-tts
MODEL_ID = "gemini-3.8-flash-tts"

print(f"=== Synthesizing all scenes strictly with: {MODEL_ID} & voice: Kore ===")

for sc_num, text in sorted(scenes.items()):
    out_mp3 = work_dir / f"scene_{sc_num:02d}.mp3"
    print(f"\n--- Generating Scene {sc_num} ---")
    generated = False
    for attempt in range(5):
        for ki, k in enumerate(active_keys):
            key_label = "Key #3" if k == k3 else "Key #4"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent?key={k}"
            payload = {
                "contents": [{"parts": [{"text": text}]}],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {
                        "languageCode": "ar-EG",
                        "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Kore"}},
                    },
                },
            }
            try:
                r = requests.post(url, json=payload, timeout=35)
                if r.status_code == 200:
                    part = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
                    audio_bytes = base64.b64decode(part["data"])
                    tmp_in = out_mp3.with_suffix(".pcm")
                    tmp_in.write_bytes(audio_bytes)
                    cmd = [
                        "ffmpeg", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1",
                        "-i", str(tmp_in), "-c:a", "libmp3lame", "-b:a", "192k",
                        "-loglevel", "error", str(out_mp3)
                    ]
                    subprocess.run(cmd, check=True)
                    tmp_in.unlink()
                    dur = sound_studio.get_audio_duration(out_mp3)
                    print(f"  ✓ Scene {sc_num} generated with {MODEL_ID} ({key_label}) -> {dur:.2f}s")
                    generated = True
                    break
                elif r.status_code == 429:
                    print(f"  {key_label} hit 429, trying next key...")
                else:
                    print(f"  {key_label} returned {r.status_code}: {r.text[:120]}")
            except Exception as e:
                print(f"  Exception with {key_label}: {e}")

        if generated:
            break
        print(f"  Cooldown 12s before attempt {attempt+2}...")
        time.sleep(12)

    if not generated:
        print(f"FATAL: Could not generate Scene {sc_num}")
        sys.exit(1)

    print("  Pausing 12s to keep rate limits completely calm...")
    time.sleep(12)

print("\nAll 7 scenes generated with 100% identical voice & model!")

# Assembling master audio
out_dir = Path("/home/user/media-empire-autopilot/production_vault/video_eldalil_wonders")
out_dir.mkdir(parents=True, exist_ok=True)

pause_mp3 = work_dir / "pause.mp3"
subprocess.run(
    ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "0.65", "-c:a", "libmp3lame", "-b:a", "192k", "-loglevel", "error", str(pause_mp3)],
    check=True
)

concat_list = work_dir / "concat_list.txt"
with open(concat_list, "w") as f:
    for i in range(7):
        sc_file = work_dir / f"scene_{i:02d}.mp3"
        f.write(f"file '{sc_file.resolve()}'\n")
        if i < 6:
            f.write(f"file '{pause_mp3.resolve()}'\n")

raw_voice = out_dir / "audio_well_of_wonders_egyptian_kore_raw.mp3"
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c:a", "libmp3lame", "-b:a", "192k", "-loglevel", "error", str(raw_voice)], check=True)

# Build subtle background tension drone
tension_wav = sound_studio._build_psychological_tension_bed(work_dir / "tension_bed.wav", duration_sec=60.0)

master_mp3 = out_dir / "audio_well_of_wonders_egyptian_kore_master.mp3"
subprocess.run(
    [
        "ffmpeg", "-y",
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
print(f"Duration: {dur:.2f}s ({dur/60:.2f}m)")
print(f"Size: {master_mp3.stat().st_size} bytes ({master_mp3.stat().st_size / (1024*1024):.2f} MB)")
