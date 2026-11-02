# -*- coding: utf-8 -*-
"""
المايسترو الرئيسي V11.0 — محرك القنوات الأربع المستقل 100% (مقدمة تشويقية إجبارية + 0% غلوشة + خوارزميات 2026)
لكل قناة يومياً:
  1) كتابة سيناريو درامي عميق (>15 دقيقة) يبدأ بمقدمة تشويقية نارية (Cold-Open Teaser) + هوك افتتاحي لكل شورت + SEO دلالي وفصول
  2) إنتاج صوت استوديو بشري نقي 100% (Kore / Aoede / Charon — صفر صوت آلي) مع مؤثرات انتقال درامية
  3) توليد صورة مصغرة سينمائية (1280x720) + مشاهد فوتوغرافية حادة 100% بدون أي غلوشة (تقطيع 4.5ث في المقدمة و8ث في الحلقة، و5.8ث طولي 9:16 للشورتس)
  4) مونتاج احترافي بشريط المقدمة التشويقية وبطاقات عناوين المشاهد التفاعلية (Chapter Cards) وكابشن كاريوكي
  5) النشر التلقائي المتكامل على يوتيوب + فيسبوك + تيك توك مع ربط الشورتات بالحلقة الكاملة وسؤال التفاعل في أول تعليق
"""

import argparse
import json
import os
import re
import shutil
import sys
import traceback
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

MEMORY_FILE = Path(__file__).resolve().parent / "state" / "empire_memory.json"


def _clean_hook_banner(raw_title: str) -> str:
    no_tags = re.sub(r"#\S+", "", raw_title).strip(" -—|")
    words = no_tags.split()
    return " ".join(words[:7])[:48]


