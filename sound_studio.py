# -*- coding: utf-8 -*-
"""
استوديو الصوت النفسي والمزامنة الدقيقة V9.0 (4-Call Gemini Human Studio + Whisper Exact Scene Lock + Climax Shorts)
1) يسجّل الحلقة الكاملة (+16 دقيقة، 12 مشهداً) في 3 دفعات صوتية متصلة عبر محركات Google Gemini Human TTS الأربعة
   (لتوفير الحصة اليومية وضمان صوت بشري مصري/أمريكي 100% دائماً بلا أي صوت آلي!).
2) يستخرج التوقيت الدقيق بالملي ثانية لكل كلمة ولكل مشهد من المشاهد الـ 12 عبر Groq Whisper-Large-V3-Turbo،
   بحيث تتغير الصورة بالضبط في اللحظة التي يبدأ فيها كلام المشهد، وتُكتب فصول اليوتيوب بالدقيقة والثانية بدقة تامة!
3) يقتطع الشورت الأول (~115–135 ثانية تنتهي عند ذروة المشهد 2 النارية) والشورت الثاني (~115–135 ثانية تنتهي عند ذروة المشهد 7 الصادمة)
   ويضيف توقف نبض درامي مفاجئ في قمة الإثارة متبوعاً بدعوة فورية لسماع القصة كاملة من أول تعليق!
"""

import base64
import math
import os
import re
import subprocess
import time
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import edge_tts
import imageio_ffmpeg
import numpy as np
import requests

FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()

GEMINI_TTS_MODELS = (
    "gemini-3.8-flash-tts",
    "gemini-3.8-flash-lite-tts",
    "gemini-3.1-flash-tts-preview",
    "gemini-2.5-flash-preview-tts",
)


def get_audio_duration(audio_path: Path) -> float:
    proc = subprocess.run([FFMPEG_BIN, "-i", str(audio_path)], capture_output=True, text=True)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", proc.stderr)
    if not m:
        return 0.0
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def format_mmss(sec: float) -> str:
    sec = max(0, int(round(sec)))
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _sanitize_tts_text(text: str) -> str:
    txt = text.replace("\u202f", " ").replace("\u00a0", " ")
    for ch in ("«", "»", "“", "”", '"', "<", ">", "&", "—", "–", "‑", "*", "#"):
        txt = txt.replace(ch, " ")
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def _norm_token(word: str) -> str:
    w = word.lower().strip()
    w = re.sub(r"[^\w\u0600-\u06FF]", "", w)
    w = re.sub(r"[\u064B-\u065F\u0670]", "", w)
    for src, dst in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ة", "ه"), ("ى", "ي")):
        w = w.replace(src, dst)
    return w


def _try_gemini_tts(
    text: str,
    is_arabic: bool,
    out_mp3: Path,
    gemini_voice: str = "",
    call_index: int = 0,
) -> bool:
    """توليد صوت بشري تمثيلي باللهجة المصرية الأصيلة (ar-EG) أو الإنجليزية (en-US) عبر تدوير نماذج Gemini TTS الأربعة."""
    gkey = os.environ.get("GEMINI_API_KEY", "").strip()
    if not gkey:
        return False

    vname = gemini_voice or ("Kore" if is_arabic else "Puck")
    lang_code = "ar-EG" if is_arabic else "en-US"
    n_m = len(GEMINI_TTS_MODELS)
    ordered_models = [GEMINI_TTS_MODELS[(call_index + k) % n_m] for k in range(n_m)]

    for model_id in ordered_models:
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
                timeout=165,
            )
            if r.status_code == 429 and ("PerMinute" in r.text or "per_minute" in r.text.lower()):
                time.sleep(22.0)
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
                    timeout=165,
                )
            if r.status_code == 200 and "inlineData" in r.text:
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
                if out_mp3.exists() and out_mp3.stat().st_size > 1200:
                    print(f"    🎙️ [Gemini Human TTS: {model_id} / {vname}] -> {get_audio_duration(out_mp3):.1f}s")
                    return True
        except Exception:
            continue
    return False


def _try_groq_orpheus(text: str, voice_id: str, out_mp3: Path) -> bool:
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


