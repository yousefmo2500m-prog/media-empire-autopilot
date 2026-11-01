#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
المشغّل الرئيسي لإمبراطورية القنوات السينمائية الترفيهية V2.0
"""

import argparse
import json
import os
import shutil
import time
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from channels_config import CHANNELS
from cinema_renderer import render_cinema_video, render_youtube_thumbnail
from empire_publisher import publish_channel_episode
from sound_studio import build_episode_soundtrack
from story_brain import (
    generate_documentary_or_riddle,
    generate_novel_episode,
    load_memory,
    save_memory,
)

BASE_DIR = Path(__file__).resolve().parent
MEMORY_PATH = BASE_DIR / "state" / "empire_memory.json"


def run_single_channel(
    channel_id: str,
    groq_key: str,
    out_dir: Path,
    mode: str = "full",
    publish: bool = False,
) -> dict:
    ch_cfg = CHANNELS[channel_id]
    prefix = ch_cfg["env_prefix"]

    if publish and not os.environ.get(f"{prefix}_ZERNIO_KEY", "").strip():
        print(f"⏭️ [{channel_id}] تخطّي مؤقت (بانتظار إضافة Secret باسم {prefix}_ZERNIO_KEY).")
        return {"channel": channel_id, "status": "waiting_for_key"}

    memory = load_memory(MEMORY_PATH)
    seed = int(time.time()) % 100000

    print(f"🎬 [{channel_id}] تأليف السيناريو التمثيلي بالعامية السينمائية...")
    if channel_id == "ch1_novels":
        script = generate_novel_episode(api_key=groq_key, memory=memory, mode=mode)
    else:
        script = generate_documentary_or_riddle(channel_id=channel_id, api_key=groq_key, memory=memory)

    ch_out = out_dir / channel_id
    work_dir = ch_out / "_work"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    ch_out.mkdir(parents=True, exist_ok=True)

    audio_wav = work_dir / "master_mix.wav"
    print(f"🎙️ [{channel_id}] تسجيل التمثيل الصوتي البشري والمؤثرات والبيانو...")
    timed_segments = build_episode_soundtrack(
        segments=script["segments"],
        voices_map=ch_cfg["voices"],
        mood=ch_cfg["music_key"],
        work_dir=work_dir,
        out_wav=audio_wav,
        seed=seed,
    )

    aspect = ch_cfg["aspect_primary"]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    mp4_path = ch_out / f"{channel_id}_{stamp}.mp4"
    thumb_path = ch_out / f"{channel_id}_{stamp}_thumb.jpg"
    meta_path = ch_out / f"{channel_id}_{stamp}_meta.json"

    print(f"🎥 [{channel_id}] تصوير اللقطات بـ FLUX 35mm والمونتاج السينمائي ({aspect})...")
    _, hero_art = render_cinema_video(
        channel_cfg=ch_cfg,
        script_data=script,
        timed_segments=timed_segments,
        audio_wav=audio_wav,
        out_mp4=mp4_path,
        aspect=aspect,
        seed=seed,
    )

    thumb_out = None
    if aspect == "16:9":
        thumb_out = render_youtube_thumbnail(
            channel_cfg=ch_cfg,
            script_data=script,
            hero_art=hero_art,
            out_jpg=thumb_path,
        )

    short_mp4 = None
    if channel_id == "ch1_novels" and mode == "full" and ch_cfg.get("also_render_short"):
        teaser_segs = timed_segments[: min(5, len(timed_segments))]
        short_mp4 = ch_out / f"{channel_id}_{stamp}_teaser_short.mp4"
        end_frame = int((teaser_segs[-1]["end_sec"] + 1.0) * 44100)
        teaser_wav = work_dir / "teaser_mix.wav"
        with wave.open(str(audio_wav), "rb") as rwf:
            frames = rwf.readframes(min(end_frame, rwf.getnframes()))
            with wave.open(str(teaser_wav), "wb") as wwf:
                wwf.setnchannels(2)
                wwf.setsampwidth(2)
                wwf.setframerate(44100)
                wwf.writeframes(frames)

        render_cinema_video(
            channel_cfg=ch_cfg,
            script_data=script,
            timed_segments=teaser_segs,
            audio_wav=teaser_wav,
            out_mp4=short_mp4,
            aspect="9:16",
            seed=seed + 7,
        )

    save_memory(MEMORY_PATH, memory)

    meta_info = {
        "channel_id": channel_id,
        "brand_name": ch_cfg["brand_name"],
        "youtube_title": script.get("youtube_title"),
        "episode_title": script.get("episode_title"),
        "description": script.get("description"),
        "first_comment": script.get("first_comment"),
        "video_file": str(mp4_path),
        "thumbnail_file": str(thumb_out) if thumb_out else None,
        "teaser_short_file": str(short_mp4) if short_mp4 else None,
    }
    meta_path.write_text(json.dumps(meta_info, ensure_ascii=False, indent=2), encoding="utf-8")

    if work_dir.exists():
        shutil.rmtree(work_dir)

    if publish:
        pub_res = publish_channel_episode(
            channel_cfg=ch_cfg,
            script_data=script,
            video_path=mp4_path,
            thumbnail_path=thumb_out,
        )
        meta_info["publish_result"] = pub_res

    print(f"✅ [{channel_id}] اكتمل الفيلم بنجاح: {mp4_path.name}")
    return meta_info


def main() -> None:
    parser = argparse.ArgumentParser(description="Autonomous Cinema Media Empire V2.0")
    parser.add_argument("--channel", default="all", choices=["all", *CHANNELS.keys()])
    parser.add_argument("--mode", default="full", choices=["full", "short"])
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--out-dir", default=str(BASE_DIR / "demo_outputs"))
    args = parser.parse_args()

    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not groq_key:
        raise SystemExit("❌ يرجى توفير GROQ_API_KEY.")

    targets: List[str] = list(CHANNELS.keys()) if args.channel == "all" else [args.channel]
    for ch_id in targets:
        run_single_channel(
            channel_id=ch_id,
            groq_key=groq_key,
            out_dir=Path(args.out_dir),
            mode=args.mode,
            publish=args.publish,
        )


if __name__ == "__main__":
    main()
