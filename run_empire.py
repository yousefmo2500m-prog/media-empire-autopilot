#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
المشغّل الرئيسي لإمبراطورية القنوات الأربع V4.0
ينتج لكل قناة:
1) فيلم حلقة كاملة (15.5–20 دقيقة، 16:9 HD) بمشاهد بصرية تعبّر عن أحداث القصة وترجمة مزامنة -> يوتيوب + فيسبوك.
2) شورت تشويقي حماسي (9:16 HD) يقف عند الذروة ويوجّه المشاهد لرابط الفيديو الكامل في أول تعليق -> YouTube Shorts + TikTok.
"""

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from channels_config import CHANNELS
from cinema_funnel_renderer import assemble_cliffhanger_short_mp4, assemble_long_episode_mp4
from empire_publisher import publish_full_and_short_funnel
from sound_studio import synthesize_long_episode_audio, synthesize_short_audio_and_words
from story_brain import generate_full_episode_and_short, load_memory, save_memory
from story_visuals import prepare_episode_scenes

BASE_DIR = Path(__file__).resolve().parent
MEMORY_PATH = BASE_DIR / "state" / "empire_memory.json"


def run_single_channel(
    channel_id: str,
    groq_key: str,
    out_dir: Path,
    publish: bool = False,
) -> dict:
    ch_cfg = CHANNELS[channel_id]
    prefix = ch_cfg["env_prefix"]
    is_ar = ch_cfg["language"] == "ar"

    if publish and not os.environ.get(f"{prefix}_ZERNIO_KEY", "").strip():
        print(f"⏭️ [{channel_id}] تخطّي مؤقت (بانتظار إضافة Secret باسم {prefix}_ZERNIO_KEY).")
        return {"channel": channel_id, "status": "waiting_for_key"}

    memory = load_memory(MEMORY_PATH)
    print(f"✍️ [{channel_id}] تأليف الحلقة الكاملة (5 فصول / +15 دقيقة) + نص الشورت التشويقي...")
    episode = generate_full_episode_and_short(channel_cfg=ch_cfg, api_key=groq_key, memory=memory)

    ch_out = out_dir / channel_id
    work_dir = ch_out / "_work"
    shutil.rmtree(work_dir, ignore_errors=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    mood = "mystery" if "mystery" in ch_cfg["niche"] else "warm"
    print(f"🎨 [{channel_id}] تجهيز الـ 8 مشاهد البصرية المعبرة عن أحداث القصة...")
    scenes = prepare_episode_scenes(episode["scene_prompts"], work_dir / "scenes", mood=mood)

    print(f"🎙️ [{channel_id}] تسجيل الصوت الكامل للحلقة (+15 دقيقة)...")
    master_mp3, subs, markers = synthesize_long_episode_audio(
        episode["acts"],
        ch_cfg["voice"],
        work_dir / "audio_long",
        min_duration_sec=float(ch_cfg.get("min_duration_sec", 920)),
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    long_mp4 = ch_out / f"{channel_id}_full_{stamp}.mp4"
    short_mp4 = ch_out / f"{channel_id}_short_{stamp}.mp4"

    print(f"🎬 [{channel_id}] مونتاج الفيلم الكامل 16:9...")
    assemble_long_episode_mp4(
        master_audio_mp3=master_mp3,
        scenes=scenes,
        subtitles=subs,
        act_markers=markers,
        brand_name=ch_cfg["brand_name"],
        is_arabic=is_ar,
        out_mp4=long_mp4,
        work_dir=work_dir / "vid_long",
    )

    print(f"⚡ [{channel_id}] تسجيل ومونتاج الشورت الحماسي 9:16 ليوتيوب شورتس وتيك توك...")
    sh_mp3, sh_words = synthesize_short_audio_and_words(
        episode["short_narration"],
        ch_cfg["voice"],
        groq_key,
        ch_cfg["language"],
        work_dir / "audio_short",
    )
    assemble_cliffhanger_short_mp4(
        short_audio_mp3=sh_mp3,
        words=sh_words,
        scenes=scenes,
        cta_banner=ch_cfg["cta_banner"],
        is_arabic=is_ar,
        out_mp4=short_mp4,
        work_dir=work_dir / "vid_short",
    )

    save_memory(MEMORY_PATH, memory)
    shutil.rmtree(work_dir, ignore_errors=True)

    meta = {
        "channel_id": channel_id,
        "brand_name": ch_cfg["brand_name"],
        "youtube_title": episode["youtube_title"],
        "short_title": episode["short_title"],
        "long_video": str(long_mp4),
        "short_video": str(short_mp4),
    }
    (ch_out / f"{channel_id}_{stamp}_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if publish:
        meta["publish_result"] = publish_full_and_short_funnel(
            channel_cfg=ch_cfg,
            episode_data=episode,
            long_video_path=long_mp4,
            short_video_path=short_mp4,
        )

    print(f"✅ [{channel_id}] اكتمل إنتاج الفيلم الطويل + الشورت التشويقي بنجاح!")
    return meta


def main() -> None:
    parser = argparse.ArgumentParser(description="4-Channel 15+ Min Movie + Shorts/TikTok Funnel Engine V4.0")
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