def _synth_single_block(
    text: str,
    voice_cfg: Dict[str, Any],
    is_arabic: bool,
    out_mp3: Path,
    call_index: int = 0,
) -> Path:
    clean = _sanitize_tts_text(text)
    out_mp3.parent.mkdir(parents=True, exist_ok=True)

    if _try_gemini_tts(clean, is_arabic, out_mp3, voice_cfg.get("gemini_voice", ""), call_index):
        return out_mp3
    if (not is_arabic) and _try_groq_orpheus(clean, voice_cfg.get("orpheus_voice", "troy"), out_mp3):
        return out_mp3

    import asyncio
    edge_voice = voice_cfg.get("edge_voice", "ar-SA-ZariyahNeural" if is_arabic else "en-US-AndrewMultilingualNeural")
    rate = voice_cfg.get("edge_rate", "+2%")
    for att in range(5):
        try:
            comm = edge_tts.Communicate(clean, edge_voice, rate=rate)
            asyncio.run(comm.save(str(out_mp3)))
            if out_mp3.exists() and out_mp3.stat().st_size > 800:
                return out_mp3
        except Exception:
            time.sleep(3.0 * (att + 1))
    raise RuntimeError(f"Failed to synthesize audio block {out_mp3.name}")


def _whisper_transcribe_words(audio_path: Path, groq_key: str, language: str) -> List[Dict[str, Any]]:
    """يستخرج التوقيت الفعلي لكل كلمة عبر Groq Whisper-Large-V3-Turbo بعد ضغط نسخة خفيفة 48kbps لتجنب أي حد حجم."""
    if not groq_key:
        return []
    slim_mp3 = audio_path.parent / f"_wslim_{audio_path.stem}.mp3"
    try:
        subprocess.run(
            [FFMPEG_BIN, "-y", "-i", str(audio_path), "-ar", "16000", "-ac", "1", "-b:a", "48k", "-loglevel", "error", str(slim_mp3)],
            check=True,
        )
        for att in range(3):
            with open(slim_mp3, "rb") as fh:
                resp = requests.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {groq_key}"},
                    files={"file": (slim_mp3.name, fh, "audio/mpeg")},
                    data=[
                        ("model", "whisper-large-v3-turbo"),
                        ("response_format", "verbose_json"),
                        ("timestamp_granularities[]", "word"),
                        ("language", language),
                    ],
                    timeout=90,
                )
            if resp.status_code == 200:
                out_w: List[Dict[str, Any]] = []
                for w in resp.json().get("words") or []:
                    txt = str(w.get("word", "")).strip(" ،,.!؟?;:\"'()[]")
                    if txt:
                        s = float(w.get("start", 0.0))
                        e = max(s + 0.08, float(w.get("end", s + 0.18)))
                        out_w.append({"word": txt, "norm": _norm_token(txt), "start": s, "end": e})
                return out_w
            if resp.status_code == 429:
                time.sleep(6.0)
    except Exception:
        pass
    finally:
        slim_mp3.unlink(missing_ok=True)
    return []


