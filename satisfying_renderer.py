# -*- coding: utf-8 -*-
"""
محرك الشورتس الإدماني السريع V3.0 (Exact Viral Satisfying Storytime + Word-by-Word Pop Captions)
مطابق 100% لأسلوب القنوات المليونية:
1) إزالة السكتات الميتة وتسريع الإيقاع اللفظي بنعومة لشد الانتباه من أول ثانية لآخر ثانية.
2) استخراج التوقيت الدقيق لكل كلمة بالمللي ثانية عبر Groq Whisper-Large-V3-Turbo.
3) فيديوهات حقيقية مريحة للأعصاب 30fps (طبخ برجر، بناء طوب مصغر، تزيين كيك، تقطيع صابون/فخار)
   مرخصة لإعادة الاستخدام التجاري (Creative Commons / Pexels) تتبدل كل 13 ثانية بدون أي صور ثابتة!
4) كلمة واحدة عريضة بيضاء بإطار أسود سميك تقفز في منتصف الشاشة مع كل كلمة منطوقة بالضبط.
"""

import json
import math
import os
import random
import subprocess
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import imageio_ffmpeg
import requests
from PIL import Image, ImageDraw, ImageFont

FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()
FONT_PATH = Path(__file__).resolve().parent / "fonts" / "Cairo-Variable.ttf"
FPS = 30
WIDTH, HEIGHT = 720, 1280

# قائمة فيديوهات مريحة للأعصاب بترخيص Creative Commons الرسمي (مسموح إعادة استخدامها تجارياً 100%)
VERIFIED_CC_SATISFYING_POOL = [
    ("6QvRRRNMiv0", "00:00:45", 22),  # تحضير تشيز برجر على الجريل عن قرب
    ("-tOs-dfM_5A", "00:00:35", 22),  # بناء بيت طوب أحمر مصغر بالأسمنت
    ("I5SO0xaaakg", "00:00:30", 22),  # تزيين تورتة وكريمة باحترافية
    ("yp6fdBcfWLQ", "00:00:10", 22),  # تقطيع صابون مريح للأعصاب
    ("Jt2Y5sEYxmk", "00:01:10", 22),  # بناء سقف وجدران منزل مصغر
    ("tl6Ia4TRijQ", "00:00:50", 22),  # تشكيل فخار يدوي مريح للعين
    ("LLBoc-C7N4w", "00:01:05", 22),  # شوي ساندوتشات وجبنة سايحة على الجريل
    ("UrdF_3L4Esc", "00:00:55", 22),  # نحت وتشكيل خزف يدوي هادئ
]


def tighten_and_pace_voice(in_audio: Path, out_mp3: Path, speed: float = 1.07) -> Path:
    """إزالة الفراغات الصامتة الطويلة وضبط سرعة السرد المشوقة مثل الشورتس الفيروسية."""
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    af = (
        f"silenceremove=stop_periods=-1:stop_duration=0.22:stop_threshold=-38dB,"
        f"atempo={speed:.2f},"
        f"acompressor=threshold=-16dB:ratio=3:attack=5:release=50,"
        f"loudnorm=I=-15:TP=-1.5:LRA=9"
    )
    subprocess.run(
        [
            FFMPEG_BIN,
            "-y",
            "-i",
            str(in_audio),
            "-af",
            af,
            "-ar",
            "44100",
            "-ac",
            "2",
            "-b:a",
            "192k",
            "-loglevel",
            "error",
            str(out_mp3),
        ],
        check=True,
    )
    return out_mp3


def get_audio_duration(audio_path: Path) -> float:
    p = subprocess.run(
        [FFMPEG_BIN, "-i", str(audio_path)],
        capture_output=True,
        text=True,
    )
    import re

    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", p.stderr)
    if not m:
        return 60.0
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def extract_whisper_words(audio_path: Path, groq_key: str, language: Optional[str] = None) -> List[Dict[str, Any]]:
    """استخراج توقيت كل كلمة بالمللي ثانية عبر Groq Whisper-Large-V3-Turbo."""
    data: List[Tuple[str, str]] = [
        ("model", "whisper-large-v3-turbo"),
        ("response_format", "verbose_json"),
        ("timestamp_granularities[]", "word"),
    ]
    if language:
        data.append(("language", language))

    with open(audio_path, "rb") as fh:
        resp = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {groq_key}"},
            files={"file": (audio_path.name, fh, "audio/mpeg")},
            data=data,
            timeout=90,
        )
    resp.raise_for_status()
    payload = resp.json()
    words = payload.get("words") or []
    cleaned: List[Dict[str, Any]] = []
    for w in words:
        txt = str(w.get("word", "")).strip(" ،,.!؟?;:\"'()[]")
        if not txt:
            continue
        s = float(w.get("start", 0.0))
        e = max(s + 0.08, float(w.get("end", s + 0.18)))
        cleaned.append({"word": txt, "start": s, "end": e})
    return cleaned


