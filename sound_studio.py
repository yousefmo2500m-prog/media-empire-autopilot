# -*- coding: utf-8 -*-
"""
استوديو الصوت البشري والمقدمة التشويقية V11.0 (Cold-Open Teaser Intro + 5-Key Pure Human Voice + Dynamic Pacing Windows)
- يسجّل المقدمة التشويقية النارية (`teaser_intro`) كافتتاحية سينمائية خاطفة (00:00–00:28) متبوعة بضربة تشويق سينمائية (Cinema Boom Transition) قبل بدء المشهد الأول!
- تقطيع سريع في المقدمة (صورة كل ~4.5 ثانية في أول 28 ثانية لخطف عين المشاهد فوراً ومنع الخروج المبكر!) ثم صورة جديدة كل ~8 ثوانٍ طوال الـ 12 مشهداً بلا أي تكرار!
- في الشورتات (Shorts): مقدمة خطف في أول 4 ثوانٍ + تقطيع بصري سريع (صورة طولية كاملة جديدة كل ~5.5 ثانية!) لرفع معدل الإكمال فوق 75%.
- حظر الأصوات الآلية (edge_tts) نهائياً 100%.
"""

import base64
import math
import os
import re
import subprocess
import time
import wave
from pathlib import Path
from typing import Any, Dict, List, Tuple

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
    txt = re.sub(r"\.{3,}", "..", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def _norm_token(word: str) -> str:
    w = word.lower().strip()
    w = re.sub(r"[^\w\u0600-\u06FF]", "", w)
    w = re.sub(r"[\u064B-\u065F\u0670]", "", w)
    for src, dst in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ة", "ه"), ("ى", "ي")):
        w = w.replace(src, dst)
    return w


def _get_gemini_keys() -> List[str]:
    keys: List[str] = []
    for env_name in (
        "GEMINI_API_KEY_2",
        "GEMINI_API_KEY_3",
        "GEMINI_API_KEY_4",
        "GEMINI_API_KEY_5",
        "GEMINI_API_KEY",
    ):
        val = os.environ.get(env_name, "").strip()
        if val and val not in keys:
            keys.append(val)
    return keys


def _try_gemini_tts_strict(
    text: str,
    is_arabic: bool,
    out_mp3: Path,
    gemini_voice: str = "Kore",
    call_index: int = 0,
) -> bool:
    gkeys = _get_gemini_keys()
    if not gkeys:
        return False

    vname = gemini_voice or ("Kore" if is_arabic else "Aoede")
    lang_code = "ar-EG" if is_arabic else "en-US"
    n_m = len(GEMINI_TTS_MODELS)

    for wave_try in range(3):
        saw_minute_limit = False
        for ki in range(len(gkeys)):
            key_idx = (call_index + ki) % len(gkeys)
            active_key = gkeys[key_idx]
            for mi in range(n_m):
                model_id = GEMINI_TTS_MODELS[(call_index + mi) % n_m]
                try:
                    r = requests.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={active_key}",
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
                        timeout=180,
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
                            print(f"    🎙️ [Human Studio Voice: {model_id} / {vname} / Key#{key_idx+1}] -> {get_audio_duration(out_mp3):.1f}s", flush=True)
                            return True
                    elif r.status_code == 429:
                        low_err = r.text.lower()
                        if "perminute" in low_err or "per_minute" in low_err or "tokens" in low_err or "rate" in low_err:
                            saw_minute_limit = True
                except Exception:
                    continue
        if wave_try < 2 and saw_minute_limit:
            print("    ⏳ [Gemini Studio Cooldown] انتظار 62 ثانية لتجديد نافذة الدقيقة وضمان ثبات الصوت البشري 100%...", flush=True)
            time.sleep(62.0)
        elif wave_try < 2:
            time.sleep(15.0)
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
                json={"model": "canopylabs/orpheus-v1-english", "input": sub, "voice": voice_id or "tara", "response_format": "wav"},
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
        for p in [*wav_parts, lst]:
            p.unlink(missing_ok=True)
        return out_mp3.exists() and out_mp3.stat().st_size > 800
    except Exception:
        return False


def _synth_human_block(
    text: str,
    voice_cfg: Dict[str, Any],
    is_arabic: bool,
    out_mp3: Path,
    call_index: int = 0,
) -> Path:
    clean = _sanitize_tts_text(text)
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    if _try_gemini_tts_strict(clean, is_arabic, out_mp3, voice_cfg.get("gemini_voice", "Kore"), call_index):
        return out_mp3
    if (not is_arabic) and _try_groq_orpheus(clean, voice_cfg.get("orpheus_voice", "tara"), out_mp3):
        return out_mp3
    raise RuntimeError("تعذر توليد الصوت البشري (تم حظر الأصوات الآلية edge_tts نهائياً).")


def _whisper_transcribe_words(audio_path: Path, groq_key: str, language: str) -> List[Dict[str, Any]]:
    if not groq_key:
        return []
    slim_mp3 = audio_path.parent / f"_wslim_{audio_path.stem}.mp3"
    try:
        subprocess.run(
            [FFMPEG_BIN, "-y", "-i", str(audio_path), "-ar", "16000", "-ac", "1", "-b:a", "48k", "-loglevel", "error", str(slim_mp3)],
            check=True,
        )
        for _ in range(3):
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
        anchor_tokens = [_norm_token(t) for t in batch_scenes[si].get("narration", "").split()[:10] if _norm_token(t)][:7]
        expected_sec = prop_starts[si]
        best_idx = None
        best_score = -1.0
        for wi in range(max(prev_word_idx + 8, 1), max(prev_word_idx + 10, total_w - 4)):
            w_sec = whisper_words[wi]["start"]
            if abs(w_sec - expected_sec) > 52.0:
                continue
            window_norms = [whisper_words[k]["norm"] for k in range(wi, min(total_w, wi + 9))]
            hits = sum(1 for tok in anchor_tokens if len(tok) >= 2 and tok in window_norms)
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


def build_dynamic_pacing_windows(
    total_dur: float,
    teaser_end_sec: float,
    words: List[Dict[str, Any]],
    fallback_text: str,
    teaser_interval_sec: float = 4.5,
    body_interval_sec: float = 8.0,
) -> List[Dict[str, Any]]:
    """
    تقطيع ديناميكي احترافي (2026 Retention Pacing):
    - في المقدمة التشويقية (0 إلى teaser_end_sec): لقطة جديدة كل ~4.5 ثانية لخطف عين المشاهد ومنع الخروج المبكر!
    - في جسم القصة (من teaser_end_sec للنهاية): لقطة جديدة كل ~8.0 ثانية بدون أي تكرار إطلاقاً!
    """
    windows: List[Dict[str, Any]] = []
    fb_words = fallback_text.split()

    def _slice_span(span_start: float, span_end: float, step_s: float) -> None:
        span = max(0.5, span_end - span_start)
        n_w = max(1, int(round(span / max(3.0, step_s))))
        w_d = span / float(n_w)
        for k in range(n_w):
            st = span_start + k * w_d
            en = span_end if k == n_w - 1 else (span_start + (k + 1) * w_d)
            matched = [w["word"] for w in words if (w["end"] > st and w["start"] < en)]
            if matched:
                spoken = " ".join(matched)
            else:
                r0 = int(len(fb_words) * (st / max(1.0, total_dur)))
                r1 = int(len(fb_words) * (en / max(1.0, total_dur)))
                spoken = " ".join(fb_words[r0 : max(r0 + 7, r1)])
            windows.append({"idx": len(windows), "start": st, "end": en, "dur": en - st, "text": spoken})

    if teaser_end_sec > 3.0 and teaser_end_sec < total_dur - 10.0:
        _slice_span(0.0, teaser_end_sec, teaser_interval_sec)
        _slice_span(teaser_end_sec, total_dur, body_interval_sec)
    else:
        _slice_span(0.0, total_dur, body_interval_sec)
    return windows


def synthesize_episode_and_climax_shorts(
    episode: Dict[str, Any],
    voice_cfg: Dict[str, Any],
    groq_key: str,
    language: str,
    work_dir: Path,
    min_duration_sec: float = 945.0,
    shot_interval_sec: float = 8.0,
) -> Dict[str, Any]:
    work_dir.mkdir(parents=True, exist_ok=True)
    is_ar = language == "ar"
    scenes: List[Dict[str, Any]] = episode["scenes"]
    teaser_text = str(episode.get("teaser_intro") or "").strip()

    pause_dur = 0.80
    pause_mp3 = work_dir / "batch_pause.mp3"
    subprocess.run(
        [
            FFMPEG_BIN, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
            "-t", f"{pause_dur}", "-c:a", "libmp3lame", "-b:a", "128k", "-loglevel", "error", str(pause_mp3),
        ],
        check=True,
    )

    intro_boom_wav = _build_cliffhanger_impact_drop(work_dir / "intro_boom.wav")
    intro_boom_mp3 = work_dir / "intro_boom.mp3"
    subprocess.run(
        [FFMPEG_BIN, "-y", "-i", str(intro_boom_wav), "-ar", "24000", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "192k", "-loglevel", "error", str(intro_boom_mp3)],
        check=True,
    )
    boom_dur = get_audio_duration(intro_boom_mp3)

    concat_lines: List[str] = []
    raw_subtitles: List[Dict[str, Any]] = []
    raw_scene_timings: List[Dict[str, Any]] = []
    all_raw_words: List[Dict[str, Any]] = []
    cursor = 0.0

    # 0) تسجيل المقدمة التشويقية النارية (Cold-Open Climax Teaser) في أول 25–30 ثانية!
    teaser_mp3 = _synth_human_block(teaser_text, voice_cfg, is_ar, work_dir / "teaser_intro.mp3", call_index=0)
    teaser_dur = get_audio_duration(teaser_mp3)
    concat_lines.append(f"file '{teaser_mp3.resolve()}'")
    t_words = _whisper_transcribe_words(teaser_mp3, groq_key, language)
    if t_words:
        for ww in t_words:
            all_raw_words.append({"word": ww["word"], "start": cursor + ww["start"], "end": cursor + ww["end"]})
        for i in range(0, len(t_words), 6):
            grp = t_words[i : i + 6]
            raw_subtitles.append({"start": cursor + grp[0]["start"], "end": cursor + grp[-1]["end"], "text": " ".join(x["word"] for x in grp)})
    else:
        tws = teaser_text.split()
        groups = [" ".join(tws[i : i + 6]) for i in range(0, len(tws), 6)] or [teaser_text[:60]]
        sd = max(0.4, teaser_dur / len(groups))
        for gi, g in enumerate(groups):
            raw_subtitles.append({"start": cursor + gi * sd, "end": cursor + (gi + 1) * sd, "text": g})

    raw_teaser_end = teaser_dur + boom_dur
    raw_scene_timings.append({
        "scene_num": 0,
        "scene_title": "المقدمة التشويقية: مقتطف من ذروة الأحداث" if is_ar else "Cold Open: Climax Preview",
        "raw_start": 0.0,
        "raw_end": raw_teaser_end,
    })
    cursor += teaser_dur
    concat_lines.append(f"file '{intro_boom_mp3.resolve()}'")
    cursor += boom_dur

    # 1) تسجيل الـ 12 مشهداً في 3 دفعات متصلة بصوت بشري صافي 100%
    batches = [scenes[0:4], scenes[4:8], scenes[8:12]]
    for b_idx, b_scenes in enumerate(batches):
        if not b_scenes:
            continue
        if b_idx > 0:
            concat_lines.append(f"file '{pause_mp3.resolve()}'")
            cursor += pause_dur

        joined_txt = " .. ".join(s["narration"] for s in b_scenes)
        b_mp3 = _synth_human_block(joined_txt, voice_cfg, is_ar, work_dir / f"mega_batch_{b_idx}.mp3", call_index=b_idx + 1)
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
                all_raw_words.append({"word": ww["word"], "start": cursor + ww["start"], "end": cursor + ww["end"]})
            for i in range(0, len(w_words), 7):
                grp = w_words[i : i + 7]
                raw_subtitles.append({"start": cursor + grp[0]["start"], "end": cursor + grp[-1]["end"], "text": " ".join(x["word"] for x in grp)})
        else:
            words_fb = joined_txt.split()
            groups = [" ".join(words_fb[i : i + 7]) for i in range(0, len(words_fb), 7)] or [joined_txt[:60]]
            seg_d = max(0.4, b_dur / len(groups))
            for gi, g in enumerate(groups):
                raw_subtitles.append({"start": cursor + gi * seg_d, "end": cursor + (gi + 1) * seg_d, "text": g})

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
        tempo = max(0.88, raw_total_dur / min_duration_sec)

    scale_f = 1.0 / tempo
    final_teaser_end = raw_teaser_end * scale_f
    final_words = [{"word": w["word"], "start": w["start"] * scale_f, "end": w["end"] * scale_f} for w in all_raw_words]
    final_subtitles = [{"start": s["start"] * scale_f, "end": s["end"] * scale_f, "text": s["text"]} for s in raw_subtitles]
    final_scene_timings: List[Dict[str, Any]] = []
    for idx, st_obj in enumerate(raw_scene_timings):
        s_sec = 0.0 if idx == 0 else st_obj["raw_start"] * scale_f
        e_sec = (raw_total_dur * scale_f) if idx == len(raw_scene_timings) - 1 else st_obj["raw_end"] * scale_f
        final_scene_timings.append({
            "scene_num": st_obj["scene_num"],
            "scene_title": st_obj["scene_title"],
            "start": s_sec,
            "end": max(s_sec + 4.0, e_sec),
        })

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
            f"[1:a]volume=0.09[bg];"
            f"[v][bg]amix=inputs=2:duration=first:dropout_transition=2[out]",
            "-map", "[out]",
            "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k",
            "-loglevel", "error", str(master_mp3),
        ],
        check=True,
    )

    master_dur = get_audio_duration(master_mp3)
    full_story_text = teaser_text + " " + " ".join(s["narration"] for s in scenes)
    long_windows = build_dynamic_pacing_windows(
        total_dur=master_dur + 0.4,
        teaser_end_sec=final_teaser_end,
        words=final_words,
        fallback_text=full_story_text,
        teaser_interval_sec=4.5,
        body_interval_sec=shot_interval_sec,
    )

    # الشورت الأول (مقدمة خطف + ذروة المشهد 2!) والشورت الثاني (مقدمة خطف + ذروة المشهد 7!)
    # نجد توقيت المشهد 1 والمشهد 2 (بعد المقدمة التي تحمل index 0)
    sc1_t = next(x for x in raw_scene_timings if x["scene_num"] == 1)
    sc2_t = next(x for x in raw_scene_timings if x["scene_num"] == 2)
    sc6_t = next(x for x in raw_scene_timings if x["scene_num"] == 6)
    sc7_t = next(x for x in raw_scene_timings if x["scene_num"] == 7)

    sh1_mp3, sh1_words, sh1_hook_end = _build_climax_short_from_master_voice(
        raw_voice_merged=raw_voice_merged,
        hook_intro_text=episode.get("short_1_hook_intro", ""),
        scene_start_sec=sc1_t["raw_start"],
        scene_climax_end_sec=sc2_t["raw_end"],
        cta_spoken_text=episode["cta_spoken_1"],
        voice_cfg=voice_cfg,
        groq_key=groq_key,
        language=language,
        tension_wav=tension_wav,
        work_dir=work_dir / "short_1",
        call_index=4,
    )
    sh1_dur = get_audio_duration(sh1_mp3)
    sh1_windows = build_dynamic_pacing_windows(
        total_dur=sh1_dur + 0.3,
        teaser_end_sec=sh1_hook_end,
        words=sh1_words,
        fallback_text=f"{episode.get('short_1_hook_intro','')} {scenes[0]['narration']} {scenes[1]['narration']}",
        teaser_interval_sec=4.2,
        body_interval_sec=6.4,
    )

    sh2_mp3, sh2_words, sh2_hook_end = _build_climax_short_from_master_voice(
        raw_voice_merged=raw_voice_merged,
        hook_intro_text=episode.get("short_2_hook_intro", ""),
        scene_start_sec=sc6_t["raw_start"],
        scene_climax_end_sec=sc7_t["raw_end"],
        cta_spoken_text=episode["cta_spoken_2"],
        voice_cfg=voice_cfg,
        groq_key=groq_key,
        language=language,
        tension_wav=tension_wav,
        work_dir=work_dir / "short_2",
        call_index=0,
    )
    sh2_dur = get_audio_duration(sh2_mp3)
    sh2_windows = build_dynamic_pacing_windows(
        total_dur=sh2_dur + 0.3,
        teaser_end_sec=sh2_hook_end,
        words=sh2_words,
        fallback_text=f"{episode.get('short_2_hook_intro','')} {scenes[5]['narration']} {scenes[6]['narration']}",
        teaser_interval_sec=4.2,
        body_interval_sec=6.4,
    )

    return {
        "master_mp3": master_mp3,
        "teaser_end_sec": final_teaser_end,
        "subtitles": final_subtitles,
        "scene_timings": final_scene_timings,
        "long_8s_windows": long_windows,
        "short_1_mp3": sh1_mp3,
        "short_1_words": sh1_words,
        "short_1_windows": sh1_windows,
        "short_1_hook_end": sh1_hook_end,
        "short_2_mp3": sh2_mp3,
        "short_2_words": sh2_words,
        "short_2_windows": sh2_windows,
        "short_2_hook_end": sh2_hook_end,
    }


