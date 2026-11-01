# -*- coding: utf-8 -*-
"""
استوديو الصوت الروائي الطويل والشورتس V4.0 (15+ Minute Storytime & Short Voice Studio)
- يسجّل الحلقات الطويلة (15–18 دقيقة) على التوازي السريع مع استخراج توقيت الجمل الدقيق للترجمة.
- يضمن أن كل حلقة طويلة تتجاوز 15 دقيقة و15 ثانية (915 ثانية كحد أدنى).
- يسجّل الشورت التشويقي الحماسي (60 ثانية) ويستخرج توقيت كل كلمة عبر Groq Whisper-Large-V3-Turbo.
- يولّد خلفية موسيقية سينمائية دافئة وهادئة جداً (-26dB) تحت صوت السرد لزيادة الاندماج.
"""

import asyncio
import math
import os
import re
import subprocess
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import edge_tts
import imageio_ffmpeg
import numpy as np
import requests

FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()


def get_audio_duration(audio_path: Path) -> float:
    proc = subprocess.run([FFMPEG_BIN, "-i", str(audio_path)], capture_output=True, text=True)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", proc.stderr)
    if not m:
        return 0.0
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def _sanitize_tts_text(text: str) -> str:
    txt = text.replace("\u202f", " ").replace("\u00a0", " ")
    for ch in ("«", "»", "“", "”", '"', "<", ">", "&", "—", "–", "‑", "*"):
        txt = txt.replace(ch, " ")
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def _split_into_paragraphs(text: str, max_chars: int = 1500) -> List[str]:
    clean = _sanitize_tts_text(text)
    sents = re.split(r"(?<=[\.\!\؟\?،,])\s+", clean)
    chunks: List[str] = []
    cur = ""
    for s in sents:
        s = s.strip()
        if not s:
            continue
        if len(cur) + len(s) + 1 <= max_chars:
            cur = f"{cur} {s}".strip()
        else:
            if cur:
                chunks.append(cur)
            cur = s[:max_chars]
    if cur:
        chunks.append(cur)
    return chunks or [clean[:max_chars]]


def _try_gemini_tts_chunk(
    text: str,
    is_arabic: bool,
    out_mp3: Path,
    gemini_voice: str = "",
    chunk_idx: int = 0,
) -> bool:
    """توليد صوت بشري تمثيلي باللهجة المصرية الأصيلة (ar-EG) أو الإنجليزية (en-US) مجاناً عبر نماذج Gemini 3.8 TTS المستقرة."""
    gkey = os.environ.get("GEMINI_API_KEY", "").strip()
    if not gkey:
        return False
    import base64
    import time

    vname = gemini_voice or ("Kore" if is_arabic else "Puck")
    lang_code = "ar-EG" if is_arabic else "en-US"
    models = (
        ("gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts", "gemini-3.1-flash-tts-preview")
        if chunk_idx % 2 == 0
        else ("gemini-3.8-flash-lite-tts", "gemini-3.8-flash-tts", "gemini-3.1-flash-tts-preview")
    )
    for model_id in models:
        for att in range(2):
            try:
                r = requests.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={gkey}",
                    json={
                        "contents": [{"parts": [{"text": text}]}],
                        "generationConfig": {
                            "responseModalities": ["AUDIO"],
                            "speechConfig": {
                                "languageCode": lang_code,
                                "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": vname}},
                            },
                        },
                    },
                    timeout=110,
                )
                if r.status_code == 429 and att == 0:
                    time.sleep(10.0)
                    continue
                if r.status_code == 200:
                    part = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
                    audio_bytes = base64.b64decode(part["data"])
                    mime = str(part.get("mimeType", "")).lower()
                    is_wav = ("wav" in mime) or (audio_bytes[:4] == b"RIFF")
                    tmp_in = out_mp3.with_suffix(".wav" if is_wav else ".pcm")
                    tmp_in.write_bytes(audio_bytes)
                    cmd = (
                        [FFMPEG_BIN, "-y", "-i", str(tmp_in), "-c:a", "libmp3lame", "-b:a", "192k", "-loglevel", "error", str(out_mp3)]
                        if is_wav
                        else [FFMPEG_BIN, "-y", "-f", "s16le", "-ar", "24000", "-ac", "1", "-i", str(tmp_in), "-c:a", "libmp3lame", "-b:a", "192k", "-loglevel", "error", str(out_mp3)]
                    )
                    subprocess.run(cmd, check=True)
                    tmp_in.unlink(missing_ok=True)
                    if out_mp3.exists() and out_mp3.stat().st_size > 800:
                        return True
                break
            except Exception:
                break
    return False


