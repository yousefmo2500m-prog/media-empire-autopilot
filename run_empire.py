#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
المشغّل الرئيسي لإمبراطورية الشورتس الفيروسية V3.0 (Viral Satisfying Karma Storytime Empire)
1) يؤلف قصة رد اعتبار ذكية وممتعة بالعامية المصرية أو الإنجليزية عبر Groq.
2) يسجّل الصوت الطبيعي (صوت البنت المصرية أو الراوي الأمريكي) ويزيل السكتات الميتة.
3) يستخرج توقيت كل كلمة بالمللي ثانية عبر Groq Whisper-Large-V3-Turbo.
4) يركّب المقاطع المريحة للأعصاب 1080p + الكلمات القافزة في منتصف الشاشة كلمة بكلمة وينشر تلقائياً.
"""

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from channels_config import CHANNELS
from empire_publisher import publish_channel_episode
from satisfying_renderer import (
    assemble_viral_satisfying_short,
    extract_whisper_words,
    fetch_satisfying_clips,
    tighten_and_pace_voice,
)
from sound_studio import _synth_single_line
from story_brain import generate_karma_story, load_memory, save_memory

BASE_DIR = Path(__file__).resolve().parent
MEMORY_PATH = BASE_DIR / "state" / "empire_memory.json"
CLIPS_CACHE = Path("/tmp/satisfying_cc_pool")


def run_single_channel(
    channel_id: str,
    groq_key: str,
    out_dir: Path,
    publish: bool = False,
) -> dict:
    ch_cfg = CHANNELS[channel_id]
    prefix = ch_cfg["env_prefix"]

    if publish and not os.environ.get(f"{prefix}_ZERNIO_KEY", "").strip():
        print(f"⏭️ [{channel_id}] تخطّي مؤقت (بانتظار إضافة Secret باسم {prefix}_ZERNIO_KEY).")
        return {"channel": channel_id, "status": "waiting_for_key"}

    memory = load_memory(MEMORY_PATH)
    print(f"🎬 [{channel_id}] تأليف قصة رد الاعتبار الذكية الجديدة...")
    story = generate_karma_story(channel_cfg=ch_cfg, api_key=groq_key, memory=memory)

    ch_out = out_dir / channel_id
    work_dir = ch_out / "_work"
    shutil.rmtree(work_dir, ignore_errors=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    print(f"🎙️ [{channel_id}] تسجيل السرد الصوتي وضبط السرعة الفيروسية...")
    raw_voice = _synth_single_line(story["story_text"], ch_cfg["voice"], work_dir / "raw_voice")
    paced_mp3 = tighten_and_pace_voice(
        raw_voice,
        work_dir / "paced_voice.mp3",
        speed=float(ch_cfg["voice"].get("speed", 1.08)),
    )

    print(f"⚡ [{channel_id}] مزامنة الكلمات بالمللي ثانية عبر Whisper...")
    words = extract_whisper_words(paced_mp3, groq_key=groq_key, language=ch_cfg["language"])

    print(f"🎥 [{channel_id}] تجهيز الفيديوهات المريحة للأعصاب 1080p والمونتاج...")
    bg_clips = fetch_satisfying_clips(
        cache_dir=CLIPS_CACHE,
        needed_count=4,
        pexels_key=os.environ.get("PEXELS_API_KEY", "").strip(),
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    mp4_path = ch_out / f"{channel_id}_{stamp}.mp4"
    assemble_viral_satisfying_short(
        paced_audio_mp3=paced_mp3,
        words=words,
        bg_clips=bg_clips,
        out_mp4=mp4_path,
    )

    save_memory(MEMORY_PATH, memory)
    shutil.rmtree(work_dir, ignore_errors=True)

    meta_info = {
        "channel_id": channel_id,
        "brand_name": ch_cfg["brand_name"],
        "youtube_title": story.get("youtube_title"),
        "description": story.get("description"),
        "first_comment": story.get("first_comment"),
        "video_file": str(mp4_path),
    }
    (ch_out / f"{channel_id}_{stamp}_meta.json").write_text(
        json.dumps(meta_info, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if publish:
        meta_info["publish_result"] = publish_channel_episode(
            channel_cfg=ch_cfg,
            script_data=story,
            video_path=mp4_path,
            thumbnail_path=None,
        )

    print(f"✅ [{channel_id}] جاهز: {mp4_path.name}")
    return meta_info


def main() -> None:
    parser = argparse.ArgumentParser(description="Viral Satisfying Karma Storytime Empire V3.0")
    parser.add_argument("--channel", default="all", choices=["all", *CHANNELS.keys()])
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
            publish=args.publish,
        )


if __name__ == "__main__":
    main()
