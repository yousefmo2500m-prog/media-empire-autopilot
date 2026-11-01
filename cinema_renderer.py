# -*- coding: utf-8 -*-
"""
محرك الإخراج السينمائي الحقيقي V2.0 (Pure Netflix 35mm Cinema Renderer — Zero Study Boxes!)
- يولّد لقطة سينمائية فوتوغرافية جديدة (35mm Film Still) لكل جملة عبر FLUX.1-schnell بدون أي علامات مائية.
- صفر صناديق مذاكرة أو إطارات: شاشة سينما كاملة مع حركة كاميرا حقيقية (Dolly Push / Pull / Handheld Drift)،
  مطر متحرك، وميض برق عند الرعد، وترجمة سينمائية صفراء قصيرة متتابعة (6-7 كلمات فقط في اللحظة) مثل أفلام نتفليكس!
"""

import io
import math
import re
import subprocess
import time
import urllib.parse
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import imageio_ffmpeg
import numpy as np
import requests
from gradio_client import Client
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()
FONT_PATH = Path(__file__).resolve().parent / "fonts" / "Cairo-Variable.ttf"
FPS = 24

_FLUX_CLIENT: Optional[Client] = None


def _get_flux() -> Client:
    global _FLUX_CLIENT
    if _FLUX_CLIENT is None:
        import os

        hf_tok = os.environ.get("HF_TOKEN", "").strip() or None
        _FLUX_CLIENT = Client("black-forest-labs/FLUX.1-schnell", token=hf_tok)
    return _FLUX_CLIENT


def _clean_text(text: str) -> str:
    cleaned = re.sub(r"[\U00010000-\U0010ffff\u2600-\u27bf\ufe0f]", "", str(text or ""))
    return " ".join(cleaned.split()).strip()


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size=size)


def generate_35mm_shot(prompt_en: str, target_w: int, target_h: int, seed: int) -> Image.Image:
    """توليد لقطة سينمائية واقعية 35mm عبر FLUX.1-schnell (مع بديل فوري عند الضغط)."""
    overscale_w = int(target_w * 1.18)
    overscale_h = int(target_h * 1.18)
    gen_w, gen_h = (1280, 720) if target_w >= target_h else (720, 1280)

    full_prompt = (
        f"{prompt_en}, 35mm anamorphic cinema film still, dramatic chiaroscuro lighting, "
        "ultra realistic photography, shallow depth of field, Kodak Vision3 film grain, strictly no text, no watermark"
    )

    img: Optional[Image.Image] = None

    # 1) المحرك الأول: FLUX.1-schnell الفائق الواقعية بدون أي علامات مائية
    for attempt in range(2):
        try:
            client = _get_flux()
            res = client.predict(
                prompt=full_prompt,
                seed=int(seed % 2147483647),
                randomize_seed=False,
                width=gen_w,
                height=gen_h,
                num_inference_steps=4,
                api_name="/infer",
            )
            img_path = res[0] if isinstance(res, (tuple, list)) else res
            img = Image.open(str(img_path)).convert("RGB")
            break
        except Exception as exc:
            print(f"[FLUX Retry {attempt + 1}] {exc}")
            time.sleep(2.0)

    # 2) المحرك الاحتياطي إن كان FLUX مزدحماً (مع احترام فاصل 46 ثانية المجاني لضمان نجاح 100% من اللقطات بدون أي شاشة مظلمة)
    if img is None:
        for p_try in range(2):
            try:
                if p_try > 0:
                    time.sleep(46.0)
                short_p = urllib.parse.quote(" ".join(prompt_en.split()[:16]) + ", 35mm dark cinema photo, no text")
                url = f"https://image.pollinations.ai/prompt/{short_p}?width={gen_w}&height={gen_h}&nologo=true&seed={seed}"
                r = requests.get(url, timeout=35)
                if r.status_code == 200 and len(r.content) > 8000:
                    raw = Image.open(io.BytesIO(r.content)).convert("RGB")
                    w0, h0 = raw.size
                    img = raw.crop((int(w0 * 0.1), int(h0 * 0.1), int(w0 * 0.9), int(h0 * 0.9)))
                    break
                if r.status_code == 402:
                    time.sleep(46.0)
            except Exception:
                time.sleep(5.0)

    if img is None:
        # خلفية ضبابية مظلمة احتياطية للطوارئ فقط
        arr = np.zeros((overscale_h, overscale_w, 3), dtype=np.uint8)
        arr[..., 0] = 14
        arr[..., 1] = 18
        arr[..., 2] = 26
        img = Image.fromarray(arr, mode="RGB")

    # ملء الأبعاد بدقة سينمائية
    src_r = img.width / img.height
    dst_r = overscale_w / overscale_h
    if src_r > dst_r:
        nh = overscale_h
        nw = int(nh * src_r)
    else:
        nw = overscale_w
        nh = int(nw / src_r)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    lx, ty = (nw - overscale_w) // 2, (nh - overscale_h) // 2
    img = img.crop((lx, ty, lx + overscale_w, ty + overscale_h))

    img = ImageEnhance.Contrast(img).enhance(1.08)
    return img