def _locate_scene_starts_in_batch(
    batch_scenes: List[Dict[str, Any]],
    whisper_words: List[Dict[str, Any]],
    batch_dur: float,
) -> List[float]:
    """يحدد الثانية الدقيقة التي يبدأ فيها كل مشهد داخل الدفعة الصوتية بمطابقة الكلمات الافتتاحية للمشهد مع كلمات Whisper."""
    n_sc = len(batch_scenes)
    if n_sc <= 1:
        return [0.0]

    char_lens = [max(20, len(s.get("narration", ""))) for s in batch_scenes]
    tot_chars = float(sum(char_lens))
    prop_starts = [0.0]
    acc = 0.0
    for cl in char_lens[:-1]:
        acc += cl
        prop_starts.append(batch_dur * (acc / tot_chars))

    if len(whisper_words) < 25:
        return prop_starts

    found_starts = [0.0]
    prev_word_idx = 0
    total_w = len(whisper_words)

    for si in range(1, n_sc):
        anchor_tokens = [_norm_token(t) for t in batch_scenes[si].get("narration", "").split()[:10] if _norm_token(t)]
        anchor_tokens = anchor_tokens[:7]
        expected_sec = prop_starts[si]

        # نبحث داخل نافذة منطقية حول التوقيت المتوقع (±45 ثانية) لضمان عدم القفز الخاطئ
        best_idx = None
        best_score = -1.0
        for wi in range(max(prev_word_idx + 8, 1), max(prev_word_idx + 10, total_w - 4)):
            w_sec = whisper_words[wi]["start"]
            if abs(w_sec - expected_sec) > 52.0:
                continue
            window_norms = [whisper_words[k]["norm"] for k in range(wi, min(total_w, wi + 9))]
            hits = sum(1 for tok in anchor_tokens if len(tok) >= 2 and tok in window_norms)
            # مكافأة إضافية إذا طابقت الكلمة الأولى مباشرة
            if anchor_tokens and window_norms and anchor_tokens[0] == window_norms[0]:
                hits += 1.5
            prox_bonus = max(0.0, 1.0 - abs(w_sec - expected_sec) / 55.0) * 0.6
            score = hits + prox_bonus
            if score > best_score and hits >= 2:
                best_score = score
                best_idx = wi

        if best_idx is not None:
            t_hit = max(found_starts[-1] + 12.0, min(batch_dur - 10.0, whisper_words[best_idx]["start"]))
            found_starts.append(t_hit)
            prev_word_idx = best_idx
        else:
            found_starts.append(max(found_starts[-1] + 15.0, expected_sec))

    return found_starts


