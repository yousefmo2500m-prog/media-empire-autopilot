# -*- coding: utf-8 -*-
"""
محرك المونتاج السينمائي الاحترافي V13.0 (LTX Moving Hook + Instant Coral Top Banner + 3-Word Fast Karaoke + Debate CTA)
- يدعم دمج لقطة فيديو ذكاء اصطناعي متحركة حقيقية 100% (LTX-Video) في الافتتاحية (الثانية 0.0) لكسر التمرير السريع فوراً!
- شريط عنوان علوي أحمر مرجاني عالي التباين (HookTop) يظهر من الإطار الأول (0.00ث) لإيقاف المتصفح الصامت على فيسبوك وتيك توك!
- كابشن كاريوكي خاطف (3 كلمات في اللقطة بخط عريض واضح) + شريط التحدي الجدلي (١ أو ٢) في الخاتمة لتفجير التعليقات!
- يعرض بطاقات عناوين الفصول التفاعلية (Netflix-Style Chapter Cards) عند بداية كل مشهد في الفيلم الطويل لمنع الملل!
"""

import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import imageio_ffmpeg

from sound_studio import get_audio_duration

FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()
ASSETS_DIR = Path(__file__).resolve().parent / "fonts"


def _strip_emojis(txt: str) -> str:
    txt = re.sub(r"[\U00010000-\U0010ffff\u2600-\u27bf\ufe0f]", "", txt)
    return re.sub(r"\s+", " ", txt).strip()


def _ass_ts(sec: float) -> str:
    sec = max(0.0, sec)
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _esc_ass(txt: str) -> str:
    return _strip_emojis(txt).replace("\\", "").replace("{", "(").replace("}", ")")


def _write_long_ass(
    subtitles: List[Dict[str, Any]],
    scene_timings: List[Dict[str, Any]],
    teaser_banner: str,
    teaser_end_sec: float,
    brand_name: str,
    total_dur: float,
    ass_path: Path,
) -> Path:
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Brand,Cairo,24,&H45FFFFFF,&H000000FF,&H85000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,1,9,36,36,26,1
Style: TeaserBadge,Cairo,31,&H00FFFFFF,&H000000FF,&H001210C5,&HD80E0C98,-1,0,0,0,100,100,0,0,3,13,0,8,40,40,26,1
Style: ChapterCard,Cairo,30,&H0028DFFF,&H00FFFFFF,&H0012141E,&HC80A0E18,-1,0,0,0,100,100,0,0,3,12,0,7,38,38,28,1
Style: Sub,Cairo,40,&H00FFFFFF,&H0000D7FF,&H00080810,&H96000000,-1,0,0,0,100,100,0,0,1,3.6,2.0,2,85,85,42,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 1,0:00:00.00,{_ass_ts(total_dur)},Brand,,0,0,0,,{_esc_ass(brand_name)}
"""
    lines = [header]

    tb_clean = _esc_ass(teaser_banner)
    if tb_clean and teaser_end_sec > 3.0:
        lines.append(
            f"Dialogue: 3,0:00:00.00,{_ass_ts(max(3.5, teaser_end_sec - 0.4))},TeaserBadge,,0,0,0,,{{\\fad(0,300)}}{tb_clean}"
        )

    for st in scene_timings:
        if int(st.get("scene_num", 0)) >= 1:
            c_start = float(st["start"]) + 0.25
            c_end = min(float(st["end"]) - 0.5, c_start + 4.8)
            c_title = _esc_ass(str(st.get("scene_title", "")))
            if c_title and c_end > c_start + 1.0:
                lines.append(
                    f"Dialogue: 3,{_ass_ts(c_start)},{_ass_ts(c_end)},ChapterCard,,0,0,0,,{{\\fad(250,350)}}{c_title}"
                )

    for sub in subtitles:
        txt = _esc_ass(sub["text"])
        if txt:
            lines.append(f"Dialogue: 2,{_ass_ts(sub['start'])},{_ass_ts(sub['end'])},Sub,,0,0,0,,{{\\fad(75,75)}}{txt}")
    ass_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ass_path


def _write_short_ass(
    words: List[Dict[str, Any]],
    brand_name: str,
    hook_banner: str,
    hook_end_sec: float,
    cta_banner: str,
    total_dur: float,
    ass_path: Path,
) -> Path:
    cta_start = max(hook_end_sec + 1.8, total_dur - 8.5)
    hook_vis_end = min(max(4.6, hook_end_sec + 0.4), min(6.2, cta_start - 0.4))
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Brand,Cairo,27,&H3800D7FF,&H000000FF,&H85000000,&H00000000,-1,0,0,0,100,100,0,0,1,2.2,1,8,30,30,46,1
Style: HookTop,Cairo,37,&H00FFFFFF,&H0028DFFF,&H001814C8,&HE8120EA8,-1,0,0,0,100,100,0,0,3,16,0,8,30,30,124,1
Style: Cap,Cairo,53,&H00FFFFFF,&H0000D7FF,&H0006060E,&HA8000000,-1,0,0,0,100,100,0,0,1,4.6,2.5,2,42,42,262,1
Style: CTA,Cairo,35,&H0028DFFF,&H00FFFFFF,&H000E1224,&HE8080C1C,-1,0,0,0,100,100,0,0,3,15,0,8,30,30,124,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 1,0:00:00.00,{_ass_ts(total_dur)},Brand,,0,0,0,,{_esc_ass(brand_name)}
Dialogue: 3,{_ass_ts(cta_start)},{_ass_ts(total_dur)},CTA,,0,0,0,,{{\\fad(160,80)}}{_esc_ass(cta_banner)}
"""
    lines = [header]
    hb_clean = _esc_ass(hook_banner)
    if hb_clean and hook_vis_end > 1.2:
        # يبدأ في الثانية 0.00 بدون تأخير ليظهر في الغلاف وللمشاهد الصامت منذ اللحظة الأولى
        lines.append(
            f"Dialogue: 3,0:00:00.00,{_ass_ts(hook_vis_end)},HookTop,,0,0,0,,{{\\fad(0,240)}}{hb_clean}"
        )

    chunk = 3
    for i in range(0, len(words), chunk):
        grp = words[i : i + chunk]
        if not grp:
            continue
        s_t = grp[0]["start"]
        e_t = grp[-1]["end"]
        if i + chunk < len(words):
            e_t = min(words[i + chunk]["start"], e_t + 0.32)
        e_t = max(s_t + 0.18, e_t)
        parts = []
        for idx_w, w in enumerate(grp):
            clean = _esc_ass(w["word"])
            if idx_w == len(grp) - 1:
                parts.append(r"{\c&H0028DFFF&}" + clean + r"{\c&H00FFFFFF&}")
            else:
                parts.append(clean)
        lines.append(f"Dialogue: 2,{_ass_ts(s_t)},{_ass_ts(e_t)},Cap,,0,0,0,,{' '.join(parts)}")
    ass_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ass_path