def _split_into_movie_beats(text: str, start_sec: float, end_sec: float) -> List[Tuple[float, float, str]]:
    """تقسيم الجملة الطويلة إلى لقطات ترجمة سينمائية قصيرة (6-7 كلمات فقط) متزامنة مع الصوت."""
    words = _clean_text(text).split()
    if not words:
        return []
    chunk_size = 7
    chunks = [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)]
    total_chars = sum(len(c) for c in chunks) or 1
    total_dur = max(0.4, end_sec - start_sec)

    beats: List[Tuple[float, float, str]] = []
    cur = start_sec
    for c in chunks:
        frac = len(c) / total_chars
        d = total_dur * frac
        beats.append((cur, cur + d, c))
        cur += d
    return beats


def _build_subtitle_layer(
    width: int,
    height: int,
    text: str,
    sub_color: Tuple[int, int, int],
) -> Image.Image:
    """ترجمة أفلام نتفليكس نظيفة بدون أي صناديق خلفية مع شريطي سينما خفيفين."""
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    is_vert = height > width

    font = _load_font(46 if is_vert else 38)
    max_w = int(width * 0.84)

    # تقسيم لسطرين كحد أقصى
    words = text.split()
    lines: List[str] = []
    cur = ""
    for w in words:
        cand = f"{cur} {w}".strip()
        bb = draw.textbbox((0, 0), cand, font=font)
        if bb[2] - bb[0] <= max_w or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)

    line_h = 58 if is_vert else 48
    base_y = height - (240 if is_vert else 88) - (len(lines) - 1) * line_h

    for idx, ln in enumerate(lines):
        bb = draw.textbbox((0, 0), ln, font=font)
        tw = bb[2] - bb[0]
        tx = (width - tw) // 2
        ty = base_y + idx * line_h
        # ظل سينمائي ناعم + تحديد أسود رفيع بدون أي صندوق!
        draw.text((tx + 2, ty + 3), ln, font=font, fill=(0, 0, 0, 210))
        draw.text(
            (tx, ty),
            ln,
            font=font,
            fill=(*sub_color, 255),
            stroke_width=3,
            stroke_fill=(0, 0, 0, 245),
        )
    return layer


def _make_cinema_grade_overlay(width: int, height: int) -> Image.Image:
    """تظليل سينمائي ناعم للجزء السفلي وشريطي Letterbox ليعطي إحساس الفيلم الحقيقي."""
    rgba = np.zeros((height, width, 4), dtype=np.uint8)
    ynorm = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, None]
    xnorm = np.linspace(-1.0, 1.0, width, dtype=np.float32)[None, :]
    vignette = np.clip((xnorm**2 + (ynorm * 2 - 1) ** 2) * 0.32, 0.0, 0.55)
    bottom_grad = np.clip((ynorm - 0.68) / 0.32, 0.0, 1.0) * 0.62
    alpha = np.clip(vignette + bottom_grad, 0.0, 0.82) * 255.0
    rgba[..., 3] = alpha.astype(np.uint8)

    if width > height:
        # شريطان سينمائيان رفيعان أعلى وأسفل الكادر (Anamorphic Cinema Look)
        bar = 28
        rgba[:bar, :, 3] = 255
        rgba[-bar:, :, 3] = 255

    return Image.fromarray(rgba, mode="RGBA")


