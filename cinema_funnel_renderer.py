# -*- coding: utf-8 -*-
"""
محرك المونتاج السينمائي المزدوج V4.0 (15+ Min Long-Form Movie + 9:16 Cliffhanger Short Renderer)
1) assemble_long_episode_mp4:
   - ينتج فيلم الحلقة الكامل (15.5–18 دقيقة، 1280x720 HD، 16:9) ليوتيوب وفيسبوك.
   - يحوّل الـ 8 مشاهد القصصية إلى 24 لقطة كاميرا سينمائية متحركة (Zoom-In / Pan-Right / Pan-Left / Close-Up)
     بحيث تتغير زاوية الكاميرا أو المشهد كل ~38 ثانية بالتزامن مع أحداث الفصول الخمسة!
   - يطبع عناوين الفصول الخمسة + الترجمة السفلية المزامنة بخط Cairo العريض الواضح.
2) assemble_cliffhanger_short_mp4:
   - ينتج الشورت التشويقي الحماسي (9:16 رأسي، 720x1280 HD) ليوتيوب شورتس وتيك توك وريلز.
   - يعرض مشاهد القصة الرأسية بتقطيع سريع حماسي كل 5 ثوانٍ + كلمات قافزة في منتصف الشاشة كلمة بكلمة
     + لافتة بارزة في النهاية: «لسماع الفيديو كامل رابط الفيديو في أول تعليق».
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List

import imageio_ffmpeg

from sound_studio import get_audio_duration

FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()
FONTS_DIR = Path(__file__).resolve().parent / "fonts"


def _fmt_ass_time(sec: float) -> str:
    sec = max(0.0, sec)
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _clean_ass_text(txt: str, is_arabic: bool) -> str:
    # تنظيف أي رموز خاصة بـ ASS وإضافة علامة اتجاه اليمين لليسار للعربية لضبط علامات التعجب والاستفهام
    cleaned = txt.replace("{", "").replace("}", "").replace("\\", " ").replace("\n", " ").strip()
    # إزالة الإيموجي لأن خط Cairo لا يرسم الإيموجي الملونة
    cleaned = "".join(ch for ch in cleaned if ord(ch) < 0x1F000)
    if is_arabic:
        return f"\u200f{cleaned}"
    return cleaned


def _write_long_ass(
    ass_path: Path,
    subtitles: List[Dict[str, Any]],
    act_markers: List[Dict[str, Any]],
    brand_name: str,
    is_arabic: bool,
) -> None:
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Cairo,40,&H00FFFFFF,&H0000FFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,3.2,1.6,2,70,70,38,1
Style: ActBanner,Cairo,36,&H0038D9FF,&H0000FFFF,&H00000000,&HB4000000,-1,0,0,0,100,100,0,0,3,2.5,0,8,60,60,28,1
Style: BrandWatermark,Cairo,24,&H55FFFFFF,&H55FFFFFF,&H55000000,&H00000000,-1,0,0,0,100,100,0,0,1,1.6,0,9,30,30,22,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    total_end = max((s["end"] for s in subtitles), default=930.0)
    lines.append(
        f"Dialogue: 0,0:00:00.00,{_fmt_ass_time(total_end)},BrandWatermark,,0,0,0,,{_clean_ass_text(brand_name, is_arabic)}"
    )

    for am in act_markers:
        st = am["start"] + 0.3
        en = st + 5.5
        label = (
            f"الفصل {am['act_num']} : {am['act_title']}"
            if is_arabic
            else f"ACT {am['act_num']} — {am['act_title']}"
        )
        lines.append(
            f"Dialogue: 2,{_fmt_ass_time(st)},{_fmt_ass_time(en)},ActBanner,,0,0,0,,  {_clean_ass_text(label, is_arabic)}  "
        )

    for s in subtitles:
        txt = _clean_ass_text(s["text"], is_arabic)
        if not txt.strip("\u200f "):
            continue
        lines.append(
            f"Dialogue: 1,{_fmt_ass_time(s['start'])},{_fmt_ass_time(s['end'])},Sub,,0,0,0,,{txt}"
        )

    ass_path.write_text("\n".join(lines), encoding="utf-8")


def _write_short_ass(
    ass_path: Path,
    words: List[Dict[str, Any]],
    cta_banner: str,
    total_dur: float,
    is_arabic: bool,
) -> None:
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: WordPop,Cairo,68,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5.5,2.5,5,40,40,40,1
Style: CtaBox,Cairo,38,&H0022E5FF,&H0000FFFF,&H00000000,&HD0000000,-1,0,0,0,100,100,0,0,3,3.0,0,2,36,36,155,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    cta_start = max(0.0, total_dur - 9.5)
    clean_cta = _clean_ass_text(cta_banner, is_arabic)
    lines.append(
        f"Dialogue: 2,{_fmt_ass_time(cta_start)},{_fmt_ass_time(total_dur)},CtaBox,,0,0,0,,  {clean_cta}  "
    )

    for idx, w in enumerate(words):
        st = w["start"]
        en = w["end"]
        if idx + 1 < len(words) and words[idx + 1]["start"] - en < 0.14:
            en = words[idx + 1]["start"]
        txt = _clean_ass_text(w["word"], is_arabic)
        if not txt.strip("\u200f "):
            continue
        lines.append(
            f"Dialogue: 1,{_fmt_ass_time(st)},{_fmt_ass_time(en)},WordPop,,0,0,0,,{{\\fscx112\\fscy112\\t(0,85,\\fscx100\\fscy100)}}{txt}"
        )

    ass_path.write_text("\n".join(lines), encoding="utf-8")


def assemble_long_episode_mp4(
    master_audio_mp3: Path,
    scenes: List[Path],
    subtitles: List[Dict[str, Any]],
    act_markers: List[Dict[str, Any]],
    brand_name: str,
    is_arabic: bool,
    out_mp4: Path,
    work_dir: Path,
) -> Path:
    """يبني الفيديو الطويل (15–18 دقيقة 16:9 HD) من 24 زاوية كاميرا متحركة فوق مشاهد القصة."""
    work_dir.mkdir(parents=True, exist_ok=True)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    total_dur = get_audio_duration(master_audio_mp3) + 0.6

    num_shots = 24
    shot_dur = total_dur / num_shots
    frames_per_shot = max(20, int(round(shot_dur * 20)))

    camera_motions = [
        f"scale=1472:828,zoompan=z='min(zoom+0.00022,1.14)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames_per_shot}:s=1280x720:fps=20",
        f"scale=1472:828,zoompan=z='1.12':x='(iw-iw/zoom)*(on/{frames_per_shot})':y='(ih-ih/zoom)*0.35':d={frames_per_shot}:s=1280x720:fps=20",
        f"scale=1472:828,zoompan=z='if(eq(on,1),1.14,max(1.01,zoom-0.00020))':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*0.28':d={frames_per_shot}:s=1280x720:fps=20",
        f"scale=1472:828,zoompan=z='1.12':x='(iw-iw/zoom)*(1-on/{frames_per_shot})':y='(ih-ih/zoom)*0.45':d={frames_per_shot}:s=1280x720:fps=20",
    ]

    # نبني 8 مقاطع أساسية بحركات كاميرا متنوعة ونكررها في 24 لقطة متتالية عبر الفصول الخمسة (أسرع 3 مرات!)
    base_clips: List[Path] = []
    for sc_idx, sc_path in enumerate(scenes):
        mot_idx = sc_idx % len(camera_motions)
        clip_p = work_dir / f"sc_{sc_idx}.mp4"
        subprocess.run(
            [
                FFMPEG_BIN, "-y", "-loop", "1", "-i", str(sc_path),
                "-vf", f"{camera_motions[mot_idx]},fade=t=in:st=0:d=0.5,fade=t=out:st={max(0.5, shot_dur-0.5):.2f}:d=0.5",
                "-t", f"{shot_dur:.3f}",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-pix_fmt", "yuv420p",
                "-loglevel", "error", str(clip_p),
            ],
            check=True,
        )
        base_clips.append(clip_p)

    shot_files = [base_clips[i % len(base_clips)] for i in range(num_shots)]

    concat_txt = work_dir / "shots_concat.txt"
    concat_txt.write_text("\n".join(f"file '{p.resolve()}'" for p in shot_files), encoding="utf-8")

    ass_path = work_dir / "long_subs.ass"
    _write_long_ass(ass_path, subtitles, act_markers, brand_name, is_arabic)

    subprocess.run(
        [
            FFMPEG_BIN, "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_txt),
            "-i", str(master_audio_mp3),
            "-vf", f"ass={ass_path}:fontsdir={FONTS_DIR}",
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "33",
            "-maxrate", "175k", "-bufsize", "350k",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "64k",
            "-movflags", "+faststart",
            "-shortest",
            "-loglevel", "error",
            str(out_mp4),
        ],
        check=True,
    )
    return out_mp4


def assemble_cliffhanger_short_mp4(
    short_audio_mp3: Path,
    words: List[Dict[str, Any]],
    scenes: List[Path],
    cta_banner: str,
    is_arabic: bool,
    out_mp4: Path,
    work_dir: Path,
) -> Path:
    """يبني الشورت الرأسي الحماسي (720x1280، 9:16) ليوتيوب شورتس وتيك توك مع الكلمات القافزة ولافتة أول تعليق."""
    work_dir.mkdir(parents=True, exist_ok=True)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    total_dur = get_audio_duration(short_audio_mp3) + 0.4

    num_cuts = 12
    cut_dur = total_dur / num_cuts
    frames_cut = max(25, int(round(cut_dur * 30)))

    cut_files: List[Path] = []
    for ci in range(num_cuts):
        sc_path = scenes[ci % len(scenes)]
        cp = work_dir / f"short_cut_{ci:02d}.mp4"
        zoom_expr = (
            f"scale=2280:1282,crop=722:1282:(iw-722)*{0.25 + 0.5*(ci%2)}:0,"
            f"zoompan=z='min(zoom+0.0012,1.16)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames_cut}:s=720x1280:fps=30,"
            f"fade=t=in:st=0:d=0.25"
        )
        subprocess.run(
            [
                FFMPEG_BIN, "-y", "-loop", "1", "-i", str(sc_path),
                "-vf", zoom_expr,
                "-t", f"{cut_dur:.3f}",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21", "-pix_fmt", "yuv420p",
                "-loglevel", "error", str(cp),
            ],
            check=True,
        )
        cut_files.append(cp)

    concat_txt = work_dir / "short_concat.txt"
    concat_txt.write_text("\n".join(f"file '{p.resolve()}'" for p in cut_files), encoding="utf-8")

    ass_path = work_dir / "short_subs.ass"
    _write_short_ass(ass_path, words, cta_banner, total_dur, is_arabic)

    subprocess.run(
        [
            FFMPEG_BIN, "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_txt),
            "-i", str(short_audio_mp3),
            "-vf", f"ass={ass_path}:fontsdir={FONTS_DIR}",
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
            "-maxrate", "1800k", "-bufsize", "3600k",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k",
            "-movflags", "+faststart",
            "-shortest",
            "-loglevel", "error",
            str(out_mp4),
        ],
        check=True,
    )
    return out_mp4