def _render_motion_clip_segment(
    motion_mp4: Path,
    dur: float,
    out_seg: Path,
    target_w: int,
    target_h: int,
    fps: int,
    crf: int = 21,
) -> bool:
    """يحوّل لقطة الفيديو المتحركة الافتتاحية لنفس أبعاد ومعدل إطارات المونتاج بدقة تامة."""
    try:
        if not motion_mp4 or not motion_mp4.exists() or motion_mp4.stat().st_size < 20000:
            return False
        clip_dur = max(0.8, get_audio_duration(motion_mp4))
        pts_factor = max(0.65, min(2.25, dur / clip_dur))
        fade_out_st = max(0.14, dur - 0.16)
        vf = (
            f"setpts={pts_factor:.4f}*PTS,"
            f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={target_w}:{target_h},"
            f"unsharp=5:5:0.75:5:5:0.0,"
            f"fade=t=in:st=0:d=0.12,fade=t=out:st={fade_out_st:.2f}:d=0.15,format=yuv420p"
        )
        subprocess.run(
            [
                FFMPEG_BIN, "-y",
                "-i", str(motion_mp4),
                "-t", f"{dur:.3f}",
                "-vf", vf, "-r", str(fps),
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", str(crf),
                "-an", "-loglevel", "error", str(out_seg),
            ],
            check=True,
        )
        return out_seg.exists() and out_seg.stat().st_size > 10000
    except Exception:
        return False