def render_cinema_video(
    channel_cfg: Dict[str, Any],
    script_data: Dict[str, Any],
    timed_segments: List[Dict[str, Any]],
    audio_wav: Path,
    out_mp4: Path,
    aspect: str = "16:9",
    seed: int = 2026,
) -> Tuple[Path, Image.Image]:
    """إخراج الفيلم الكامل بلقطات متغيرة وحركة كاميرا ومطر وبرق وترجمة سينمائية."""
    width, height = (1280, 720) if aspect == "16:9" else (1080, 1920)
    sub_color = channel_cfg.get("subtitle_color", (255, 218, 68))

    # 1) توليد لقطة سينمائية 35mm مستقلة لكل مقطع!
    shots: List[Dict[str, Any]] = []
    all_beats: List[Tuple[float, float, Image.Image]] = []

    for idx, seg in enumerate(timed_segments):
        print(f"   🎞️ تصوير اللقطة السينمائية {idx + 1}/{len(timed_segments)}...")
        art = generate_35mm_shot(
            prompt_en=seg.get("shot_prompt_en") or "dark moody thriller room 35mm film",
            target_w=width,
            target_h=height,
            seed=seed + idx * 97,
        )
        # تحديد مدى اللقطة من نهاية السابقة إلى بداية التالية بدون فجوات سوداء
        t0 = 0.0 if idx == 0 else (timed_segments[idx - 1]["end_sec"] + seg["start_sec"]) * 0.5
        t1 = (
            9999.0
            if idx == len(timed_segments) - 1
            else (seg["end_sec"] + timed_segments[idx + 1]["start_sec"]) * 0.5
        )
        shots.append(
            {
                "art": art,
                "t0": t0,
                "t1": t1,
                "move": seg.get("camera_move", "push_in" if idx % 2 == 0 else "pull_out"),
                "rain": bool(seg.get("rain_fx", False)),
                "flash_at": seg["start_sec"] - 0.15 if seg.get("sfx") in ("thunder", "reveal") else None,
            }
        )
        for bs, be, btxt in _split_into_movie_beats(seg["text"], seg["start_sec"], seg["end_sec"]):
            all_beats.append((bs, be, _build_subtitle_layer(width, height, btxt, sub_color)))

    with wave.open(str(audio_wav), "rb") as wf:
        total_duration = wf.getnframes() / float(wf.getframerate())
    shots[-1]["t1"] = total_duration

    total_frames = max(1, int(math.ceil(total_duration * FPS)))
    grade_overlay = _make_cinema_grade_overlay(width, height)

    # خطوط مطر سينمائية متحركة للقطات الخارجية
    rng = np.random.default_rng(seed)
    rain_drops = [
        (rng.uniform(0.0, 1.0), rng.uniform(0.0, 1.0), rng.uniform(1.4, 2.2), int(rng.uniform(18, 36)))
        for _ in range(55)
    ]

    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        FFMPEG_BIN,
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{width}x{height}",
        "-r",
        str(FPS),
        "-i",
        "pipe:0",
        "-i",
        str(audio_wav),
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
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    shot_i = 0
    beat_i = 0

    def _sample_shot(sh: Dict[str, Any], t_now: float) -> Image.Image:
        art: Image.Image = sh["art"]
        span = max(0.5, sh["t1"] - sh["t0"])
        p = float(np.clip((t_now - sh["t0"]) / span, 0.0, 1.0))

        move = sh["move"]
        if move == "pull_out":
            zoom = 1.15 - 0.12 * p
            px, py = 0.5, 0.5
        elif move == "pan_right":
            zoom = 1.08
            px, py = p, 0.5
        elif move == "pan_left":
            zoom = 1.08
            px, py = 1.0 - p, 0.5
        else:  # push_in + حركة تنفس كاميرا سينمائية طبيعية
            zoom = 1.01 + 0.14 * p
            px = 0.5 + 0.08 * math.sin(t_now * 0.7)
            py = 0.5 + 0.05 * math.cos(t_now * 0.55)

        cw, ch = int(art.width / zoom), int(art.height / zoom)
        cx = int(max(0, art.width - cw) * np.clip(px, 0.0, 1.0))
        cy = int(max(0, art.height - ch) * np.clip(py, 0.0, 1.0))
        return art.crop((cx, cy, cx + cw, cy + ch)).resize((width, height), Image.Resampling.BILINEAR)

    try:
        for f_idx in range(total_frames):
            t_sec = f_idx / float(FPS)

            while shot_i + 1 < len(shots) and t_sec >= shots[shot_i]["t1"]:
                shot_i += 1

            cur_shot = shots[shot_i]
            frame_rgb = _sample_shot(cur_shot, t_sec)

            # انتقال تلاشي سينمائي ناعم (Cross-Dissolve 0.35s) بين اللقطات!
            if shot_i > 0 and (t_sec - cur_shot["t0"]) < 0.35:
                alpha_mix = float(np.clip((t_sec - cur_shot["t0"]) / 0.35, 0.0, 1.0))
                prev_rgb = _sample_shot(shots[shot_i - 1], t_sec)
                frame_rgb = Image.blend(prev_rgb, frame_rgb, alpha_mix)

            frame = frame_rgb.convert("RGBA")

            # خيوط المطر الليلي المتحركة في اللقطات الممطرة
            if cur_shot["rain"]:
                rdraw = ImageDraw.Draw(frame, "RGBA")
                for rx, ry, rspd, rlen in rain_drops:
                    yy = ((ry + t_sec * rspd) % 1.05) * height
                    xx = ((rx - t_sec * 0.18) % 1.0) * width
                    rdraw.line((xx, yy, xx - rlen * 0.28, yy + rlen), fill=(200, 220, 255, 62), width=2)

            # وميض برق خاطف لحظة الرعد أو الصدمة الدرامية
            if cur_shot["flash_at"] is not None and 0.0 <= (t_sec - cur_shot["flash_at"]) <= 0.18:
                fl_strength = int((1.0 - (t_sec - cur_shot["flash_at"]) / 0.18) * 115)
                flash_layer = Image.new("RGBA", (width, height), (225, 238, 255, fl_strength))
                frame.alpha_composite(flash_layer)

            frame.alpha_composite(grade_overlay)

            # إظهار الترجمة السينمائية القصيرة المتزامنة
            while beat_i + 1 < len(all_beats) and t_sec >= all_beats[beat_i][1]:
                beat_i += 1
            if beat_i < len(all_beats):
                bs, be, blayer = all_beats[beat_i]
                if bs - 0.06 <= t_sec <= be + 0.12:
                    frame.alpha_composite(blayer)

            proc.stdin.write(frame.convert("RGB").tobytes())
    finally:
        if proc.stdin:
            proc.stdin.close()
        ret = proc.wait()
        if ret != 0:
            raise RuntimeError(f"FFmpeg exited with code {ret}")

    return out_mp4, shots[0]["art"]


