# -*- coding: utf-8 -*-
"""
استوديو الصوت الطبيعي للشورتس الفيروسية V3.0 (Natural Storytime Voice Studio)
- القناة المصرية: صوت راوية مصرية طبيعية ودافئة عبر VoiceTut-TTS (Mariam / Sarah)
  مع خط احتياطي سريع `ar-EG-SalmaNeural`.
- القناة الإنجليزية: راوٍ أمريكي تفاعلي طبيعي عبر ResembleAI Chatterbox
  مع خط احتياطي سريع `en-US-AndrewNeural` / `en-US-BrianNeural`.
- يقسّم القصة لجمل قصيرة ويدمجها بسلاسة لضمان عدم انقطاع الـ ZeroGPU أبداً.
"""

import asyncio
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import edge_tts
import imageio_ffmpeg
from gradio_client import Client

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


def _split_story_chunks(text: str, max_chars: int = 220) -> List[str]:
    sentences = re.split(r"(?<=[\.\!\؟\?،,])\s+", text.strip())
    chunks: List[str] = []
    cur = ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(cur) + len(s) + 1 <= max_chars:
            cur = f"{cur} {s}".strip()
        else:
            if cur:
                chunks.append(cur)
            cur = s
    if cur:
        chunks.append(cur)
    return chunks or [text.strip()]


def _synth_chunk(chunk_text: str, v_cfg: Dict[str, Any], out_stem: Path) -> Path:
    engine = v_cfg.get("engine", "voicetut_female")

    if engine == "voicetut_female":
        speaker = v_cfg.get("voicetut_speaker", "Mariam")
        try:
            client = _get_voicetut()
            wav_res, _ = client.predict(
                text=chunk_text,
                language="ar",
                voice_mode="preset",
                speaker=speaker,
                ref_audio=None,
                ref_text="",
                num_step=32,
                guidance=2.4,
                speed=1.02,
                normalize=True,
                api_name="/synthesize",
            )
            out_wav = out_stem.with_suffix(".wav")
            shutil.copyfile(str(wav_res), str(out_wav))
            if out_wav.stat().st_size > 800:
                return out_wav
        except Exception as exc:
            print(f"[VoiceTut Fallback -> SalmaNeural] {exc}")

    elif engine == "chatterbox_en":
        try:
            client = _get_chatterbox()
            wav_res = client.predict(
                text_input=chunk_text,
                audio_prompt_path_input=None,
                exaggeration_input=0.58,
                temperature_input=0.75,
                seed_num_input=0,
                cfgw_input=0.5,
                vad_trim_input=True,
                api_name="/generate_tts_audio",
            )
            out_wav = out_stem.with_suffix(".wav")
            shutil.copyfile(str(wav_res), str(out_wav))
            if out_wav.stat().st_size > 800:
                return out_wav
        except Exception as exc:
            print(f"[Chatterbox Fallback -> AndrewNeural] {exc}")

    out_mp3 = out_stem.with_suffix(".mp3")
    fb_voice = v_cfg.get("edge_voice", "ar-EG-SalmaNeural")
    fb_rate = v_cfg.get("edge_rate", "+8%")
    for attempt in range(3):
        try:
            comm = edge_tts.Communicate(chunk_text, fb_voice, rate=fb_rate)
            asyncio.run(comm.save(str(out_mp3)))
            if out_mp3.exists() and out_mp3.stat().st_size > 500:
                return out_mp3
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"فشل تسجيل المقطع الصوتي: {chunk_text[:40]}")


def _synth_single_line(full_story_text: str, v_cfg: Dict[str, Any], out_stem: Path) -> Path:
    """يسجّل القصة كاملة بجودة بشرية سلسة ويدمج أجزاءها في ملف صوتي واحد."""
    chunks = _split_story_chunks(full_story_text, max_chars=240)
    tmp_dir = out_stem.parent / "_tts_parts"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    part_files: List[Path] = []
    for idx, ch in enumerate(chunks):
        pf = _synth_chunk(ch, v_cfg, tmp_dir / f"part_{idx:03d}")
        part_files.append(pf)

    if len(part_files) == 1:
        return part_files[0]

    concat_txt = tmp_dir / "concat.txt"
    concat_txt.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in part_files),
        encoding="utf-8",
    )
    merged_mp3 = out_stem.with_suffix(".mp3")
    subprocess.run(
        [
            FFMPEG_BIN,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_txt),
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            "-loglevel",
            "error",
            str(merged_mp3),
        ],
        check=True,
    )
    return merged_mp3