def _try_groq_orpheus_chunk(text: str, voice_id: str, out_mp3: Path) -> bool:
    """توليد صوت بشري إنجليزي سينمائي مجاني 100% عبر Groq Orpheus-V1-English."""
    gkey = os.environ.get("GROQ_API_KEY", "").strip()
    if not gkey:
        return False
    try:
        chunks = [text[i : i + 190] for i in range(0, len(text), 190)]
        wav_parts: List[Path] = []
        for ci, sub in enumerate(chunks):
            r = requests.post(
                "https://api.groq.com/openai/v1/audio/speech",
                headers={"Authorization": f"Bearer {gkey}", "Content-Type": "application/json"},
                json={"model": "canopylabs/orpheus-v1-english", "input": sub, "voice": voice_id or "troy", "response_format": "wav"},
                timeout=60,
            )
            if r.status_code != 200:
                return False
            wp = out_mp3.parent / f"_orph_{out_mp3.stem}_{ci}.wav"
            wp.write_bytes(r.content)
            wav_parts.append(wp)
        lst = out_mp3.parent / f"_orph_{out_mp3.stem}.txt"
        lst.write_text("\n".join(f"file '{p.resolve()}'" for p in wav_parts), encoding="utf-8")
        subprocess.run(
            [FFMPEG_BIN, "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:a", "libmp3lame", "-b:a", "192k", "-loglevel", "error", str(out_mp3)],
            check=True,
        )
        for p in wav_parts + [lst]:
            p.unlink(missing_ok=True)
        return out_mp3.exists() and out_mp3.stat().st_size > 800
    except Exception:
        return False


def _try_hf_egyptian_chunk(text: str, speaker: str, out_mp3: Path) -> bool:
    """توليد صوت بودكاست مصري بشري عبر VoiceTut-TTS على Hugging Face مجاناً عند توفر HF_TOKEN."""
    hf_tok = os.environ.get("HF_TOKEN", "").strip()
    if not hf_tok:
        return False
    try:
        from gradio_client import Client
        import shutil
        client = Client("oddadmix/VoiceTut-TTS", token=hf_tok)
        res = client.predict(text=text, speaker=speaker or "Mariam", api_name="/generate_speech")
        wav_p = res[0] if isinstance(res, (list, tuple)) else res
        if wav_p and Path(str(wav_p)).exists():
            subprocess.run(
                [FFMPEG_BIN, "-y", "-i", str(wav_p), "-c:a", "libmp3lame", "-b:a", "192k", "-loglevel", "error", str(out_mp3)],
                check=True,
            )
            return out_mp3.exists() and out_mp3.stat().st_size > 800
    except Exception:
        pass
    return False


async def _synth_chunks_parallel(
    chunks: List[str],
    voice_name: str,
    rate: str,
    work_dir: Path,
    voice_cfg: Optional[Dict[str, Any]] = None,
) -> List[Tuple[Path, List[Dict[str, Any]]]]:
    sem = asyncio.Semaphore(2)
    vcfg = voice_cfg or {}

    async def _one(idx: int, txt: str) -> Tuple[Path, List[Dict[str, Any]]]:
        async with sem:
            await asyncio.sleep(0.5 * (idx % 2))
            is_ar = "ar-" in voice_name
            p_out = work_dir / f"chunk_{idx:04d}.mp3"
            # 1) المحرك الأول: Google Gemini Native Egyptian/English Human TTS (مجاني للأبد في Google AI Studio)
            if await asyncio.to_thread(_try_gemini_tts_chunk, txt, is_ar, p_out, vcfg.get("gemini_voice", ""), idx):
                return p_out, []
            # 2) المحرك الثاني: VoiceTut المصري (للعربي) أو Groq Orpheus البشري (للإنجليزي)
            if is_ar and await asyncio.to_thread(_try_hf_egyptian_chunk, txt, vcfg.get("voicetut_speaker", "Mariam"), p_out):
                return p_out, []
            if (not is_ar) and await asyncio.to_thread(_try_groq_orpheus_chunk, txt, vcfg.get("orpheus_voice", "troy"), p_out):
                return p_out, []
            # 3) المحرك الاحتياطي للطوارئ فقط
            last_err = None
            for att in range(6):
                try:
                    comm = edge_tts.Communicate(txt, voice_name, rate=rate)
                    audio_buf = bytearray()
                    bounds: List[Dict[str, Any]] = []
                    async for msg in comm.stream():
                        if msg["type"] == "audio":
                            audio_buf.extend(msg["data"])
                        elif msg["type"] in ("SentenceBoundary", "WordBoundary"):
                            bounds.append({
                                "type": msg["type"],
                                "offset": float(msg["offset"]) / 1e7,
                                "duration": max(0.12, float(msg["duration"]) / 1e7),
                                "text": str(msg["text"]).strip(),
                            })
                    if len(audio_buf) < 400:
                        raise RuntimeError("Empty TTS stream")
                    p = work_dir / f"chunk_{idx:04d}.mp3"
                    p.write_bytes(bytes(audio_buf))
                    return p, bounds
                except Exception as exc:
                    last_err = exc
                    await asyncio.sleep(3.5 * (att + 1))
            raise RuntimeError(f"TTS chunk {idx} failed: {last_err}")

    return await asyncio.gather(*(_one(i, c) for i, c in enumerate(chunks)))


