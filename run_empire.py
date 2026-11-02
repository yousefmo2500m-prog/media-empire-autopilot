#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
المشغّل الرئيسي لإمبراطورية القنوات الأربع V9.0 (Neuro-Psychological Retention + 1:1 Visual Sync + Chapters + Custom Thumbnail)
ينتج وينشر يومياً لكل قناة بشكل مستقل 100%:
1) فيلم حلقة كامل (+16 دقيقة، 16:9 HD، 12 مشهداً مخصصاً بدون تكرار أي صورة + تقسيم فصول بالدقيقة والثانية + غلاف يوتيوب ناري) -> يوتيوب + فيسبوك.
2) الشورت العميق الأول (~115–135 ثانية، 9:16 رأسي كامل بدون قص جانبي، يقطع فجأة عند الذروة النارية الأولى) -> YouTube Shorts + TikTok.
3) الشورت العميق الثاني (~115–135 ثانية، 9:16 رأسي كامل بدون قص جانبي، يقطع فجأة عند ذروة منتصف القصة، مجدول بعد 3 ساعات) -> YouTube Shorts + TikTok.
"""

import argparse
import concurrent.futures
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from channels_config import CHANNELS
from cinema_funnel_renderer import assemble_cliffhanger_short_mp4, assemble_long_episode_mp4
from empire_publisher import publish_full_and_short_funnel
from sound_studio import format_mmss, get_audio_duration, synthesize_episode_and_climax_shorts
from story_brain import generate_full_episode_and_short, load_memory, save_memory
from story_visuals import generate_all_episode_visuals

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
        print(f"⏭️ [{channel_id}] تخطّي مؤقت (بانتظار {prefix}_ZERNIO_KEY).")
        return {"channel": channel_id, "status": "waiting_for_key"}

    memory = load_memory(MEMORY_PATH)
    print(f"🧠 [{channel_id}] تأليف الرواية النفسية الكاملة (12 مشهداً متسلسلاً) + غلاف اليوتيوب + 2 شورتس ذروة...")
    episode = generate_full_episode_and_short(channel_cfg=ch_cfg, api_key=groq_key, memory=memory)

    ch_out = out_dir / channel_id
    work_dir = ch_out / "_work"
    shutil.rmtree(work_dir, ignore_errors=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    mood = ch_cfg["voice"].get("mood", "mystery")

    print(f"⚡ [{channel_id}] تشغيل متوازٍ لـ (23 مشهداً بصرياً مخصصاً + الغلاف) بالتزامن مع (تسجيل الصوت البشري ومزامنة Whisper)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        fut_vis = ex.submit(
            generate_all_episode_visuals,
            episode["scene_prompts"],
            episode["short_1_vertical_prompts"],
            episode["short_2_vertical_prompts"],
            episode["thumbnail_prompt"],
            episode["thumbnail_hook_text"],
            episode["thumbnail_badge_text"],
            is_ar,
            work_dir / "visuals",
            mood,
        )
        fut_aud = ex.submit(
            synthesize_episode_and_climax_shorts,
            episode,
            ch_cfg["voice"],
            groq_key,
            ch_cfg["language"],
            work_dir / "audio",
            float(ch_cfg.get("min_duration_sec", 950)),
        )
        vis_pack = fut_vis.result()
        aud_pack = fut_aud.result()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    long_mp4 = ch_out / f"{channel_id}_full_{stamp}.mp4"
    short1_mp4 = ch_out / f"{channel_id}_short1_{stamp}.mp4"
    short2_mp4 = ch_out / f"{channel_id}_short2_{stamp}.mp4"
    thumb_jpg = ch_out / f"{channel_id}_thumb_{stamp}.jpg"
    shutil.copy2(vis_pack["thumbnail"], thumb_jpg)

    print(f"🎬 [{channel_id}] مونتاج الفيلم الكامل 16:9 HD (12 مشهداً مقفولة 1:1 بدون أي تكرار + فصول المشاهد)...")
    assemble_long_episode_mp4(
        master_audio_mp3=aud_pack["master_mp3"],
        scenes=vis_pack["long_scenes"],
        subtitles=aud_pack["subtitles"],
        scene_timings=aud_pack["scene_timings"],
        brand_name=ch_cfg["brand_name"],
        is_arabic=is_ar,
        out_mp4=long_mp4,
        work_dir=work_dir / "vid_long",
    )

    print(f"🔥 [{channel_id}] مونتاج الشورت العميق الأول 9:16 (صورة رأسية كاملة بدون قص + توقف مفاجئ في قمة الذروة)...")
    assemble_cliffhanger_short_mp4(
        short_audio_mp3=aud_pack["short_1_mp3"],
        words=aud_pack["short_1_words"],
        vertical_scenes=vis_pack["short_1_scenes"],
        cta_banner=ch_cfg["cta_banner"],
        is_arabic=is_ar,
        out_mp4=short1_mp4,
        work_dir=work_dir / "vid_short1",
    )

    print(f"🔥 [{channel_id}] مونتاج الشورت العميق الثاني 9:16 (صورة رأسية كاملة بدون قص + ذروة منتصف القصة)...")
    assemble_cliffhanger_short_mp4(
        short_audio_mp3=aud_pack["short_2_mp3"],
        words=aud_pack["short_2_words"],
        vertical_scenes=vis_pack["short_2_scenes"],
        cta_banner=ch_cfg["cta_banner"],
        is_arabic=is_ar,
        out_mp4=short2_mp4,
        work_dir=work_dir / "vid_short2",
    )

    long_dur = get_audio_duration(long_mp4)
    sh1_dur = get_audio_duration(short1_mp4)
    sh2_dur = get_audio_duration(short2_mp4)
    print(
        f"📊 [{channel_id}] الأطوال النهائية -> الفيلم الكامل: {format_mmss(long_dur)} | "
        f"الشورت 1: {format_mmss(sh1_dur)} | الشورت 2: {format_mmss(sh2_dur)}"
    )

    save_memory(MEMORY_PATH, memory)
    shutil.rmtree(work_dir, ignore_errors=True)

    meta = {
        "channel_id": channel_id,
        "brand_name": ch_cfg["brand_name"],
        "youtube_title": episode["youtube_title"],
        "thumbnail_hook_text": episode["thumbnail_hook_text"],
        "short_1_title": episode["short_1_title"],
        "short_2_title": episode["short_2_title"],
        "durations_sec": {"long": round(long_dur, 1), "short_1": round(sh1_dur, 1), "short_2": round(sh2_dur, 1)},
        "chapters": [
            {
                "scene_num": st["scene_num"],
                "scene_title": st["scene_title"],
                "from": format_mmss(st["start"]),
                "to": format_mmss(st["end"]),
            }
            for st in aud_pack["scene_timings"]
        ],
        "long_video": str(long_mp4),
        "short_1_video": str(short1_mp4),
        "short_2_video": str(short2_mp4),
        "thumbnail": str(thumb_jpg),
    }

    if publish:
        meta["publish_result"] = publish_full_and_short_funnel(
            channel_cfg=ch_cfg,
            episode_data=episode,
            scene_timings=aud_pack["scene_timings"],
            long_video_path=long_mp4,
            short_video_path=short1_mp4,
            short_2_video_path=short2_mp4,
            thumbnail_path=thumb_jpg,
        )
        # تنظيف ملفات الفيديو الكبيرة بعد النشر مباشرة للحفاظ على نظافة الخادم
        for fp in (long_mp4, short1_mp4, short2_mp4):
            fp.unlink(missing_ok=True)

    (ch_out / f"{channel_id}_{stamp}_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"✅ [{channel_id}] اكتمل إنتاج ونشر منظومة V9.0 بالكامل بنجاح!")
    return meta


def main() -> None:
    parser = argparse.ArgumentParser(description="4-Channel V9.0 Psychological Thriller + 1:1 Visuals + Chapters + Thumbnail Engine")
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