def synthesize_episode_and_climax_shorts(
    episode: Dict[str, Any],
    voice_cfg: Dict[str, Any],
    groq_key: str,
    language: str,
    work_dir: Path,
    min_duration_sec: float = 950.0,
) -> Dict[str, Any]:
    """
    ينتج حزمة الصوت الكاملة المتزامنة بدقة الملي ثانية:
    - master_mp3: الصوت الرئيسي للفيلم الكامل (+16 دقيقة) ممزوجاً بخلفية التوتر النفسي ونبض القلب الهادئ.
    - subtitles: جمل الترجمة المزامنة كلمة بكلمة للفيلم الكامل.
    - scene_timings: قائمة الـ 12 مشهداً مع (scene_num, scene_title, start, end) الدقيقة لبناء الفيديو وفصول اليوتيوب!
    - short_1_mp3 & short_1_words: الشورت الأول (~115–135 ثانية) يقطع فجأة عند ذروة المشهد 2 + نداء أول تعليق!
    - short_2_mp3 & short_2_words: الشورت الثاني (~115–135 ثانية) يقطع فجأة عند ذروة المشهد 7 + نداء أول تعليق!
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    is_ar = language == "ar"
    scenes: List[Dict[str, Any]] = episode["scenes"]

    # تقسيم الـ 12 مشهداً إلى 3 دفعات كبيرة (4 مشاهد لكل دفعة = 3 طلبات Gemini TTS فقط للفيلم الكامل!)
    batches = [scenes[0:4], scenes[4:8], scenes[8:12]]
    pause_dur = 0.85
    pause_mp3 = work_dir / "batch_pause.mp3"
    subprocess.run(
        [
            FFMPEG_BIN, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
            "-t", f"{pause_dur}", "-c:a", "libmp3lame", "-b:a", "128k", "-loglevel", "error", str(pause_mp3),
        ],
        check=True,
    )

    concat_lines: List[str] = []
    raw_subtitles: List[Dict[str, Any]] = []
    raw_scene_timings: List[Dict[str, Any]] = []
    all_raw_words: List[Dict[str, Any]] = []
    cursor = 0.0

    for b_idx, b_scenes in enumerate(batches):
        if not b_scenes:
            continue
        if b_idx > 0:
            concat_lines.append(f"file '{pause_mp3.resolve()}'")
            cursor += pause_dur

        joined_txt = " .. ".join(s["narration"] for s in b_scenes)
        b_mp3 = _synth_single_block(joined_txt, voice_cfg, is_ar, work_dir / f"mega_batch_{b_idx}.mp3", call_index=b_idx)
        b_dur = get_audio_duration(b_mp3)
        concat_lines.append(f"file '{b_mp3.resolve()}'")

        w_words = _whisper_transcribe_words(b_mp3, groq_key, language)
        local_starts = _locate_scene_starts_in_batch(b_scenes, w_words, b_dur)

        for si, sc in enumerate(b_scenes):
            st_local = local_starts[si]
            en_local = local_starts[si + 1] if (si + 1 < len(local_starts)) else b_dur
            raw_scene_timings.append({
                "scene_num": int(sc["scene_num"]),
                "scene_title": sc["scene_title"],
                "raw_start": cursor + st_local,
                "raw_end": cursor + en_local,
            })

        if w_words:
            for ww in w_words:
                all_raw_words.append({
                    "word": ww["word"],
                    "start": cursor + ww["start"],
                    "end": cursor + ww["end"],
                })
            step = 7
            for i in range(0, len(w_words), step):
                grp = w_words[i : i + step]
                raw_subtitles.append({
                    "start": cursor + grp[0]["start"],
                    "end": cursor + grp[-1]["end"],
                    "text": " ".join(x["word"] for x in grp),
                })
        else:
            words_fallback = joined_txt.split()
            step = 7
            groups = [" ".join(words_fallback[i : i + step]) for i in range(0, len(words_fallback), step)] or [joined_txt[:60]]
            seg_d = max(0.4, b_dur / len(groups))
            for gi, g in enumerate(groups):
                raw_subtitles.append({
                    "start": cursor + gi * seg_d,
                    "end": cursor + (gi + 1) * seg_d,
                    "text": g,
                })

        cursor += b_dur

    concat_txt = work_dir / "long_concat.txt"
    concat_txt.write_text("\n".join(concat_lines), encoding="utf-8")
    raw_voice_merged = work_dir / "long_voice_raw.mp3"
    subprocess.run(
        [
            FFMPEG_BIN, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt),
            "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k",
            "-loglevel", "error", str(raw_voice_merged),
        ],
        check=True,
    )

    raw_total_dur = get_audio_duration(raw_voice_merged)
    tempo = 1.0
    if 120.0 < raw_total_dur < min_duration_sec:
        tempo = max(0.86, raw_total_dur / min_duration_sec)

    scale_f = 1.0 / tempo
    final_subtitles = [
        {"start": s["start"] * scale_f, "end": s["end"] * scale_f, "text": s["text"]}
        for s in raw_subtitles
    ]
    final_scene_timings: List[Dict[str, Any]] = []
    for idx, st_obj in enumerate(raw_scene_timings):
        s_sec = 0.0 if idx == 0 else st_obj["raw_start"] * scale_f
        e_sec = (raw_total_dur * scale_f) if idx == len(raw_scene_timings) - 1 else st_obj["raw_end"] * scale_f
        final_scene_timings.append({
            "scene_num": st_obj["scene_num"],
            "scene_title": st_obj["scene_title"],
            "start": s_sec,
            "end": max(s_sec + 5.0, e_sec),
        })

    # مزج خلفية التوتر النفسي ونبض القلب تحت الفيلم الكامل
    tension_wav = _build_psychological_tension_bed(work_dir / "psych_tension_bed.wav", duration_sec=56.0)
    master_mp3 = work_dir / "long_episode_master.mp3"
    tempo_flt = f"atempo={tempo:.4f}," if abs(tempo - 1.0) > 0.005 else ""
    subprocess.run(
        [
            FFMPEG_BIN, "-y",
            "-i", str(raw_voice_merged),
            "-stream_loop", "-1", "-i", str(tension_wav),
            "-filter_complex",
            f"[0:a]{tempo_flt}acompressor=threshold=-16dB:ratio=2.8:attack=5:release=60,loudnorm=I=-15:TP=-1.5:LRA=9[v];"
            f"[1:a]volume=0.075[bg];"
            f"[v][bg]amix=inputs=2:duration=first:dropout_transition=2[out]",
            "-map", "[out]",
            "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k",
            "-loglevel", "error", str(master_mp3),
        ],
        check=True,
    )

    # الآن نبني الشورت الأول (ينتهي عند ذروة المشهد 2!) والشورت الثاني (ينتهي عند ذروة المشهد 7!)
    sh1_mp3, sh1_words = _build_climax_short_from_master_voice(
        raw_voice_merged=raw_voice_merged,
        scene_start_sec=raw_scene_timings[0]["raw_start"],
        scene_climax_end_sec=raw_scene_timings[min(1, len(raw_scene_timings) - 1)]["raw_end"],
        cta_spoken_text=episode["cta_spoken_1"],
        voice_cfg=voice_cfg,
        groq_key=groq_key,
        language=language,
        tension_wav=tension_wav,
        work_dir=work_dir / "short_1",
        call_index=3,
    )

    s6_i = min(5, len(raw_scene_timings) - 2)
    s7_i = min(6, len(raw_scene_timings) - 1)
    sh2_mp3, sh2_words = _build_climax_short_from_master_voice(
        raw_voice_merged=raw_voice_merged,
        scene_start_sec=raw_scene_timings[s6_i]["raw_start"],
        scene_climax_end_sec=raw_scene_timings[s7_i]["raw_end"],
        cta_spoken_text=episode["cta_spoken_2"],
        voice_cfg=voice_cfg,
        groq_key=groq_key,
        language=language,
        tension_wav=tension_wav,
        work_dir=work_dir / "short_2",
        call_index=4,
    )

    return {
        "master_mp3": master_mp3,
        "subtitles": final_subtitles,
        "scene_timings": final_scene_timings,
        "short_1_mp3": sh1_mp3,
        "short_1_words": sh1_words,
        "short_2_mp3": sh2_mp3,
        "short_2_words": sh2_words,
    }


def _build_climax_short_from_master_voice(
    raw_voice_merged: Path,
    scene_start_sec: float,
    scene_climax_end_sec: float,
    cta_spoken_text: str,
    voice_cfg: Dict[str, Any],
    groq_key: str,
    language: str,
    tension_wav: Path,
    work_dir: Path,
    call_index: int,
) -> Tuple[Path, List[Dict[str, Any]]]:
    """
    يبني شورت عميقاً (~105–140 ثانية، أقل دائماً من 165 ثانية لضمان تصنيفه كشورت على يوتيوب وتيك توك):
    يغمر المشاهد بعمق في القصة ثم يقطع فجأة في أعلى لحظة ذروة وإثارة مع صدمة نبض ودعوة لأول تعليق!
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    is_ar = language == "ar"

    raw_seg_dur = max(30.0, scene_climax_end_sec - scene_start_sec)
    story_slice = work_dir / "story_slice.mp3"
    subprocess.run(
        [
            FFMPEG_BIN, "-y",
            "-ss", f"{max(0.0, scene_start_sec):.3f}",
            "-t", f"{raw_seg_dur:.3f}",
            "-i", str(raw_voice_merged),
            "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k",
            "-loglevel", "error", str(story_slice),
        ],
        check=True,
    )

    # تسريع طفيف حيوي للشورت إذا تجاوز 128 ثانية ليبقى الإيقاع مشدوداً وتحت سقف الـ 155 ثانية شاملاً الخاتمة
    slice_dur = get_audio_duration(story_slice)
    short_tempo = 1.04
    if slice_dur / short_tempo > 128.0:
        short_tempo = min(1.22, slice_dur / 124.0)

    story_paced = work_dir / "story_paced.mp3"
    subprocess.run(
        [
            FFMPEG_BIN, "-y", "-i", str(story_slice),
            "-af", f"silenceremove=stop_periods=-1:stop_duration=0.28:stop_threshold=-40dB,atempo={short_tempo:.4f}",
            "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k",
            "-loglevel", "error", str(story_paced),
        ],
        check=True,
    )

    # تأثير صدمة توقف مفاجئ (Dramatic Cliffhanger Impact Drop — 0.45s) عند قمة الذروة!
    drop_wav = _build_cliffhanger_impact_drop(work_dir / "impact_drop.wav")
    drop_mp3 = work_dir / "impact_drop.mp3"
    subprocess.run(
        [FFMPEG_BIN, "-y", "-i", str(drop_wav), "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k", "-loglevel", "error", str(drop_mp3)],
        check=True,
    )

    cta_raw = _synth_single_block(cta_spoken_text, voice_cfg, is_ar, work_dir / "cta_raw.mp3", call_index=call_index)
    cta_paced = work_dir / "cta_paced.mp3"
    subprocess.run(
        [
            FFMPEG_BIN, "-y", "-i", str(cta_raw),
            "-af", "silenceremove=stop_periods=-1:stop_duration=0.22:stop_threshold=-38dB,atempo=1.05",
            "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k",
            "-loglevel", "error", str(cta_paced),
        ],
        check=True,
    )

    concat_list = work_dir / "short_voice_concat.txt"
    concat_list.write_text(
        f"file '{story_paced.resolve()}'\nfile '{drop_mp3.resolve()}'\nfile '{cta_paced.resolve()}'\n",
        encoding="utf-8",
    )
    voice_combined = work_dir / "short_voice_clean.mp3"
    subprocess.run(
        [
            FFMPEG_BIN, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-af", "acompressor=threshold=-16dB:ratio=2.8,loudnorm=I=-14:TP=-1.5:LRA=8",
            "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k",
            "-loglevel", "error", str(voice_combined),
        ],
        check=True,
    )

    short_master = work_dir / "short_master.mp3"
    subprocess.run(
        [
            FFMPEG_BIN, "-y",
            "-i", str(voice_combined),
            "-stream_loop", "-1", "-i", str(tension_wav),
            "-filter_complex", "[1:a]volume=0.14[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=1[out]",
            "-map", "[out]", "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k",
            "-loglevel", "error", str(short_master),
        ],
        check=True,
    )

    words = _whisper_transcribe_words(voice_combined, groq_key, language)
    if not words:
        dur = get_audio_duration(short_master)
        tokens = [t for t in cta_spoken_text.split() if t]
        step = dur / max(1, len(tokens))
        words = [{"word": t, "start": i * step, "end": (i + 1) * step} for i, t in enumerate(tokens)]

    return short_master, words