def _build_climax_short_from_master_voice(
    raw_voice_merged: Path,
    hook_intro_text: str,
    scene_start_sec: float,
    scene_climax_end_sec: float,
    cta_spoken_text: str,
    voice_cfg: Dict[str, Any],
    groq_key: str,
    language: str,
    tension_wav: Path,
    work_dir: Path,
    call_index: int,
) -> Tuple[Path, List[Dict[str, Any]], float]:
    work_dir.mkdir(parents=True, exist_ok=True)
    is_ar = language == "ar"

    # نسجّل جملة الخطف الافتتاحية + جملة الـ CTA معاً في استدعاء واحد بفاصل صمت واضح لتوفير الحصة وتسريع الأداء!
    eff_start_sec = max(0.0, max(scene_start_sec, scene_climax_end_sec - 108.0))
    raw_seg_dur = max(28.0, scene_climax_end_sec - eff_start_sec)
    story_slice = work_dir / "story_slice.mp3"
    subprocess.run(
        [
            FFMPEG_BIN, "-y",
            "-ss", f"{eff_start_sec:.3f}",
            "-t", f"{raw_seg_dur:.3f}",
            "-i", str(raw_voice_merged),
            "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k",
            "-loglevel", "error", str(story_slice),
        ],
        check=True,
    )

    slice_dur = get_audio_duration(story_slice)
    short_tempo = 1.07
    if slice_dur / short_tempo > 102.0:
        short_tempo = min(1.22, slice_dur / 98.0)

    story_paced = work_dir / "story_paced.mp3"
    subprocess.run(
        [
            FFMPEG_BIN, "-y", "-i", str(story_slice),
            "-af", f"silenceremove=stop_periods=-1:stop_duration=0.25:stop_threshold=-40dB,atempo={short_tempo:.4f}",
            "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k",
            "-loglevel", "error", str(story_paced),
        ],
        check=True,
    )

    drop_wav = _build_cliffhanger_impact_drop(work_dir / "impact_drop.wav")
    drop_mp3 = work_dir / "impact_drop.mp3"
    subprocess.run(
        [FFMPEG_BIN, "-y", "-i", str(drop_wav), "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k", "-loglevel", "error", str(drop_mp3)],
        check=True,
    )

    parts_for_concat: List[str] = []
    hook_dur = 0.0
    if hook_intro_text and len(hook_intro_text.split()) >= 5:
        hook_raw = _synth_human_block(hook_intro_text, voice_cfg, is_ar, work_dir / "hook_raw.mp3", call_index=call_index)
        hook_paced = work_dir / "hook_paced.mp3"
        subprocess.run(
            [
                FFMPEG_BIN, "-y", "-i", str(hook_raw),
                "-af", "silenceremove=stop_periods=-1:stop_duration=0.20:stop_threshold=-38dB,atempo=1.06",
                "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k",
                "-loglevel", "error", str(hook_paced),
            ],
            check=True,
        )
        hook_dur = get_audio_duration(hook_paced) + get_audio_duration(drop_mp3)
        parts_for_concat.append(f"file '{hook_paced.resolve()}'")
        parts_for_concat.append(f"file '{drop_mp3.resolve()}'")

    cta_raw = _synth_human_block(cta_spoken_text, voice_cfg, is_ar, work_dir / "cta_raw.mp3", call_index=call_index + 2)
    cta_paced = work_dir / "cta_paced.mp3"
    subprocess.run(
        [
            FFMPEG_BIN, "-y", "-i", str(cta_raw),
            "-af", "silenceremove=stop_periods=-1:stop_duration=0.22:stop_threshold=-38dB,atempo=1.06",
            "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k",
            "-loglevel", "error", str(cta_paced),
        ],
        check=True,
    )

    parts_for_concat.extend([
        f"file '{story_paced.resolve()}'",
        f"file '{drop_mp3.resolve()}'",
        f"file '{cta_paced.resolve()}'",
    ])
    concat_list = work_dir / "short_voice_concat.txt"
    concat_list.write_text("\n".join(parts_for_concat) + "\n", encoding="utf-8")
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

    return short_master, words, max(4.0, hook_dur)