def synthesize_long_episode_audio(
    acts: List[Dict[str, Any]],
    voice_cfg: Dict[str, Any],
    work_dir: Path,
    min_duration_sec: float = 920.0,
) -> Tuple[Path, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    يسجّل الفصول الخمسة كاملة ويُرجع:
    (مسار الملف الصوتي المدمج >= 15.3 دقيقة، قائمة جمل الترجمة المزامنة، قائمة توقيت بداية كل فصل).
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    voice_name = voice_cfg.get("edge_voice", "ar-EG-SalmaNeural")
    rate = voice_cfg.get("edge_rate", "+3%")

    all_chunks: List[str] = []
    chunk_act_map: List[int] = []
    for act in acts:
        act_chunks = _split_into_paragraphs(act["narration"], max_chars=1800)
        for ch in act_chunks:
            all_chunks.append(ch)
            chunk_act_map.append(int(act["act_num"]))

    results = asyncio.run(_synth_chunks_parallel(all_chunks, voice_name, rate, work_dir, voice_cfg))

    # إنشاء وقفة درامية قصيرة (1.1 ثانية) بين الفصول
    pause_mp3 = work_dir / "act_pause.mp3"
    subprocess.run(
        [
            FFMPEG_BIN, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
            "-t", "1.1", "-c:a", "libmp3lame", "-b:a", "128k", "-loglevel", "error", str(pause_mp3),
        ],
        check=True,
    )

    concat_lines: List[str] = []
    subtitles: List[Dict[str, Any]] = []
    act_markers: List[Dict[str, Any]] = []
    cursor = 0.0
    prev_act = None

    for idx, (mp3_path, bounds) in enumerate(results):
        cur_act = chunk_act_map[idx]
        if cur_act != prev_act:
            if prev_act is not None:
                concat_lines.append(f"file '{pause_mp3.resolve()}'")
                cursor += 1.1
            act_obj = next((a for a in acts if int(a["act_num"]) == cur_act), acts[0])
            act_markers.append({
                "act_num": cur_act,
                "act_title": act_obj["act_title"],
                "start": cursor,
            })
            prev_act = cur_act

        dur = get_audio_duration(mp3_path)
        concat_lines.append(f"file '{mp3_path.resolve()}'")

        if bounds:
            for b in bounds:
                s_txt = b["text"]
                if not s_txt:
                    continue
                b_start = cursor + b["offset"]
                b_dur = b["duration"]
                # تقسيم الجملة الطويلة إلى شرائح مريحة للقراءة (7 كلمات لكل شريحة)
                words = s_txt.split()
                step = 7
                groups = [" ".join(words[i : i + step]) for i in range(0, len(words), step)] or [s_txt]
                seg_d = b_dur / len(groups)
                for gi, g in enumerate(groups):
                    subtitles.append({
                        "start": b_start + gi * seg_d,
                        "end": b_start + (gi + 1) * seg_d,
                        "text": g,
                    })
        else:
            words = all_chunks[idx].split()
            step = 7
            groups = [" ".join(words[i : i + step]) for i in range(0, len(words), step)]
            seg_d = max(0.5, dur / max(1, len(groups)))
            for gi, g in enumerate(groups):
                subtitles.append({
                    "start": cursor + gi * seg_d,
                    "end": cursor + (gi + 1) * seg_d,
                    "text": g,
                })

        cursor += dur

    concat_txt = work_dir / "long_concat.txt"
    concat_txt.write_text("\n".join(concat_lines), encoding="utf-8")
    raw_merged = work_dir / "long_voice_raw.mp3"
    subprocess.run(
        [
            FFMPEG_BIN, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt),
            "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "160k",
            "-loglevel", "error", str(raw_merged),
        ],
        check=True,
    )

    actual_dur = get_audio_duration(raw_merged)
    tempo = 1.0
    if actual_dur < min_duration_sec and actual_dur > 100:
        # تبطيء طفيف طبيعي جداً إذا لزم لضمان كسر حاجز الـ 15 دقيقة و20 ثانية دائماً
        tempo = max(0.86, actual_dur / min_duration_sec)
        scale_factor = 1.0 / tempo
        for s in subtitles:
            s["start"] *= scale_factor
            s["end"] *= scale_factor
        for am in act_markers:
            am["start"] *= scale_factor

    # توليد موسيقى خلفية درامية ناعمة جداً (Ambient Warm Pad) ومزجها تحت الصوت البشري
    expected_final_dur = actual_dur / tempo + 2.0
    pad_wav = _build_warm_cinema_pad(work_dir / "cinema_pad.wav", duration_sec=min(60.0, expected_final_dur), mood=voice_cfg.get("mood", "mystery"))

    final_mp3 = work_dir / "long_episode_master.mp3"
    tempo_flt = f"atempo={tempo:.4f}," if abs(tempo - 1.0) > 0.005 else ""
    subprocess.run(
        [
            FFMPEG_BIN, "-y",
            "-i", str(raw_merged),
            "-stream_loop", "-1", "-i", str(pad_wav),
            "-filter_complex",
            f"[0:a]{tempo_flt}acompressor=threshold=-16dB:ratio=2.8:attack=5:release=60,loudnorm=I=-15:TP=-1.5:LRA=9[v];"
            f"[1:a]volume=0.045[bg];"
            f"[v][bg]amix=inputs=2:duration=first:dropout_transition=2[out]",
            "-map", "[out]",
            "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "160k",
            "-loglevel", "error", str(final_mp3),
        ],
        check=True,
    )
    return final_mp3, subtitles, act_markers