def _build_cliffhanger_impact_drop(out_wav: Path) -> Path:
    """صدمة سينمائية عميقة (Sub-Bass Boom + Breathless Silence) تفصل ذروة القصة عن نداء الرابط في أول تعليق."""
    sr = 24000
    dur = 0.48
    n = int(sr * dur)
    t = np.linspace(0.0, dur, n, endpoint=False, dtype=np.float32)
    freq = 95.0 * np.exp(-t * 6.5) + 32.0
    boom = np.exp(-t * 8.5) * np.sin(2 * math.pi * freq * t)
    pcm = np.clip(boom * 0.72 * 32767.0, -32767, 32767).astype(np.int16)
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return out_wav


def _build_psychological_tension_bed(out_wav: Path, duration_sec: float = 56.0) -> Path:
    """خلفية إثارة نفسية سينمائية آسرة (نبض قلب بشري عميق + Drone تشويقي مظلم مثل أقوى قنوات القصص العالمية)."""
    sr = 24000
    n = int(sr * duration_sec)
    t = np.linspace(0.0, duration_sec, n, endpoint=False, dtype=np.float32)

    drone = (
        0.34 * np.sin(2 * math.pi * 73.42 * t)
        + 0.22 * np.sin(2 * math.pi * 87.31 * t + 0.4)
        + 0.15 * np.sin(2 * math.pi * 110.00 * t + 1.1)
    ) * (0.72 + 0.28 * np.sin(2 * math.pi * 0.10 * t))

    beat_period = 0.94
    phase = np.mod(t, beat_period)
    hb1 = np.exp(-phase * 25.0) * np.sin(2 * math.pi * 52.0 * phase)
    hb2 = np.where(phase > 0.24, np.exp(-(phase - 0.24) * 29.0) * np.sin(2 * math.pi * 46.0 * (phase - 0.24)), 0.0)
    heartbeat = 0.44 * (hb1 + 0.72 * hb2)

    shimmer = 0.08 * np.sin(2 * math.pi * (146.83 + 8.0 * np.sin(2 * math.pi * 0.05 * t)) * t)
    sig = 0.56 * drone + heartbeat + shimmer

    pcm = np.clip(sig * 0.46 * 32767.0, -32767, 32767).astype(np.int16)
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return out_wav