def render_youtube_thumbnail(
    channel_cfg: Dict[str, Any],
    script_data: Dict[str, Any],
    hero_art: Image.Image,
    out_jpg: Path,
) -> Path:
    """بوستر يوتيوب سينمائي من اللقطة البطولية بدون أي إطارات مدرسية."""
    w, h = 1280, 720
    canvas = hero_art.resize((w, h), Image.Resampling.LANCZOS).convert("RGBA")
    shade = _make_cinema_grade_overlay(w, h)
    canvas.alpha_composite(shade)

    draw = ImageDraw.Draw(canvas, "RGBA")
    headline = _clean_text(script_data.get("thumbnail_headline") or script_data.get("episode_title", ""))
    font_big = _load_font(82)

    bb = draw.textbbox((0, 0), headline, font=font_big)
    tw = bb[2] - bb[0]
    tx = (w - tw) // 2
    ty = h - 155
    draw.text((tx + 4, ty + 5), headline, font=font_big, fill=(0, 0, 0, 230))
    draw.text(
        (tx, ty),
        headline,
        font=font_big,
        fill=(255, 220, 65, 255),
        stroke_width=5,
        stroke_fill=(0, 0, 0, 255),
    )
    out_jpg.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(str(out_jpg), quality=93)
    return out_jpg
