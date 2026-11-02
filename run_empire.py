# -*- coding: utf-8 -*-
"""
المشغّل الرئيسي لإمبراطورية القنوات الأربع V10.0 (Algorithm & 8-Second FLUX Cinema Masterpiece):
1. تأليف سيناريو إثارة نفسية واقعي / تحقيق ذكي + حزمة الخوارزميات والسيو الكاملة لعام 2026.
2. تسجيل صوت بشري حقيقي 100% (صفر صوت آلي edge_tts!) وتقطيع الحلقة الكاملة والشورتين إلى نوافذ زمنية دقيقة كل ~8 ثوانٍ.
3. توليد وصف بصري فريد لكل نافذة 8 ثوانٍ مطابق للكلام المنطوق فيها، ثم رسم ~145 صورة FLUX 8K فريدة بدون تكرار أي صورة مرتين + غلاف يوتيوب ناري عالي النقر (1280x720).
4. مونتاج متوازٍ فائق السرعة للفيديو الكامل (16:9) والشورتين الطوليين الكاملين (9:16 بدون قص) + نشر خوارزمي متكامل بالتاجات والفصول وأول تعليق.
"""

import argparse
import hashlib
import os
import shutil
import tempfile
from pathlib import Path

from channels_config import CHANNELS
from cinema_funnel_renderer import render_long_episode_mp4, render_vertical_short_mp4
from empire_publisher import publish_channel_funnel
from sound_studio import get_audio_duration, synthesize_episode_and_climax_shorts
from story_brain import (
    generate_8sec_shot_prompts,
    generate_full_episode_and_short,
    load_memory,
    save_memory,
)
from story_visuals import build_viral_youtube_thumbnail, generate_8sec_shots_batch

BASE_DIR = Path(__file__).resolve().parent
MEMORY_PATH = BASE_DIR / "state" / "empire_memory.json"