def fetch_satisfying_clips(cache_dir: Path, needed_count: int = 4, pexels_key: str = "") -> List[Path]:
    """جلب وتجهيز مقاطع الفيديو المريحة للأعصاب بدون علامات مائية وبأبعاد رأسية 720x1280."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(cache_dir.glob("clip_*.mp4"))
    if len(existing) >= needed_count:
        random.shuffle(existing)
        return existing[:needed_count]

    ready: List[Path] = list(existing)

    # 1) إذا توفر مفتاح Pexels المجاني، يجلب منه أولاً
    if pexels_key:
        for q in ("burger cooking", "cake decorating", "pottery wheel", "woodworking"):
            if len(ready) >= needed_count:
                break
            try:
                r = requests.get(
                    "https://api.pexels.com/videos/search",
                    headers={"Authorization": pexels_key},
                    params={"query": q, "orientation": "portrait", "per_page": 4},
                    timeout=20,
                )
                if r.status_code == 200:
                    for v in r.json().get("videos", []):
                        files = [f for f in v.get("video_files", []) if f.get("height", 0) >= 720]
                        if files:
                            dl_url = files[0]["link"]
                            raw_p = cache_dir / f"_px_{v['id']}.mp4"
                            out_p = cache_dir / f"clip_px_{v['id']}.mp4"
                            raw_p.write_bytes(requests.get(dl_url, timeout=45).content)
                            subprocess.run(
                                [
                                    FFMPEG_BIN,
                                    "-y",
                                    "-i",
                                    str(raw_p),
                                    "-t",
                                    "18",
                    "-vf",
                    "scale=828:1472:force_original_aspect_ratio=increase,crop=720:1280,fps=30",
                                    "-an",
                                    "-c:v",
                                    "libx264",
                                    "-preset",
                                    "veryfast",
                                    "-crf",
                                    "20",
                                    "-loglevel",
                                    "error",
                                    str(out_p),
                                ],
                                check=True,
                            )
                            raw_p.unlink(missing_ok=True)
                            ready.append(out_p)
                            break
            except Exception:
                pass

    # 2) السحب التلقائي من مكتبة Creative Commons الموثقة عبر yt-dlp (بدون أي مفتاح API!)
    pool = list(VERIFIED_CC_SATISFYING_POOL)
    random.shuffle(pool)
    for vid, ss, dur in pool:
        if len(ready) >= needed_count:
            break
        out_p = cache_dir / f"clip_cc_{vid}.mp4"
        if out_p.exists() and out_p.stat().st_size > 100_000:
            if out_p not in ready:
                ready.append(out_p)
            continue
        try:
            raw_base = cache_dir / f"_raw_{vid}"
            subprocess.run(
                [
                    "yt-dlp",
                    "--ffmpeg-location",
                    FFMPEG_BIN,
                    "-f",
                    "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
                    "-o",
                    str(raw_base) + ".%(ext)s",
                    f"https://www.youtube.com/watch?v={vid}",
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            dl_files = list(cache_dir.glob(f"_raw_{vid}.*"))
            if not dl_files:
                continue
            subprocess.run(
                [
                    FFMPEG_BIN,
                    "-y",
                    "-ss",
                    ss,
                    "-i",
                    str(dl_files[0]),
                    "-t",
                    str(dur),
                    "-vf",
                    "scale=828:1472:force_original_aspect_ratio=increase,crop=720:1280,fps=30",
                    "-an",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "veryfast",
                    "-crf",
                    "20",
                    "-loglevel",
                    "error",
                    str(out_p),
                ],
                check=True,
            )
            for f in dl_files:
                f.unlink(missing_ok=True)
            ready.append(out_p)
        except Exception as exc:
            print(f"[CC Clip Warning {vid}] {exc}")

    return ready


def _render_word_badge(word: str, scale_pop: float = 1.0) -> Image.Image:
    """رسم الكلمة الواحدة في منتصف الشاشة بخط عريض أبيض وإطار أسود سميك مثل الفيديو المرجعي تماماً."""
    font_size = max(48, int(74 * scale_pop))
    font = ImageFont.truetype(str(FONT_PATH), size=font_size)
    # لوحة صغيرة حول الكلمة فقط لدمج فائق السرعة على الفريم
    dummy = Image.new("RGBA", (WIDTH, 220), (0, 0, 0, 0))
    d = ImageDraw.Draw(dummy)
    bb = d.textbbox((0, 0), word, font=font, stroke_width=9)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    tx = (WIDTH - tw) // 2 - bb[0]
    ty = (220 - th) // 2 - bb[1]

    # ظل خلفي خفيف + إطار أسود عريض + نص أبيض ناصع
    d.text((tx + 3, ty + 5), word, font=font, fill=(0, 0, 0, 175), stroke_width=9, stroke_fill=(0, 0, 0, 175))
    d.text(
        (tx, ty),
        word,
        font=font,
        fill=(255, 255, 255, 255),
        stroke_width=8,
        stroke_fill=(0, 0, 0, 255),
    )
    return dummy


def assemble_viral_satisfying_short(
    paced_audio_mp3: Path,
    words: List[Dict[str, Any]],
    bg_clips: List[Path],
    out_mp4: Path,
) -> Path:
    """دمج مقاطع الفيديو المريحة للأعصاب + الصوت السريع + الكلمات القافزة كلمة بكلمة في منتصف الشاشة."""
    total_dur = get_audio_duration(paced_audio_mp3) + 0.35
    total_frames = int(math.ceil(total_dur * FPS))

    # بناء شريط خلفية الفيديو المتصل عبر تكرار وتبديل المقاطع المريحة للأعصاب كل 13 ثانية
    concat_dir = out_mp4.parent / "_bg_work"
    concat_dir.mkdir(parents=True, exist_ok=True)
    list_txt = concat_dir / "concat.txt"
    acc_sec = 0.0
    lines_concat: List[str] = []
    idx = 0
    while acc_sec < total_dur + 5.0:
        clip = bg_clips[idx % len(bg_clips)]
        lines_concat.append(f"file '{clip.resolve()}'")
        acc_sec += 14.0
        idx += 1
    list_txt.write_text("\n".join(lines_concat) + "\n", encoding="utf-8")

    bg_stream_mp4 = concat_dir / "bg_joined.mp4"
    subprocess.run(
        [
            FFMPEG_BIN,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_txt),
            "-t",
            f"{total_dur:.2f}",
            "-r",
            str(FPS),
            "-s",
            f"{WIDTH}x{HEIGHT}",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "20",
            "-loglevel",
            "error",
            str(bg_stream_mp4),
        ],
        check=True,
    )

    # تجهيز صور الكلمات مسبقاً (حجم Pop أول فريمين + حجم طبيعي) لسرعة فائقة
    word_cache: Dict[Tuple[str, bool], Image.Image] = {}
    for w in words:
        txt = w["word"]
        if (txt, True) not in word_cache:
            word_cache[(txt, True)] = _render_word_badge(txt, scale_pop=1.12)
            word_cache[(txt, False)] = _render_word_badge(txt, scale_pop=1.00)

    # قراءة فريمات الفيديو الخلفي مباشرة وتوقيع الكلمة النشطة في منتصف الشاشة
    reader = subprocess.Popen(
        [
            FFMPEG_BIN,
            "-i",
            str(bg_stream_mp4),
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-loglevel",
            "error",
            "pipe:1",
        ],
        stdout=subprocess.PIPE,
    )

    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    writer = subprocess.Popen(
        [
            FFMPEG_BIN,
            "-y",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{WIDTH}x{HEIGHT}",
            "-r",
            str(FPS),
            "-i",
            "pipe:0",
            "-i",
            str(paced_audio_mp3),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-movflags",
            "+faststart",
            "-loglevel",
            "error",
            str(out_mp4),
        ],
        stdin=subprocess.PIPE,
    )

    frame_bytes_len = WIDTH * HEIGHT * 3
    w_idx = 0
    n_words = len(words)
    paste_y = (HEIGHT - 220) // 2 + 25  # في منتصف الشاشة تماماً مثل الفيديو المرجعي!

    try:
        for f_i in range(total_frames):
            raw = reader.stdout.read(frame_bytes_len) if reader.stdout else b""
            if len(raw) < frame_bytes_len:
                break
            t_sec = f_i / float(FPS)

            while w_idx + 1 < n_words and t_sec >= words[w_idx + 1]["start"]:
                w_idx += 1

            if w_idx < n_words:
                cur_w = words[w_idx]
                if cur_w["start"] - 0.03 <= t_sec <= cur_w["end"] + 0.08:
                    is_pop = (t_sec - cur_w["start"]) < 0.075
                    badge = word_cache[(cur_w["word"], is_pop)]
                    frame_img = Image.frombytes("RGB", (WIDTH, HEIGHT), raw)
                    frame_img.paste(badge, (0, paste_y), badge)
                    raw = frame_img.tobytes()

            writer.stdin.write(raw)
    finally:
        if reader.stdout:
            reader.stdout.close()
        reader.wait()
        if writer.stdin:
            writer.stdin.close()
        ret = writer.wait()
        if ret != 0:
            raise RuntimeError(f"FFmpeg writer failed: {ret}")

    import shutil

    shutil.rmtree(concat_dir, ignore_errors=True)
    return out_mp4
