# -*- coding: utf-8 -*-
"""
استوديو الصوت السينمائي وتعدد الشخصيات (Multi-Voice Neural TTS + Copyright-Free Cinema Score)
يولّد أصوات الشخصيات والراوي عبر edge-tts، ويمزجها مع موسيقى تصويرية ومؤثرات صوتية
مولّدة رياضياً بنسبة 100% لضمان صفر مطالبات حقوق طبع ونشر (0% Content ID) مدى الحياة.
"""

import asyncio
import os
import subprocess
import wave
from pathlib import Path
from typing import Dict, List, Tuple

import edge_tts
import imageio_ffmpeg
import numpy as np

SAMPLE_RATE = 44100
FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()


async def _synth_line_async(
    text: str,
    voice: str,
    rate: str,
    pitch: str,
    out_mp3: Path,
) -> None:
    last_err = None
    fallback_voices = [voice, "ar-SA-HamedNeural", "en-US-ChristopherNeural"]
    for idx, v in enumerate(fallback_voices):
        try:
            comm = edge_tts.Communicate(
                text=text,
                voice=v,
                rate=rate if idx == 0 else "+0%",
                pitch=pitch if idx == 0 else "+0Hz",
            )
            await comm.save(str(out_mp3))
            if out_mp3.exists() and out_mp3.stat().st_size > 400:
                return
        except Exception as exc:
            last_err = exc
            await asyncio.sleep(1.2)
    raise RuntimeError(f"فشل توليد الصوت للنص ({text[:35]}...): {last_err}")


def decode_audio_to_stereo_float(audio_path: Path) -> np.ndarray:
    """فك ضغط ملف الصوت إلى مصفوفة ستيريو 44.1kHz float32 عبر FFmpeg."""
    cmd = [
        FFMPEG_BIN,
        "-y",
        "-i",
        str(audio_path),
        "-f",
        "s16le",
        "-acodec",
        "pcm_s16le",
        "-ar",
        str(SAMPLE_RATE),
        "-ac",
        "2",
        "-loglevel",
        "error",
        "pipe:1",
    ]
    proc = subprocess.run(cmd, capture_output=True, check=True)
    pcm = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    if pcm.size == 0:
        return np.zeros((SAMPLE_RATE, 2), dtype=np.float32)
    return pcm.reshape(-1, 2)