def run_single_channel(ch_id: str, dry_run: bool = False, keep_output_dir: str = "") -> None:
    if ch_id not in CHANNELS:
        raise ValueError(f"معرف القناة غير معروف: {ch_id}")

    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not groq_key:
        raise RuntimeError("مفتاح GROQ_API_KEY غير متوفر في البيئة!")

    ch = CHANNELS[ch_id]
    work_root = Path("/tmp/media_empire_work") / ch_id
    if work_root.exists():
        shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True, exist_ok=True)

    out_dir = Path(keep_output_dir) if keep_output_dir else (work_root / "out")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 76, flush=True)
    print(f"بدء الإنتاج السينمائي الاحترافي V11.0 لقناة: {ch['brand_name']} ({ch_id})", flush=True)
    print("=" * 76, flush=True)

    # 1) توليد القصة الكاملة + المقدمة التشويقية النارية + حزمة الخوارزميات وحفظ الذاكرة
    memory = load_memory(MEMORY_FILE)
    ep = generate_full_episode_and_short(channel_cfg=ch, api_key=groq_key, memory=memory)
    save_memory(MEMORY_FILE, memory)

    teaser_words = len(str(ep.get("teaser_intro", "")).split())
    total_words = teaser_words + sum(len(s.get("narration", "").split()) for s in ep["scenes"])
    print(
        f"[{ch_id}] عنوان الحلقة: {ep['youtube_title']} | إجمالي الكلمات: {total_words} "
        f"| المقدمة التشويقية: {teaser_words} كلمة",
        flush=True,
    )

    # 2) إنتاج الصوت البشري النقي 100% + نوافذ التقطيع البصري الديناميكي
    audio_pack = synthesize_episode_and_climax_shorts(
        episode=ep,
        voice_cfg=ch["voice"],
        groq_key=groq_key,
        language=ch["language"],
        work_dir=work_root / "audio",
        min_duration_sec=float(ch.get("min_duration_sec", 945.0)),
        shot_interval_sec=float(ch.get("shot_interval_sec", 8.0)),
    )
    total_dur = get_audio_duration(audio_pack["master_mp3"])
    s1_dur = get_audio_duration(audio_pack["short_1_mp3"])
    s2_dur = get_audio_duration(audio_pack["short_2_mp3"])
    n_long_shots = len(audio_pack["long_8s_windows"])
    n_s1_shots = len(audio_pack["short_1_windows"])
    n_s2_shots = len(audio_pack["short_2_windows"])
    print(
        f"[{ch_id}] مدة الحلقة الكاملة: {total_dur/60:.2f} دقيقة "
        f"(المقدمة التشويقية حتى {audio_pack['teaser_end_sec']:.1f}ث | {n_long_shots} لقطة حادة فريدة) | "
        f"الشورت 1: {s1_dur:.1f}ث ({n_s1_shots} لقطة 9:16) | "
        f"الشورت 2: {s2_dur:.1f}ث ({n_s2_shots} لقطة 9:16)",
        flush=True,
    )

    # 3) صياغة الأوصاف البصرية الفوتوغرافية الدقيقة لكل نافذة (صفر تكرار وصفر غلوشة)
    print(f"[{ch_id}] صياغة الأوصاف البصرية الفوتوغرافية الدقيقة ({n_long_shots + n_s1_shots + n_s2_shots} لقطة)...", flush=True)
    long_prompts = generate_8sec_shot_prompts(
        windows=audio_pack["long_8s_windows"],
        character_visual_anchor=ep["character_visual_anchor"],
        story_title=ep["youtube_title"],
        api_key=groq_key,
        is_vertical=False,
    )
    s1_prompts = generate_8sec_shot_prompts(
        windows=audio_pack["short_1_windows"],
        character_visual_anchor=ep["character_visual_anchor"],
        story_title=ep["youtube_title"],
        api_key=groq_key,
        is_vertical=True,
    )
    s2_prompts = generate_8sec_shot_prompts(
        windows=audio_pack["short_2_windows"],
        character_visual_anchor=ep["character_visual_anchor"],
        story_title=ep["youtube_title"],
        api_key=groq_key,
        is_vertical=True,
    )

    seed_base = abs(hash(ep["youtube_title"])) % 80000 + 100

    # 4) توليد الصورة المصغرة السينمائية عالية النقر (1280x720)
    print(f"[{ch_id}] توليد وتصميم الصورة المصغرة السينمائية (1280x720)...", flush=True)
    thumb_jpg = build_viral_youtube_thumbnail(
        prompt=ep["thumbnail_prompt"],
        hook_text=ep["thumbnail_hook_text"],
        badge_text=ep["thumbnail_badge_text"],
        brand_name=ch["brand_name"],
        language=ch["language"],
        out_path=out_dir / f"{ch_id}_thumb.jpg",
        seed=seed_base + 77,
    )

    # 5) توليد اللقطات الحادة 100% للحلقة الكاملة والمقطعين الطوليين (صفر غلوشة!)
    print(f"[{ch_id}] توليد {n_long_shots} صورة فوتوغرافية حادة 16:9 للحلقة الكاملة (بدون أي غلوشة)...", flush=True)
    long_imgs = generate_8sec_shots_batch(
        prompts=long_prompts,
        out_dir=work_root / "img_long",
        prefix="lshot",
        width=1280,
        height=720,
        seed_base=seed_base + 200,
        max_workers=4,
    )

    print(f"[{ch_id}] توليد {n_s1_shots + n_s2_shots} صورة طولية حادة 9:16 للشورتس (بدون قص أو غلوشة)...", flush=True)
    s1_imgs = generate_8sec_shots_batch(
        prompts=s1_prompts,
        out_dir=work_root / "img_s1",
        prefix="s1shot",
        width=720,
        height=1280,
        seed_base=seed_base + 3200,
        max_workers=4,
    )
    s2_imgs = generate_8sec_shots_batch(
        prompts=s2_prompts,
        out_dir=work_root / "img_s2",
        prefix="s2shot",
        width=720,
        height=1280,
        seed_base=seed_base + 6200,
        max_workers=4,
    )

    long_mp4 = out_dir / f"{ch_id}_full_episode.mp4"
    s1_mp4 = out_dir / f"{ch_id}_short_1.mp4"
    s2_mp4 = out_dir / f"{ch_id}_short_2.mp4"

    # 6) المونتاج السينمائي للحلقة الكاملة (شريط المقدمة التشويقية + بطاقات الفصول + 6 حركات كاميرا)
    print(f"[{ch_id}] مونتاج الحلقة الكاملة HD (1280x720) مع شريط المقدمة التشويقية وبطاقات الفصول...", flush=True)
    render_long_episode_mp4(
        shot_images=long_imgs,
        shot_windows=audio_pack["long_8s_windows"],
        audio_mp3=audio_pack["master_mp3"],
        subtitles=audio_pack["subtitles"],
        scene_timings=audio_pack["scene_timings"],
        teaser_banner=str(ep.get("teaser_banner_text", "")),
        teaser_end_sec=float(audio_pack["teaser_end_sec"]),
        brand_name=ch["brand_name"],
        out_mp4=long_mp4,
        work_dir=work_root / "render_long",
    )

    # 7) المونتاج السينمائي لمقطعي الشورتس الطوليين 9:16 (لافتة هوك افتتاحية + تقطيع سريع + CTA)
    s1_hook_banner = _clean_hook_banner(str(ep.get("short_1_title") or ep["youtube_title"]))
    s2_hook_banner = _clean_hook_banner(str(ep.get("short_2_title") or ep["youtube_title"]))

    print(f"[{ch_id}] مونتاج الشورت التشويقي الأول (720x1280 كادر طولي كامل)...", flush=True)
    render_vertical_short_mp4(
        vertical_images=s1_imgs,
        short_windows=audio_pack["short_1_windows"],
        short_mp3=audio_pack["short_1_mp3"],
        short_words=audio_pack["short_1_words"],
        brand_name=ch["brand_name"],
        hook_banner=s1_hook_banner,
        hook_end_sec=float(audio_pack["short_1_hook_end"]),
        cta_banner=ep["cta_banner"],
        out_mp4=s1_mp4,
        work_dir=work_root / "render_s1",
    )

    print(f"[{ch_id}] مونتاج الشورت التشويقي الثاني (720x1280 كادر طولي كامل)...", flush=True)
    render_vertical_short_mp4(
        vertical_images=s2_imgs,
        short_windows=audio_pack["short_2_windows"],
        short_mp3=audio_pack["short_2_mp3"],
        short_words=audio_pack["short_2_words"],
        brand_name=ch["brand_name"],
        hook_banner=s2_hook_banner,
        hook_end_sec=float(audio_pack["short_2_hook_end"]),
        cta_banner=ep["cta_banner"],
        out_mp4=s2_mp4,
        work_dir=work_root / "render_s2",
    )

    # 8) النشر التلقائي المتكامل (إن لم يكن dry-run)
    if dry_run:
        print(
            f"[{ch_id}] DRY-RUN مكتمل بنجاح:\n"
            f" - Thumbnail: {thumb_jpg} ({thumb_jpg.stat().st_size / 1024:.1f} KB)\n"
            f" - Long MP4 : {long_mp4} ({long_mp4.stat().st_size / (1024*1024):.2f} MB)\n"
            f" - Short 1  : {s1_mp4} ({s1_mp4.stat().st_size / (1024*1024):.2f} MB)\n"
            f" - Short 2  : {s2_mp4} ({s2_mp4.stat().st_size / (1024*1024):.2f} MB)",
            flush=True,
        )
    else:
        pub_res = publish_channel_funnel(
            ch=ch,
            episode_meta=ep,
            scene_timings=audio_pack["scene_timings"],
            long_mp4=long_mp4,
            thumbnail_jpg=thumb_jpg,
            short1_mp4=s1_mp4,
            short2_mp4=s2_mp4,
        )
        print(f"CDN_AUDIT_URLS: {json.dumps(pub_res.get('cdn_urls', {}), ensure_ascii=False)}", flush=True)
        print(f"[{ch_id}] تم النشر بنجاح! رابط الحلقة الكاملة على يوتيوب: {pub_res.get('youtube_watch_url')}", flush=True)

    if not keep_output_dir:
        shutil.rmtree(work_root, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Media Empire Autopilot V11.0")
    parser.add_argument("--channel", type=str, default="all", help="معرف القناة أو all")
    parser.add_argument("--dry-run", action="store_true", help="توليد بدون نشر")
    parser.add_argument("--output-dir", type=str, default="", help="مجلد حفظ المخرجات عند الاختبار")
    args = parser.parse_args()

    targets = list(CHANNELS.keys()) if args.channel == "all" else [args.channel]
    failures = 0
    for cid in targets:
        try:
            run_single_channel(cid, dry_run=args.dry_run, keep_output_dir=args.output_dir)
        except Exception as exc:
            failures += 1
            print(f"[ERROR] فشل تشغيل القناة {cid}: {exc}", file=sys.stderr, flush=True)
            traceback.print_exc()

    if failures == len(targets):
        sys.exit(1)


if __name__ == "__main__":
    main()