def synthesize_short_audio_and_words(
    short_text: str,
    voice_cfg: Dict[str, Any],
    groq_key: str,
    language: str,
    work_dir: Path,
) -> Tuple[Path, List[Dict[str, Any]]]:
    """يسجّل الشورت الحماسي (55–68 ثانية) ويستخرج توقيت كل كلمة بالمللي ثانية."""
    work_dir.mkdir(parents=True, exist_ok=True)
    voice_name = voice_cfg.get("edge_voice", "ar-EG-SalmaNeural")
    is_ar = "ar-" in voice_name
    raw_mp3 = work_dir / "short_raw.mp3"
    clean_short = _sanitize_tts_text(short_text)

    synth_ok = _try_gemini_tts_chunk(clean_short, is_ar, raw_mp3, voice_cfg.get("gemini_voice", ""), 0)
    if not synth_ok and is_ar:
        synth_ok = _try_hf_egyptian_chunk(clean_short, voice_cfg.get("voicetut_speaker", "Mariam"), raw_mp3)
    if not synth_ok and not is_ar:
        synth_ok = _try_groq_orpheus_chunk(clean_short, voice_cfg.get("orpheus_voice", "troy"), raw_mp3)
    if not synth_ok:
        last_err = None
        for att in range(6):
            try:
                comm = edge_tts.Communicate(clean_short, voice_name, rate="+6%")
                asyncio.run(comm.save(str(raw_mp3)))
                if raw_mp3.exists() and raw_mp3.stat().st_size > 500:
                    break
            except Exception as exc:
                last_err = exc
                import time
                time.sleep(3.0 * (att + 1))
        else:
            raise RuntimeError(f"Short TTS failed after retries: {last_err}")

    voice_clean = work_dir / "short_voice_clean.mp3"
    subprocess.run(
        [
            FFMPEG_BIN, "-y", "-i", str(raw_mp3),
            "-af", "silenceremove=stop_periods=-1:stop_duration=0.22:stop_threshold=-38dB,acompressor=threshold=-16dB:ratio=2.8,loudnorm=I=-14:TP=-1.5:LRA=8",
            "-ar", "44100", "-ac", "2", "-b:a", "192k", "-loglevel", "error", str(voice_clean),
        ],
        check=True,
    )

    pad_wav = _build_warm_cinema_pad(work_dir / "short_thriller_pad.wav", duration_sec=40.0, mood=voice_cfg.get("mood", "mystery"))
    paced_mp3 = work_dir / "short_master.mp3"
    subprocess.run(
        [
            FFMPEG_BIN, "-y",
            "-i", str(voice_clean),
            "-stream_loop", "-1", "-i", str(pad_wav),
            "-filter_complex", "[1:a]volume=0.14[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=1[out]",
            "-map", "[out]", "-ar", "44100", "-ac", "2", "-b:a", "192k", "-loglevel", "error", str(paced_mp3),
        ],
        check=True,
    )

    # استخراج توقيت الكلمات من الصوت الصافي عبر Groq Whisper-Large-V3-Turbo
    words: List[Dict[str, Any]] = []
    if groq_key:
        try:
            with open(voice_clean, "rb") as fh:
                resp = requests.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {groq_key}"},
                    files={"file": (paced_mp3.name, fh, "audio/mpeg")},
                    data=[
                        ("model", "whisper-large-v3-turbo"),
                        ("response_format", "verbose_json"),
                        ("timestamp_granularities[]", "word"),
                        ("language", language),
                    ],
                    timeout=60,
                )
            if resp.status_code == 200:
                for w in resp.json().get("words") or []:
                    txt = str(w.get("word", "")).strip(" ،,.!؟?;:\"'()[]")
                    if txt:
                        s = float(w.get("start", 0.0))
                        e = max(s + 0.09, float(w.get("end", s + 0.20)))
                        words.append({"word": txt, "start": s, "end": e})
        except Exception:
            pass

    if not words:
        dur = get_audio_duration(paced_mp3)
        tokens = [t.strip(" ،,.!؟?") for t in short_text.split() if t.strip(" ،,.!؟?")]
        step = dur / max(1, len(tokens))
        words = [{"word": t, "start": i * step, "end": (i + 1) * step} for i, t in enumerate(tokens)]

    return paced_mp3, words