def _render_single_long_8s_shot(
    idx: int,
    img_path: Path,
    dur: float,
    out_seg: Path,
    fps: int = 20,
    opening_motion_mp4: Optional[Path] = None,
) -> Tuple[int, Path]:
    if idx == 0 and opening_motion_mp4 is not None:
        if _render_motion_clip_segment(opening_motion_mp4, dur, out_seg, 1280, 720, fps, crf=22):
            return idx, out_seg

    fade_out_st = max(0.16, dur - 0.20)
    d_safe = max(1.0, dur)
    mode = idx % 6
    if mode == 0:
        mv = f"scale=1424:801,crop=1280:720:'(iw-1280)*(t/{d_safe:.2f})':'(ih-720)/2'"
    elif mode == 1:
        mv = f"scale=1424:801,crop=1280:720:'(iw-1280)*(1-t/{d_safe:.2f})':'(ih-720)/2'"
    elif mode == 2:
        mv = f"scale=1424:801,crop=1280:720:'(iw-1280)/2':'(ih-720)*(t/{d_safe:.2f})'"
    elif mode == 3:
        mv = f"scale=1424:801,crop=1280:720:'(iw-1280)/2':'(ih-720)*(1-t/{d_safe:.2f})'"
    elif mode == 4:
        mv = f"scale=1424:801,crop=1280:720:'(iw-1280)*(t/{d_safe:.2f})':'(ih-720)*(t/{d_safe:.2f})'"
    else:
        mv = f"scale=1424:801,crop=1280:720:'(iw-1280)*(1-t/{d_safe:.2f})':'(ih-720)*(t/{d_safe:.2f})'"

    vf = f"{mv},fade=t=in:st=0:d=0.16,fade=t=out:st={fade_out_st:.2f}:d=0.18,format=yuv420p"
    subprocess.run(
        [
            FFMPEG_BIN, "-y",
            "-loop", "1", "-framerate", str(fps), "-t", f"{dur:.3f}", "-i", str(img_path),
            "-vf", vf, "-r", str(fps),
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
            "-an", "-loglevel", "error", str(out_seg),
        ],
        check=True,
    )
    return idx, out_seg