def _build_cliffhanger_impact_drop(out_wav: Path) -> Path:
    sr = 24000
    dur = 0.56
    n = int(sr * dur)
    t = np.linspace(0.0, dur, n, endpoint=False, dtype=np.float32)
    freq = 115.0 * np.exp(-t * 6.2) + 32.0
    boom = np.exp(-t * 7.5) * np.sin(2 * math.pi * freq * t)
    pcm = np.clip(boom * 0.80 * 32767.0, -32767, 32767).astype(np.int16)
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return out_wav


def _build_psychological_tension_bed(out_wav: Path, duration_sec: float = 56.0) -> Path:
    sr = 24000
    n = int(sr * duration_sec)
    t = np.linspace(0.0, duration_sec, n, endpoint=False, dtype=np.float32)

    drone = (
        0.34 * np.sin(2 * math.pi * 73.42 * t)
        + 0.22 * np.sin(2 * math.pi * 87.31 * t + 0.4)
        + 0.15 * np.sin(2 * math.pi * 110.00 * t + 1.1)
    ) * (0.72 + 0.28 * np.sin(2 * math.pi * 0.10 * t))

    beat_period = 0.90
    phase = np.mod(t, beat_period)
    hb1 = np.exp(-phase * 25.0) * np.sin(2 * math.pi * 52.0 * phase)
    hb2 = np.where(phase > 0.24, np.exp(-(phase - 0.24) * 29.0) * np.sin(2 * math.pi * 46.0 * (phase - 0.24)), 0.0)
    heartbeat = 0.47 * (hb1 + 0.74 * hb2)

    riser_phase = np.mod(t, 12.0)
    riser_env = np.where(riser_phase > 9.6, ((riser_phase - 9.6) / 2.4) ** 2, 0.0)
    riser = 0.19 * riser_env * np.sin(2 * math.pi * (120.0 + 38.0 * riser_env) * t)

    sig = 0.54 * drone + heartbeat + riser
    pcm = np.clip(sig * 0.46 * 32767.0, -32767, 32767).astype(np.int16)
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return out_wav