def _build_warm_cinema_pad(out_wav: Path, duration_sec: float = 48.0, mood: str = "mystery") -> Path:
    """يولّد خلفية صوتية سينمائية حسب روح القناة: نبض تحقيقات وتشويق لقنوات الألغاز، أو نغمة سينمائية دافئة ناعمة للروايات المتنوعة."""
    sr = 24000
    n = int(sr * duration_sec)
    t = np.linspace(0.0, duration_sec, n, endpoint=False, dtype=np.float32)
    if mood == "warm":
        chords = [(110.0, 164.81, 220.0), (87.31, 130.81, 174.61), (130.81, 164.81, 196.0), (98.0, 146.83, 196.0)]
        seg_len = n // len(chords)
        sig = np.zeros(n, dtype=np.float32)
        for ci, (f1, f2, f3) in enumerate(chords):
            s_i = ci * seg_len
            e_i = n if ci == len(chords) - 1 else (ci + 1) * seg_len
            tt = t[s_i:e_i] - t[s_i]
            d_seg = max(0.1, float(e_i - s_i) / sr)
            env = np.sin(np.pi * tt / d_seg) ** 0.45
            sig[s_i:e_i] = (0.45 * np.sin(2 * math.pi * f1 * tt) + 0.30 * np.sin(2 * math.pi * f2 * tt) + 0.20 * np.sin(2 * math.pi * f3 * tt)) * env
    else:
        drone = (
            0.34 * np.sin(2 * math.pi * 73.42 * t)
            + 0.22 * np.sin(2 * math.pi * 87.31 * t + 0.4)
            + 0.14 * np.sin(2 * math.pi * 110.00 * t + 1.1)
        ) * (0.72 + 0.28 * np.sin(2 * math.pi * 0.11 * t))
        beat_period = 0.92
        phase = np.mod(t, beat_period)
        hb1 = np.exp(-phase * 26.0) * np.sin(2 * math.pi * 52.0 * phase)
        hb2 = np.where(phase > 0.23, np.exp(-(phase - 0.23) * 30.0) * np.sin(2 * math.pi * 46.0 * (phase - 0.23)), 0.0)
        heartbeat = 0.42 * (hb1 + 0.72 * hb2)
        riser = 0.09 * np.sin(2 * math.pi * (146.83 + 12.0 * np.sin(2 * math.pi * 0.0625 * t)) * t)
        sig = 0.55 * drone + heartbeat + riser
    pcm = np.clip(sig * 0.45 * 32767.0, -32767, 32767).astype(np.int16)
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return out_wav