def render_long_episode_mp4(
    shot_images: List[Path],
    shot_windows: List[Dict[str, Any]],
    audio_mp3: Path,
    subtitles: List[Dict[str, Any]],
    scene_timings: List[Dict[str, Any]],
    teaser_banner: str,
    teaser_end_sec: float,
    brand_name: str,
    out_mp4: Path,
    work_dir: Path,
    opening_motion_mp4: Optional[Path] = None,
) -> Path:
    work_dir.mkdir(parents=True, exist_ok=True)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    total_dur = get_audio_duration(audio_mp3)
    fps = 20

    n_shots = min(len(shot_images), len(shot_windows))
    seg_paths: List[Path] = [work_dir / f"lshot_{i:03d}.mp4" for i in range(n_shots)]

    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = [
            ex.submit(
                _render_single_long_8s_shot,
                i,
                shot_images[i],
                max(2.0, float(shot_windows[i]["dur"])),
                seg_paths[i],
                fps,
                opening_motion_mp4 if i == 0 else None,
            )
            for i in range(n_shots)
        ]
        for f in as_completed(futs):
            f.result()

    concat_file = work_dir / "long_v_concat.txt"
    concat_file.write_text("\n".join(f"file '{p.resolve()}'" for p in seg_paths), encoding="utf-8")
    joined_v = work_dir / "long_v_joined.mp4"
    subprocess.run(
        [FFMPEG_BIN, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", "-loglevel", "error", str(joined_v)],
        check=True,
    )

    ass_file = _write_long_ass(
        subtitles=subtitles,
        scene_timings=scene_timings,
        teaser_banner=teaser_banner,
        teaser_end_sec=teaser_end_sec,
        brand_name=brand_name,
        total_dur=total_dur,
        ass_path=work_dir / "long_subs.ass",
    )
    ass_esc = str(ass_file.resolve()).replace("\\", "/").replace(":", "\\:")
    fonts_esc = str(ASSETS_DIR.resolve()).replace("\\", "/").replace(":", "\\:")

    subprocess.run(
        [
            FFMPEG_BIN, "-y",
            "-i", str(joined_v),
            "-i", str(audio_mp3),
            "-vf", f"subtitles='{ass_esc}':fontsdir='{fonts_esc}'",
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            "-pix_fmt", "yuv420p", "-r", str(fps),
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart",
            "-loglevel", "error", str(out_mp4),
        ],
        check=True,
    )

    for sp in seg_paths:
        sp.unlink(missing_ok=True)
    joined_v.unlink(missing_ok=True)
    return out_mp4


def _render_single_short_8s_shot(
    idx: int,
    img_path: Path,
    dur: float,
    out_seg: Path,
    fps: int = 24,
    opening_motion_mp4: Optional[Path] = None,
) -> Tuple[int, Path]:
    if idx == 0 and opening_motion_mp4 is not None:
        if _render_motion_clip_segment(opening_motion_mp4, dur, out_seg, 720, 1280, fps, crf=21):
            return idx, out_seg

    fade_out_st = max(0.12, dur - 0.14)
    d_safe = max(0.9, dur)
    mode = idx % 4
    if mode == 0:
        mv = f"scale=764:1358,crop=720:1280:'(iw-720)/2':'(ih-1280)*(t/{d_safe:.2f})'"
    elif mode == 1:
        mv = f"scale=764:1358,crop=720:1280:'(iw-720)/2':'(ih-1280)*(1-t/{d_safe:.2f})'"
    elif mode == 2:
        mv = f"scale=764:1358,crop=720:1280:'(iw-720)*(t/{d_safe:.2f})':'(ih-1280)/2'"
    else:
        mv = f"scale=764:1358,crop=720:1280:'(iw-720)*(1-t/{d_safe:.2f})':'(ih-1280)/2'"

    vf = f"{mv},fade=t=in:st=0:d=0.12,fade=t=out:st={fade_out_st:.2f}:d=0.14,format=yuv420p"
    subprocess.run(
        [
            FFMPEG_BIN, "-y",
            "-loop", "1", "-framerate", str(fps), "-t", f"{dur:.3f}", "-i", str(img_path),
            "-vf", vf, "-r", str(fps),
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "21",
            "-an", "-loglevel", "error", str(out_seg),
        ],
        check=True,
    )
    return idx, out_seg


def render_vertical_short_mp4(
    vertical_images: List[Path],
    short_windows: List[Dict[str, Any]],
    short_mp3: Path,
    short_words: List[Dict[str, Any]],
    brand_name: str,
    hook_banner: str,
    hook_end_sec: float,
    cta_banner: str,
    out_mp4: Path,
    work_dir: Path,
    opening_motion_mp4: Optional[Path] = None,
) -> Path:
    work_dir.mkdir(parents=True, exist_ok=True)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    total_dur = get_audio_duration(short_mp3)
    fps = 24

    n_shots = min(len(vertical_images), len(short_windows))
    seg_paths: List[Path] = [work_dir / f"vshot_{i:03d}.mp4" for i in range(n_shots)]

    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = [
            ex.submit(
                _render_single_short_8s_shot,
                i,
                vertical_images[i],
                max(1.6, float(short_windows[i]["dur"])),
                seg_paths[i],
                fps,
                opening_motion_mp4 if i == 0 else None,
            )
            for i in range(n_shots)
        ]
        for f in as_completed(futs):
            f.result()

    concat_file = work_dir / "short_v_concat.txt"
    concat_file.write_text("\n".join(f"file '{p.resolve()}'" for p in seg_paths), encoding="utf-8")
    joined_v = work_dir / "short_v_joined.mp4"
    subprocess.run(
        [FFMPEG_BIN, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", "-loglevel", "error", str(joined_v)],
        check=True,
    )

    ass_file = _write_short_ass(
        words=short_words,
        brand_name=brand_name,
        hook_banner=hook_banner,
        hook_end_sec=hook_end_sec,
        cta_banner=cta_banner,
        total_dur=total_dur,
        ass_path=work_dir / "short_subs.ass",
    )
    ass_esc = str(ass_file.resolve()).replace("\\", "/").replace(":", "\\:")
    fonts_esc = str(ASSETS_DIR.resolve()).replace("\\", "/").replace(":", "\\:")

    subprocess.run(
        [
            FFMPEG_BIN, "-y",
            "-i", str(joined_v),
            "-i", str(short_mp3),
            "-vf", f"subtitles='{ass_esc}':fontsdir='{fonts_esc}'",
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
            "-pix_fmt", "yuv420p", "-r", str(fps),
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart",
            "-loglevel", "error", str(out_mp4),
        ],
        check=True,
    )

    for sp in seg_paths:
        sp.unlink(missing_ok=True)
    joined_v.unlink(missing_ok=True)
    return out_mp4