def generate_ambient_cinema_bed(
    total_samples: int,
    mood: str,
    scene_boundaries_samples: List[int],
    seed: int = 101,
) -> np.ndarray:
    """
    توليد موسيقى تصويرية سينمائية أصلية + مؤثرات جوية (مطر خفيف / نبض غموض / دقات ساعة)
    بدون أي عينات خارجية — آمنة 100% على يوتيوب وفيسبوك للأبد.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(total_samples, dtype=np.float32) / SAMPLE_RATE

    # ترددات الكورد الأساسي حسب هوية القناة
    if mood == "suspense_noir":
        # D minor 9 سينمائي دافئ للروايات الدرامية والغموض
        freqs = [73.42, 110.00, 146.83, 174.61, 220.00, 329.63]
    elif mood == "dark_sci":
        # C minor مستقبلي للعلوم والأسرار بالإنجليزية
        freqs = [65.41, 98.00, 130.81, 155.56, 196.00, 293.66]
    elif mood == "epic_history":
        # A Phrygian شرقي تاريخي مهيب
        freqs = [55.00, 82.41, 110.00, 116.54, 164.81, 220.00]
    else:  # detective_tick
        # E minor بوليسي تفاعلي
        freqs = [82.41, 123.47, 164.81, 196.00, 246.94]

    left = np.zeros(total_samples, dtype=np.float32)
    right = np.zeros(total_samples, dtype=np.float32)

    for i, f in enumerate(freqs):
        lfo_rate = 0.07 + 0.03 * i
        pan = 0.35 + 0.3 * np.sin(2 * np.pi * (0.04 + 0.015 * i) * t + i)
        amp = (0.28 / (i + 1.2)) * (0.72 + 0.28 * np.sin(2 * np.pi * lfo_rate * t + i * 1.1))
        wave_l = np.sin(2 * np.pi * (f * 0.999) * t) * amp * pan
        wave_r = np.sin(2 * np.pi * (f * 1.001) * t + 0.4) * amp * (1.0 - pan * 0.5)
        left += wave_l
        right += wave_r

    # مؤثر مطر ليلي ناعم جداً في مسرح الروايات
    if mood == "suspense_noir":
        noise = rng.normal(0.0, 0.018, size=total_samples).astype(np.float32)
        # تنعيم الضوضاء لتبدو كمطر دافئ خلف النافذة
        kernel = np.ones(18, dtype=np.float32) / 18.0
        soft_rain = np.convolve(noise, kernel, mode="same")
        left += soft_rain * 0.85
        right += np.roll(soft_rain, 120) * 0.85

    # نبضة انتقال سينمائية هادئة (Sub-boom) عند بداية كل مشهد جديد
    boom_len = int(0.95 * SAMPLE_RATE)
    boom_t = np.arange(boom_len, dtype=np.float32) / SAMPLE_RATE
    boom_freq = 68.0 * np.exp(-boom_t * 2.1) + 34.0
    boom_wave = np.sin(2 * np.pi * np.cumsum(boom_freq) / SAMPLE_RATE) * np.exp(-boom_t * 3.8) * 0.22
    for b_idx in scene_boundaries_samples:
        if 0 <= b_idx < total_samples - 100:
            end_i = min(total_samples, b_idx + boom_len)
            seg = boom_wave[: end_i - b_idx]
            left[b_idx:end_i] += seg
            right[b_idx:end_i] += seg

    # دقات ساعة تشويقية في آخر 8 ثوانٍ لقناة الألغاز
    if mood == "detective_tick" and total_samples > SAMPLE_RATE * 10:
        tick_start = max(0, total_samples - int(8.5 * SAMPLE_RATE))
        tick_len = int(0.06 * SAMPLE_RATE)
        tt = np.arange(tick_len, dtype=np.float32) / SAMPLE_RATE
        tick_click = np.sin(2 * np.pi * 1150.0 * tt) * np.exp(-tt * 55.0) * 0.18
        pos = tick_start
        step = int(0.5 * SAMPLE_RATE)
        while pos + tick_len < total_samples - int(0.5 * SAMPLE_RATE):
            left[pos : pos + tick_len] += tick_click
            right[pos : pos + tick_len] += tick_click
            pos += step

    bed = np.stack([left, right], axis=1)
    peak = np.max(np.abs(bed)) + 1e-6
    return (bed / peak) * 0.26


def build_episode_soundtrack(
    segments: List[Dict],
    voices_map: Dict[str, Dict],
    mood: str,
    work_dir: Path,
    out_wav: Path,
    seed: int = 101,
) -> List[Dict]:
    """
    يبني الشريط الصوتي الكامل للحلقة:
    - يولّد صوت كل سطر بشخصيته المحددة (الراوي / البطل / المحقق / البطلة)
    - يحسب التوقيت الدقيق بالثواني لكل مشهد وسطر (لاستخدامه في المونتاج والترجمة)
    - يدمج الأصوات مع الموسيقى التصويرية مع خفض تلقائي للموسيقى وقت الكلام (Auto-Ducking).
    """
    work_dir.mkdir(parents=True, exist_ok=True)

    async def _batch_generate():
        tasks = []
        for idx, seg in enumerate(segments):
            role = seg.get("speaker", "narrator")
            v_cfg = voices_map.get(role) or next(iter(voices_map.values()))
            mp3_path = work_dir / f"line_{idx:03d}.mp3"
            seg["_mp3_path"] = mp3_path
            seg["_speaker_label"] = seg.get("speaker_name") or v_cfg.get("label", "🎙️")
            tasks.append(
                _synth_line_async(
                    text=seg["text"],
                    voice=v_cfg["voice"],
                    rate=v_cfg.get("rate", "+0%"),
                    pitch=v_cfg.get("pitch", "+0Hz"),
                    out_mp3=mp3_path,
                )
            )
        # تشغيل بحد أقصى 3 اتصالات متزامنة لثبات الخدمة 100%
        sem = asyncio.Semaphore(3)

        async def _guarded(coro):
            async with sem:
                return await coro

        await asyncio.gather(*[_guarded(t) for t in tasks])

    asyncio.run(_batch_generate())

    # تجميع المقاطع الصوتية مع فواصل تنفّس درامية طبيعية
    intro_pad = int(0.85 * SAMPLE_RATE)
    outro_pad = int(1.40 * SAMPLE_RATE)
    voice_chunks: List[np.ndarray] = [np.zeros((intro_pad, 2), dtype=np.float32)]
    envelope_chunks: List[np.ndarray] = [np.zeros(intro_pad, dtype=np.float32)]
    scene_boundaries: List[int] = [0]

    cursor_samples = intro_pad
    prev_scene_id = None
    timed_segments: List[Dict] = []

    for idx, seg in enumerate(segments):
        pcm = decode_audio_to_stereo_float(seg["_mp3_path"])
        # تطبيع صوت المتحدث لمستوى استوديو واضح وموحد
        v_peak = np.max(np.abs(pcm)) + 1e-6
        pcm = (pcm / v_peak) * 0.88

        scene_id = seg.get("scene_id", idx)
        if prev_scene_id is not None and scene_id != prev_scene_id:
            # فاصل درامي أطول قليلاً عند الانتقال لمشهد بصري جديد
            gap = int(0.62 * SAMPLE_RATE)
            voice_chunks.append(np.zeros((gap, 2), dtype=np.float32))
            envelope_chunks.append(np.zeros(gap, dtype=np.float32))
            cursor_samples += gap
            scene_boundaries.append(cursor_samples)
        elif idx > 0:
            gap = int(0.32 * SAMPLE_RATE)
            voice_chunks.append(np.zeros((gap, 2), dtype=np.float32))
            envelope_chunks.append(np.zeros(gap, dtype=np.float32))
            cursor_samples += gap

        start_sec = cursor_samples / SAMPLE_RATE
        dur_sec = pcm.shape[0] / SAMPLE_RATE
        end_sec = start_sec + dur_sec

        voice_chunks.append(pcm)
        envelope_chunks.append(np.ones(pcm.shape[0], dtype=np.float32))
        cursor_samples += pcm.shape[0]
        prev_scene_id = scene_id

        enriched = dict(seg)
        enriched.pop("_mp3_path", None)
        enriched["start_sec"] = round(start_sec, 3)
        enriched["end_sec"] = round(end_sec, 3)
        enriched["duration_sec"] = round(dur_sec, 3)
        enriched["speaker_badge"] = seg["_speaker_label"]
        timed_segments.append(enriched)

    voice_chunks.append(np.zeros((outro_pad, 2), dtype=np.float32))
    envelope_chunks.append(np.zeros(outro_pad, dtype=np.float32))
    total_samples = cursor_samples + outro_pad

    voice_track = np.concatenate(voice_chunks, axis=0)
    speech_env = np.concatenate(envelope_chunks, axis=0)

    # تنعيم غلاف الخفض التلقائي (Smooth Auto-Ducking)
    smooth_win = int(0.25 * SAMPLE_RATE)
    duck_kernel = np.ones(smooth_win, dtype=np.float32) / smooth_win
    smooth_env = np.convolve(speech_env, duck_kernel, mode="same")
    # الموسيقى تنخفض لـ 38% أثناء الحديث وترتفع لـ 90% في الفواصل الدرامية
    bed_gain = (0.90 - 0.52 * smooth_env)[:, None]

    bed_track = generate_ambient_cinema_bed(
        total_samples=total_samples,
        mood=mood,
        scene_boundaries_samples=scene_boundaries,
        seed=seed,
    )

    # تلاشي دخول وخروج احترافي (Fade In / Fade Out)
    fade_in = min(int(0.8 * SAMPLE_RATE), total_samples // 4)
    fade_out = min(int(1.2 * SAMPLE_RATE), total_samples // 4)
    bed_track[:fade_in] *= np.linspace(0.0, 1.0, fade_in, dtype=np.float32)[:, None]
    bed_track[-fade_out:] *= np.linspace(1.0, 0.0, fade_out, dtype=np.float32)[:, None]

    mixed = voice_track + bed_track * bed_gain
    mixed = np.tanh(mixed * 1.08) * 0.94  # Soft studio limiter

    pcm16 = (np.clip(mixed, -1.0, 1.0) * 32767.0).astype(np.int16)
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm16.tobytes())

    return timed_segments