def run_single_channel(channel_id: str, dry_run: bool = False) -> None:
    if channel_id not in CHANNELS:
        raise ValueError(f"معرف قناة غير معروف: {channel_id}")

    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not groq_key:
        raise RuntimeError("GROQ_API_KEY غير متوفر في البيئة.")

    cfg = CHANNELS[channel_id]
    memory = load_memory(MEMORY_PATH)
    shot_interval = float(cfg.get("shot_interval_sec", 8.0))

    print(f"🎬 [{cfg['brand_name']}] 1/6 تأليف سيناريو واقعي نفسي + حزمة خوارزميات يوتيوب وتيك توك V10.0...")
    episode = generate_full_episode_and_short(cfg, groq_key, memory)
    print(f"   ✅ العنوان: {episode['youtube_title']} | الغلاف: {episode['thumbnail_hook_text']}")

    seed_base = int(hashlib.md5(episode["youtube_title"].encode("utf-8")).hexdigest()[:6], 16)
    tmp_root = Path(tempfile.mkdtemp(prefix=f"v10_{channel_id}_"))

    try:
        print(f"🎙️ [{cfg['brand_name']}] 2/6 تسجيل الصوت البشري الحقيقي 100% ({cfg['voice']['gemini_voice']}) وتقسيم نوافذ الـ 8 ثوانٍ...")
        audio_pack = synthesize_episode_and_climax_shorts(
            episode=episode,
            voice_cfg=cfg["voice"],
            groq_key=groq_key,
            language=cfg["language"],
            work_dir=tmp_root / "audio",
            min_duration_sec=float(cfg["min_duration_sec"]),
            shot_interval_sec=shot_interval,
        )
        long_dur = get_audio_duration(audio_pack["master_mp3"])
        sh1_dur = get_audio_duration(audio_pack["short_1_mp3"])
        sh2_dur = get_audio_duration(audio_pack["short_2_mp3"])
        long_wins = audio_pack["long_8s_windows"]
        sh1_wins = audio_pack["short_1_windows"]
        sh2_wins = audio_pack["short_2_windows"]
        print(
            f"   ✅ الصوت البشري جاهز: الفيلم {long_dur/60:.2f} دقيقة ({len(long_wins)} لقطة × ~8ث) | "
            f"شورت #1 ({sh1_dur:.1f}ث / {len(sh1_wins)} لقطة) | شورت #2 ({sh2_dur:.1f}ث / {len(sh2_wins)} لقطة)"
        )

        print(f"🧠 [{cfg['brand_name']}] 3/6 كتابة مشاهد بصرية مخصصة لكل نافذة 8 ثوانٍ مطابقة للكلام المنطوق...")
        long_prompts = generate_8sec_shot_prompts(
            windows=long_wins,
            character_visual_anchor=episode["character_visual_anchor"],
            story_title=episode["youtube_title"],
            api_key=groq_key,
            is_vertical=False,
        )
        sh1_prompts = generate_8sec_shot_prompts(
            windows=sh1_wins,
            character_visual_anchor=episode["character_visual_anchor"],
            story_title=episode["short_1_title"],
            api_key=groq_key,
            is_vertical=True,
        )
        sh2_prompts = generate_8sec_shot_prompts(
            windows=sh2_wins,
            character_visual_anchor=episode["character_visual_anchor"],
            story_title=episode["short_2_title"],
            api_key=groq_key,
            is_vertical=True,
        )

        total_unique_imgs = len(long_prompts) + len(sh1_prompts) + len(sh2_prompts) + 1
        print(f"🎨 [{cfg['brand_name']}] 4/6 رسم الغلاف الناري + {total_unique_imgs - 1} صورة FLUX سينمائية فريدة بدون أي تكرار...", flush=True)
        thumb_jpg = build_viral_youtube_thumbnail(
            prompt=episode["thumbnail_prompt"],
            hook_text=episode["thumbnail_hook_text"],
            badge_text=episode["thumbnail_badge_text"],
            brand_name=cfg["brand_name"],
            language=cfg["language"],
            out_path=tmp_root / f"{channel_id}_thumbnail_1280x720.jpg",
            seed=seed_base + 777,
        )
        sh1_imgs = generate_8sec_shots_batch(
            prompts=sh1_prompts,
            out_dir=tmp_root / "shots_sh1_9x16",
            prefix="sh1_9x16",
            width=720,
            height=1280,
            seed_base=seed_base + 20000,
            max_workers=6,
        )
        sh2_imgs = generate_8sec_shots_batch(
            prompts=sh2_prompts,
            out_dir=tmp_root / "shots_sh2_9x16",
            prefix="sh2_9x16",
            width=720,
            height=1280,
            seed_base=seed_base + 40000,
            max_workers=6,
        )
        long_imgs = generate_8sec_shots_batch(
            prompts=long_prompts,
            out_dir=tmp_root / "shots_16x9",
            prefix="long16x9",
            width=1280,
            height=720,
            seed_base=seed_base,
            max_workers=6,
        )

        print(f"🎞️ [{cfg['brand_name']}] 5/6 مونتاج متوازٍ (صورة جديدة كل ~8 ثوانٍ بلا تكرار) للفيلم الطويل والشورتين...")
        long_mp4 = render_long_episode_mp4(
            shot_images=long_imgs,
            shot_windows=long_wins,
            audio_mp3=audio_pack["master_mp3"],
            subtitles=audio_pack["subtitles"],
            brand_name=cfg["brand_name"],
            out_mp4=tmp_root / f"{channel_id}_full_episode.mp4",
            work_dir=tmp_root / "render_long",
        )
        short_1_mp4 = render_vertical_short_mp4(
            vertical_images=sh1_imgs,
            short_windows=sh1_wins,
            short_mp3=audio_pack["short_1_mp3"],
            short_words=audio_pack["short_1_words"],
            brand_name=cfg["brand_name"],
            cta_banner=episode["cta_banner"],
            out_mp4=tmp_root / f"{channel_id}_climax_short_1.mp4",
            work_dir=tmp_root / "render_short_1",
        )
        short_2_mp4 = render_vertical_short_mp4(
            vertical_images=sh2_imgs,
            short_windows=sh2_wins,
            short_mp3=audio_pack["short_2_mp3"],
            short_words=audio_pack["short_2_words"],
            brand_name=cfg["brand_name"],
            cta_banner=episode["cta_banner"],
            out_mp4=tmp_root / f"{channel_id}_climax_short_2.mp4",
            work_dir=tmp_root / "render_short_2",
        )

        if dry_run:
            out_dir = Path("/tmp/empire_v10_preview")
            out_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(long_mp4, out_dir / long_mp4.name)
            shutil.copy2(thumb_jpg, out_dir / thumb_jpg.name)
            shutil.copy2(short_1_mp4, out_dir / short_1_mp4.name)
            shutil.copy2(short_2_mp4, out_dir / short_2_mp4.name)
            print(f"✅ [DRY RUN] الملفات جاهزة في {out_dir}")
        else:
            print(f"🚀 [{cfg['brand_name']}] 6/6 النشر الخوارزمي الكامل (غلاف + فصول + تاجات + سؤال تعليقات + شورتين)...")
            pub_res = publish_channel_funnel(
                channel_cfg=cfg,
                episode=episode,
                scene_timings=audio_pack["scene_timings"],
                long_mp4=long_mp4,
                thumbnail_jpg=thumb_jpg,
                short_1_mp4=short_1_mp4,
                short_2_mp4=short_2_mp4,
            )
            print(f"   🎉 نتيجة النشر: {pub_res}")
            save_memory(MEMORY_PATH, memory)
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", required=True, help="معرف القناة أو all")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.channel == "all":
        for cid in CHANNELS:
            run_single_channel(cid, dry_run=args.dry_run)
    else:
        run_single_channel(args.channel, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
