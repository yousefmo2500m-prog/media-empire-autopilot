#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
المشغّل الرئيسي لإمبراطورية القنوات الأربع V7.0
ينتج يومياً لكل قناة بشكل مستقل 100%:
1) فيلم حلقة كامل (16–18 دقيقة، 16:9 HD) بمشاهد ذكاء اصطناعي مخصصة وترجمة مزامنة -> يوتيوب + فيسبوك.
2) الشورت التشويقي الأول (Short #1 — 9:16 HD) من صدمة البداية -> YouTube Shorts + TikTok (مع رابط الفيلم الكامل في أول تعليق).
3) الشورت التشويقي الثاني (Short #2 — 9:16 HD) من المفاجأة الثانية بقلب القصة -> YouTube Shorts + TikTok بعد 3 ساعات (مع نفس رابط الفيلم الكامل في أول تعليق).
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
    print(f"✍️ [{channel_id}] تأليف الفيلم الكامل (+15 دقيقة) + 2 شورتس تشويقيين لنفس الحلقة...")
    episode = generate_full_episode_and_short(channel_cfg=ch_cfg, api_key=groq_key, memory=memory)

    ch_out = out_dir / channel_id
    work_dir = ch_out / "_work"
    shutil.rmtree(work_dir, ignore_errors=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    mood = "mystery" if ("conan" in ch_cfg["niche"] or "mystery" in ch_cfg["niche"] or "detective" in ch_cfg["niche"]) else "warm"
    ch_cfg["voice"]["mood"] = mood
    print(f"🎨 [{channel_id}] توليد الـ 8 مشاهد السينمائية المخصصة لأحداث القصة بالذكاء الاصطناعي...")
    scenes = prepare_episode_scenes(episode["scene_prompts"], work_dir / "scenes", mood=mood)

    print(f"🎙️ [{channel_id}] تسجيل الصوت الكامل للحلقة (+15 دقيقة)...")
    master_mp3, subs, markers = synthesize_long_episode_audio(
        episode["acts"],
        ch_cfg["voice"],
        work_dir / "audio_long",
        min_duration_sec=float(ch_cfg.get("min_duration_sec", 940)),
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    long_mp4 = ch_out / f"{channel_id}_full_{stamp}.mp4"
    short1_mp4 = ch_out / f"{channel_id}_short1_{stamp}.mp4"
    short2_mp4 = ch_out / f"{channel_id}_short2_{stamp}.mp4"

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

    print(f"⚡ [{channel_id}] تسجيل ومونتاج الشورت التشويقي الأول (Short #1) 9:16...")
    sh1_mp3, sh1_words = synthesize_short_audio_and_words(
        episode["short_1_narration"],
        ch_cfg["voice"],
        groq_key,
        ch_cfg["language"],
        work_dir / "audio_short1",
    )
    assemble_cliffhanger_short_mp4(
        short_audio_mp3=sh1_mp3,
        words=sh1_words,
        scenes=scenes[:4] if len(scenes) >= 4 else scenes,
        cta_banner=ch_cfg["cta_banner"],
        is_arabic=is_ar,
        out_mp4=short1_mp4,
        work_dir=work_dir / "vid_short1",
    )

    print(f"⚡ [{channel_id}] تسجيل ومونتاج الشورت التشويقي الثاني (Short #2) 9:16...")
    sh2_mp3, sh2_words = synthesize_short_audio_and_words(
        episode["short_2_narration"],
        ch_cfg["voice"],
        groq_key,
        ch_cfg["language"],
        work_dir / "audio_short2",
    )
    scenes_sh2 = (scenes[4:] + scenes[:2]) if len(scenes) >= 6 else scenes[::-1]
    assemble_cliffhanger_short_mp4(
        short_audio_mp3=sh2_mp3,
        words=sh2_words,
        scenes=scenes_sh2,
        cta_banner=ch_cfg["cta_banner"],
        is_arabic=is_ar,
        out_mp4=short2_mp4,
        work_dir=work_dir / "vid_short2",
    )

    save_memory(MEMORY_PATH, memory)
    shutil.rmtree(work_dir, ignore_errors=True)

    meta = {
        "channel_id": channel_id,
        "brand_name": ch_cfg["brand_name"],
        "youtube_title": episode["youtube_title"],
        "short_1_title": episode["short_1_title"],
        "short_2_title": episode["short_2_title"],
        "long_video": str(long_mp4),
        "short_1_video": str(short1_mp4),
        "short_2_video": str(short2_mp4),
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
            short_video_path=short1_mp4,
            short_2_video_path=short2_mp4,
        )

    print(f"✅ [{channel_id}] اكتمل إنتاج الفيلم الطويل + 2 شورتس تشويقيين بنجاح!")
    return meta


def main() -> None:
    parser = argparse.ArgumentParser(description="4-Channel 15+ Min Movie + 2x Daily Shorts/TikTok Funnel Engine V7.0")
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
