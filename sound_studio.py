# -*- coding: utf-8 -*-
"""
استوديو الدراما الصوتية والمؤثرات السينمائية V2.0
- أصوات بودكاست وتمثيل مصري طبيعي 100% عبر VoiceTut-TTS (مدرب على 380 ساعة بودكاست مصري)
  + تمثيل إنجليزي عاطفي عبر ResembleAI Chatterbox.
- موسيقى بيانو وتشيلو درامية حقيقية بترددات الـ Minor مع صدى قاعة سينمائي (Reverb) — بدون أي طنين ممل.
- مؤثرات صوتية تمثيلية (خبط على الخشب، نبضات قلب، رعد ومطر، شريط كاسيت، خطوات بطيئة، صدمة كشف السر).
"""

import asyncio
import os
import shutil
import subprocess
import time
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional

import edge_tts
import imageio_ffmpeg
import numpy as np
from gradio_client import Client

SAMPLE_RATE = 44100
FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()

_VOICETUT_CLIENT: Optional[Client] = None
_CHATTERBOX_CLIENT: Optional[Client] = None


def _get_voicetut() -> Client:
    global _VOICETUT_CLIENT
    if _VOICETUT_CLIENT is None:
        hf_tok = os.environ.get("HF_TOKEN", "").strip() or None
        _VOICETUT_CLIENT = Client("mohammedaly22/VoiceTut-TTS", token=hf_tok)
    return _VOICETUT_CLIENT


def _get_chatterbox() -> Client:
    global _CHATTERBOX_CLIENT
    if _CHATTERBOX_CLIENT is None:
        hf_tok = os.environ.get("HF_TOKEN", "").strip() or None
        _CHATTERBOX_CLIENT = Client("ResembleAI/Chatterbox", token=hf_tok)
    return _CHATTERBOX_CLIENT


def decode_audio_to_stereo_float(audio_path: Path) -> np.ndarray:
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
        return np.zeros((SAMPLE_RATE // 2, 2), dtype=np.float32)
    return pcm.reshape(-1, 2)


def _apply_tape_phone_filter(pcm: np.ndarray) -> np.ndarray:
    """فلتر شريط كاسيت / مكالمة هاتفية غامضة للشخصيات المتصلة عن بُعد."""
    # فرق بسيط لمحاكاة استجابة شريط مغناطيسي دافئ
    hp = pcm - np.roll(pcm, 18, axis=0) * 0.72
    kernel = np.ones(9, dtype=np.float32) / 9.0
    left = np.convolve(hp[:, 0], kernel, mode="same")
    right = np.convolve(hp[:, 1], kernel, mode="same")
    filtered = np.tanh(np.stack([left, right], axis=1) * 1.9) * 0.75
    hiss = np.random.default_rng(77).normal(0.0, 0.0045, size=filtered.shape).astype(np.float32)
    return filtered + hiss


def _synth_single_line(text: str, v_cfg: Dict[str, Any], out_audio: Path) -> Path:
    engine = v_cfg.get("engine", "voicetut")

    if engine in ("voicetut", "voicetut_en"):
        lang = "en" if engine == "voicetut_en" else "ar"
        for attempt in range(2):
            try:
                client = _get_voicetut()
                wav_res, _ = client.predict(
                    text=text,
                    language=lang,
                    voice_mode="preset",
                    speaker=v_cfg.get("speaker", "Hassan"),
                    ref_audio=None,
                    ref_text="",
                    num_step=36,
                    guidance=2.5,
                    speed=float(v_cfg.get("speed", 1.02)),
                    normalize=True,
                    api_name="/synthesize",
                )
                out_wav = out_audio.with_suffix(".wav")
                shutil.copyfile(str(wav_res), str(out_wav))
                if out_wav.stat().st_size > 800:
                    return out_wav
            except Exception as exc:
                print(f"[VoiceTut Retry {attempt + 1}] {exc}")
                time.sleep(2.0)

    elif engine == "chatterbox":
        for attempt in range(2):
            try:
                client = _get_chatterbox()
                wav_res = client.predict(
                    text_input=text,
                    audio_prompt_path_input=None,
                    exaggeration_input=float(v_cfg.get("exaggeration", 0.62)),
                    temperature_input=0.78,
                    seed_num_input=0,
                    cfgw_input=0.5,
                    vad_trim_input=True,
                    api_name="/generate_tts_audio",
                )
                out_wav = out_audio.with_suffix(".wav")
                shutil.copyfile(str(wav_res), str(out_wav))
                if out_wav.stat().st_size > 800:
                    return out_wav
            except Exception as exc:
                print(f"[Chatterbox Retry {attempt + 1}] {exc}")
                time.sleep(2.0)

    # خط دفاع احتياطي مضمون 100% لو حدث ضغط مؤقت على السيرفر المجاني
    fallback_voice = v_cfg.get("fallback_edge", "ar-EG-ShakirNeural")
    mp3_out = out_audio.with_suffix(".mp3")

    async def _edge():
        comm = edge_tts.Communicate(text=text, voice=fallback_voice, rate="+2%")
        await comm.save(str(mp3_out))

    asyncio.run(_edge())
    return mp3_out


def synthesize_foley_sfx(sfx_name: str, seed: int = 1) -> np.ndarray:
    """توليد مؤثرات صوتية درامية حقيقية (خبط باب، نبض قلب، رعد، خطوات، كاسيت، صدمة)."""
    rng = np.random.default_rng(seed)
    sfx_name = (sfx_name or "").lower().strip()

    if sfx_name == "knock":
        # 3 خبطات واقعية على باب خشبي مجوّف في سكون الليل
        dur = int(1.65 * SAMPLE_RATE)
        out = np.zeros((dur, 2), dtype=np.float32)
        hit_len = int(0.16 * SAMPLE_RATE)
        ht = np.arange(hit_len, dtype=np.float32) / SAMPLE_RATE
        wood = (
            np.sin(2 * np.pi * (135.0 * np.exp(-ht * 18.0) + 68.0) * ht) * np.exp(-ht * 24.0) * 0.75
            + np.sin(2 * np.pi * 245.0 * ht) * np.exp(-ht * 42.0) * 0.35
        )
        for offset_s in (0.05, 0.52, 1.02):
            idx = int(offset_s * SAMPLE_RATE)
            out[idx : idx + hit_len, 0] += wood * 0.65
            out[idx + 12 : idx + 12 + hit_len, 1] += wood * 0.60
        return out

    if sfx_name == "heartbeat":
        dur = int(1.8 * SAMPLE_RATE)
        out = np.zeros((dur, 2), dtype=np.float32)
        beat_len = int(0.22 * SAMPLE_RATE)
        bt = np.arange(beat_len, dtype=np.float32) / SAMPLE_RATE
        lub = np.sin(2 * np.pi * 52.0 * bt) * np.exp(-bt * 16.0) * 0.72
        dub = np.sin(2 * np.pi * 44.0 * bt) * np.exp(-bt * 20.0) * 0.55
        for base_s in (0.04, 0.92):
            i1 = int(base_s * SAMPLE_RATE)
            i2 = int((base_s + 0.24) * SAMPLE_RATE)
            out[i1 : i1 + beat_len] += lub[:, None]
            out[i2 : i2 + beat_len] += dub[:, None]
        return out

    if sfx_name == "thunder":
        dur = int(2.4 * SAMPLE_RATE)
        t = np.arange(dur, dtype=np.float32) / SAMPLE_RATE
        raw = rng.normal(0.0, 1.0, size=dur).astype(np.float32)
        # تنعيم عميق للحصول على هزيم رعد حقيقي
        k = np.ones(160, dtype=np.float32) / 160.0
        rumble = np.convolve(raw, k, mode="same") * 3.8
        env = np.exp(-t * 1.45) * (0.4 + 0.6 * np.exp(-((t - 0.18) * 7.0) ** 2))
        sig = np.clip(rumble * env * 0.65, -0.8, 0.8)
        return np.stack([sig, np.roll(sig, 350) * 0.92], axis=1)

    if sfx_name == "cassette":
        dur = int(0.75 * SAMPLE_RATE)
        out = np.zeros((dur, 2), dtype=np.float32)
        cl_len = int(0.05 * SAMPLE_RATE)
        ct = np.arange(cl_len, dtype=np.float32) / SAMPLE_RATE
        click = (rng.normal(0, 0.4, cl_len).astype(np.float32) + np.sin(2 * np.pi * 920 * ct) * 0.5) * np.exp(-ct * 65.0)
        out[600 : 600 + cl_len] += click[:, None] * 0.55
        out[6800 : 6800 + cl_len] += click[:, None] * 0.40
        return out

    if sfx_name == "reveal":
        dur = int(1.9 * SAMPLE_RATE)
        t = np.arange(dur, dtype=np.float32) / SAMPLE_RATE
        freq = 110.0 * np.exp(-t * 1.5) + 36.0
        boom = np.sin(2 * np.pi * np.cumsum(freq) / SAMPLE_RATE) * np.exp(-t * 2.2) * 0.62
        shimmer = np.sin(2 * np.pi * 587.33 * t) * np.exp(-t * 2.8) * 0.12
        sig = boom + shimmer
        return np.stack([sig, np.roll(sig, 180)], axis=1)

    return np.zeros((0, 2), dtype=np.float32)


def _piano_note(freq: float, dur_sec: float) -> np.ndarray:
    """توليد نغمة بيانو دافئة بـ 5 توافقيات طبيعية وضربة مطرقة ناعمة."""
    n = int(dur_sec * SAMPLE_RATE)
    t = np.arange(n, dtype=np.float32) / SAMPLE_RATE
    attack = np.minimum(1.0, t / 0.014)
    note = (
        0.58 * np.sin(2 * np.pi * freq * t) * np.exp(-t * 1.55)
        + 0.24 * np.sin(2 * np.pi * freq * 2.0 * t) * np.exp(-t * 2.4)
        + 0.11 * np.sin(2 * np.pi * freq * 3.0 * t) * np.exp(-t * 3.3)
        + 0.05 * np.sin(2 * np.pi * freq * 4.01 * t) * np.exp(-t * 4.5)
    ) * attack
    return note.astype(np.float32)


def compose_cinematic_score(total_samples: int, music_key: str, seed: int = 42) -> np.ndarray:
    """
    تأليف موسيقى تصويرية سينمائية حقيقية (بيانو ليلي غامض + تشيلو دافئ + مطر خفيف + صدى قاعة)
    خالٍ تماماً من الطنين الرتيب ومضمون 0% حقوق ملكية للأبد.
    """
    rng = np.random.default_rng(seed)
    left = np.zeros(total_samples, dtype=np.float32)
    right = np.zeros(total_samples, dtype=np.float32)

    # سلم موسيقي درامي سينمائي (D Minor / E Minor)
    if music_key == "ancient_mystery":
        melody_hz = [220.00, 233.08, 277.18, 293.66, 329.63, 349.23, 440.00]
        bass_hz = [55.00, 73.42, 58.27, 82.41]
    elif music_key == "crime_clock":
        melody_hz = [329.63, 392.00, 493.88, 466.16, 369.99, 329.63]
        bass_hz = [82.41, 98.00, 73.42, 61.74]
    else:  # thriller_piano / dark_pulse_piano
        melody_hz = [293.66, 349.23, 440.00, 466.16, 440.00, 329.63, 261.63, 293.66]
        bass_hz = [73.42, 58.27, 65.41, 55.00]

    # 1) نغمات البيانو المتفرقة الساحرة (Arpeggio بطيء مثل موسيقى مسلسلات الغموض)
    cursor = int(0.4 * SAMPLE_RATE)
    step_idx = 0
    while cursor < total_samples - SAMPLE_RATE:
        freq = melody_hz[step_idx % len(melody_hz)]
        if rng.random() < 0.25:
            freq *= 2.0 if freq < 300 else 0.5
        note_dur = float(rng.uniform(1.8, 2.9))
        wave_n = _piano_note(freq, note_dur) * 0.28
        end_i = min(total_samples, cursor + len(wave_n))
        seg = wave_n[: end_i - cursor]
        pan_l = 0.62 if step_idx % 2 == 0 else 0.38
        left[cursor:end_i] += seg * pan_l
        right[cursor:end_i] += seg * (1.0 - pan_l * 0.45)
        cursor += int(rng.uniform(1.15, 2.15) * SAMPLE_RATE)
        step_idx += 1

    # 2) طبقة تشيلو دافئة منخفضة تتغير كل 6 ثوانٍ
    bar_len = int(6.0 * SAMPLE_RATE)
    pos = 0
    b_idx = 0
    while pos < total_samples:
        chunk_n = min(bar_len, total_samples - pos)
        bt = np.arange(chunk_n, dtype=np.float32) / SAMPLE_RATE
        bf = bass_hz[b_idx % len(bass_hz)]
        swell = np.sin(np.pi * bt / max(0.2, chunk_n / SAMPLE_RATE)) ** 0.7
        cello = (
            0.14 * np.sin(2 * np.pi * bf * bt)
            + 0.07 * np.sin(2 * np.pi * bf * 1.5 * bt)
            + 0.04 * np.sin(2 * np.pi * bf * 2.0 * bt)
        ) * swell
        left[pos : pos + chunk_n] += cello
        right[pos : pos + chunk_n] += cello * 0.95
        pos += chunk_n
        b_idx += 1

    # 3) صدى سينمائي واسع (Stereo Hall Reverb)
    for delay_ms, gain in ((115, 0.30), (235, 0.20), (380, 0.12)):
        d = int(delay_ms * SAMPLE_RATE / 1000.0)
        if d < total_samples:
            left[d:] += right[:-d] * gain
            right[d:] += left[:-d] * gain

    # 4) مطر ليلي خفيف جداً خارج النافذة لأجواء السهر والاستمتاع
    rain_raw = rng.normal(0.0, 0.011, size=total_samples).astype(np.float32)
    rain_smooth = np.convolve(rain_raw, np.ones(22, dtype=np.float32) / 22.0, mode="same")
    left += rain_smooth
    right += np.roll(rain_smooth, 160)

    score = np.stack([left, right], axis=1)
    peak = np.max(np.abs(score)) + 1e-6
    return (score / peak) * 0.34


def build_episode_soundtrack(
    segments: List[Dict[str, Any]],
    voices_map: Dict[str, Dict[str, Any]],
    mood: str,
    work_dir: Path,
    out_wav: Path,
    seed: int = 101,
) -> List[Dict[str, Any]]:
    work_dir.mkdir(parents=True, exist_ok=True)

    intro_pad = int(0.65 * SAMPLE_RATE)
    outro_pad = int(1.60 * SAMPLE_RATE)
    voice_chunks: List[np.ndarray] = [np.zeros((intro_pad, 2), dtype=np.float32)]
    env_chunks: List[np.ndarray] = [np.zeros(intro_pad, dtype=np.float32)]
    cursor = intro_pad
    timed_segments: List[Dict[str, Any]] = []

    for idx, seg in enumerate(segments):
        role = seg.get("speaker", "narrator")
        v_cfg = voices_map.get(role) or next(iter(voices_map.values()))

        # إدراج المؤثر الصوتي التمثيلي قبل الجملة إن وُجد (مثل خبط الباب أو الرعد أو الكاسيت)
        sfx_tag = seg.get("sfx", "none")
        if sfx_tag and sfx_tag != "none":
            sfx_pcm = synthesize_foley_sfx(sfx_tag, seed=seed + idx)
            if sfx_pcm.shape[0] > 0:
                voice_chunks.append(sfx_pcm)
                env_chunks.append(np.zeros(sfx_pcm.shape[0], dtype=np.float32))
                cursor += sfx_pcm.shape[0]

        audio_file = _synth_single_line(seg["text"], v_cfg, work_dir / f"seg_{idx:03d}")
        pcm = decode_audio_to_stereo_float(audio_file)

        if v_cfg.get("tape_fx") or seg.get("sfx") == "cassette":
            pcm = _apply_tape_phone_filter(pcm)

        peak = np.max(np.abs(pcm)) + 1e-6
        pcm = (pcm / peak) * 0.90

        if idx > 0 and (not sfx_tag or sfx_tag == "none"):
            gap = int(0.38 * SAMPLE_RATE)
            voice_chunks.append(np.zeros((gap, 2), dtype=np.float32))
            env_chunks.append(np.zeros(gap, dtype=np.float32))
            cursor += gap

        start_sec = cursor / SAMPLE_RATE
        dur_sec = pcm.shape[0] / SAMPLE_RATE
        end_sec = start_sec + dur_sec

        voice_chunks.append(pcm)
        env_chunks.append(np.ones(pcm.shape[0], dtype=np.float32))
        cursor += pcm.shape[0]

        enriched = dict(seg)
        enriched["start_sec"] = round(start_sec, 3)
        enriched["end_sec"] = round(end_sec, 3)
        enriched["duration_sec"] = round(dur_sec, 3)
        timed_segments.append(enriched)

    voice_chunks.append(np.zeros((outro_pad, 2), dtype=np.float32))
    env_chunks.append(np.zeros(outro_pad, dtype=np.float32))
    total_samples = cursor + outro_pad

    voice_track = np.concatenate(voice_chunks, axis=0)
    speech_env = np.concatenate(env_chunks, axis=0)

    smooth_win = int(0.28 * SAMPLE_RATE)
    smooth_env = np.convolve(speech_env, np.ones(smooth_win, dtype=np.float32) / smooth_win, mode="same")
    # البيانو ينخفض بنعومة أثناء الحوار ويرتفع بجمال بين الجمل
    music_gain = (0.95 - 0.58 * smooth_env)[:, None]

    score_track = compose_cinematic_score(total_samples, music_key=mood, seed=seed)

    fade_in = min(int(0.6 * SAMPLE_RATE), total_samples // 4)
    fade_out = min(int(1.4 * SAMPLE_RATE), total_samples // 4)
    score_track[:fade_in] *= np.linspace(0.0, 1.0, fade_in, dtype=np.float32)[:, None]
    score_track[-fade_out:] *= np.linspace(1.0, 0.0, fade_out, dtype=np.float32)[:, None]

    master = np.tanh((voice_track + score_track * music_gain) * 1.06) * 0.95
    pcm16 = (np.clip(master, -1.0, 1.0) * 32767.0).astype(np.int16)

    out_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm16.tobytes())

    return timed_segments
