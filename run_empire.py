# -*- coding: utf-8 -*-
"""
المايسترو الرئيسي V13.0 — محرك القنوات الأربع المستقل 100% (1 فيلم كامل + 4 شورتس يومياً + افتتاحية فيديو AI متحرك + كسر حاجز الـ 200 مشاهدة)
لكل قناة يومياً:
  1) كتابة سيناريو درامي عميق (>15 دقيقة) بعنوان بحثي عالي الطلب على يوتيوب + مقدمة تشويقية نارية + 4 شورتس (2 عميقين + 2 خاطفين <55ث)
  2) إنتاج صوت استوديو بشري نقي 100% (Kore / Aoede / Charon — صفر صوت آلي) مع قفلات جدلية باختيارين (١ أو ٢) لتفجير التعليقات
  3) توليد صورة مصغرة سينمائية (1280x720) + مشاهد فوتوغرافية حادة 100% + تحريك الافتتاحية بفيديو ذكاء اصطناعي حقيقي (LTX-Video)
  4) مونتاج احترافي بشريط خطف علوي مرجاني منذ الثانية 0.00 وكابشن كاريوكي سريع وبطاقات فصول للفيلم الطويل
  5) النشر والجدولة التلقائية الموزعة على مدار اليوم (كل 3 ساعات) على يوتيوب + فيسبوك + تيك توك بدون روابط خارجية تكتم وصول تيك توك
"""

import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys
import traceback
from pathlib import Path
from typing import Optional

from channels_config import CHANNELS
from cinema_funnel_renderer import render_long_episode_mp4, render_vertical_short_mp4
from empire_publisher import publish_channel_funnel, resolve_channel_slot_status
from sound_studio import get_audio_duration, synthesize_episode_and_climax_shorts
from story_brain import (
    generate_8sec_shot_prompts,
    generate_full_episode_and_short,
    load_memory,
    save_memory,
)
from story_visuals import (
    _CLIENT_CACHE,
    _EXHAUSTED_SLOTS,
    build_viral_short_cover,
    build_viral_youtube_thumbnail,
    generate_8sec_shots_batch,
    generate_opening_motion_clip,
)

MEMORY_FILE = Path(__file__).resolve().parent / "state" / "empire_memory.json"


def _clean_hook_banner(raw_title: str) -> str:
    no_tags = re.sub(r"#\S+", "", raw_title).strip(" -—|")
    words = no_tags.split()
    return " ".join(words[:7])[:52]


def run_single_channel(
    ch_id: str,
    dry_run: bool = False,
    keep_output_dir: str = "",
    target_slot_utc: Optional[dt.datetime] = None,
) -> None:
    if ch_id not in CHANNELS:
        raise ValueError(f"معرف القناة غير معروف: {ch_id}")

    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not groq_key:
        raise RuntimeError("مفتاح GROQ_API_KEY غير متوفر في البيئة!")

    ch = CHANNELS[ch_id]
    _EXHAUSTED_SLOTS.clear()
    _CLIENT_CACHE.clear()
    work_root = Path("/tmp/media_empire_work") / ch_id
    if work_root.exists():
        shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True, exist_ok=True)

    out_dir = Path(keep_output_dir) if keep_output_dir else (work_root / "out")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 76, flush=True)
    print(f"بدء الإنتاج السينمائي الاحترافي V13.0 لقناة: {ch['brand_name']} ({ch_id})", flush=True)
    print("=" * 76, flush=True)

    # 1) توليد القصة الكاملة + المقدمة التشويقية + بيانات الـ 4 شورتس وحفظ الذاكرة
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

    # 2) إنتاج الصوت البشري النقي 100% للفيلم الطويل والـ 4 شورتس (2 عميقين + 2 خاطفين <55ث)
    audio_pack = synthesize_episode_and_climax_shorts(
        episode=ep,
        voice_cfg=ch["voice"],
        groq_key=groq_key,
        language=ch["language"],
        work_dir=work_root / "audio",
        min_duration_sec=float(ch.get("min_duration_sec", 945.0)),
        shot_interval_sec=float(ch.get("shot_interval_sec", 9.0)),
    )
    total_dur = get_audio_duration(audio_pack["master_mp3"])
    s1_dur = get_audio_duration(audio_pack["short_1_mp3"])
    s2_dur = get_audio_duration(audio_pack["short_2_mp3"])
    s3_dur = get_audio_duration(audio_pack["short_3_mp3"])
    s4_dur = get_audio_duration(audio_pack["short_4_mp3"])
    n_long_shots = len(audio_pack["long_8s_windows"])
    n_s1 = len(audio_pack["short_1_windows"])
    n_s2 = len(audio_pack["short_2_windows"])
    n_s3 = len(audio_pack["short_3_windows"])
    n_s4 = len(audio_pack["short_4_windows"])
    print(
        f"[{ch_id}] الفيلم الطويل: {total_dur/60:.2f}د ({n_long_shots} لقطة) | "
        f"شورت 1 (عميق): {s1_dur:.1f}ث ({n_s1} لقطة) | شورت 2 (عميق): {s2_dur:.1f}ث ({n_s2} لقطة) | "
        f"شورت 3 (خاطف): {s3_dur:.1f}ث ({n_s3} لقطة) | شورت 4 (خاطف): {s4_dur:.1f}ث ({n_s4} لقطة)",
        flush=True,
    )

    # 3) صياغة الأوصاف البصرية الفوتوغرافية الدقيقة لكل نافذة (صفر تكرار وصفر غلوشة)
    total_v_shots = n_s1 + n_s2 + n_s3 + n_s4
    print(f"[{ch_id}] صياغة الأوصاف البصرية الفوتوغرافية ({n_long_shots} أفقي + {total_v_shots} طولي)...", flush=True)
    long_prompts = generate_8sec_shot_prompts(
        windows=audio_pack["long_8s_windows"],
        character_visual_anchor=ep["character_visual_anchor"],
        story_title=ep["youtube_title"],
        api_key=groq_key,
        is_vertical=False,
    )
    all_short_windows = (
        audio_pack["short_1_windows"]
        + audio_pack["short_2_windows"]
        + audio_pack["short_3_windows"]
        + audio_pack["short_4_windows"]
    )
    all_short_prompts = generate_8sec_shot_prompts(
        windows=all_short_windows,
        character_visual_anchor=ep["character_visual_anchor"],
        story_title=ep["youtube_title"],
        api_key=groq_key,
        is_vertical=True,
    )

    seed_base = abs(hash(ep["youtube_title"])) % 80000 + 100

    # 4) توليد اللقطات الحادة 100% للحلقة الكاملة والـ 4 شورتس في دفعة موحدة سريعة
    print(f"[{ch_id}] توليد {n_long_shots} صورة فوتوغرافية حادة 16:9 للفيلم الطويل...", flush=True)
    long_imgs = generate_8sec_shots_batch(
        prompts=long_prompts,
        out_dir=work_root / "img_long",
        prefix="lshot",
        width=1280,
        height=720,
        seed_base=seed_base + 200,
        max_workers=5,
    )

    # 5) توليد الصورة المصغرة السينمائية عالية النقر (1280x720) مع صمام أمان الكادر البطولي الافتتاحي
    print(f"[{ch_id}] توليد وتصميم الصورة المصغرة السينمائية (1280x720)...", flush=True)
    thumb_jpg = build_viral_youtube_thumbnail(
        prompt=ep["thumbnail_prompt"],
        hook_text=ep["thumbnail_hook_text"],
        badge_text=ep["thumbnail_badge_text"],
        brand_name=ch["brand_name"],
        language=ch["language"],
        out_path=out_dir / f"{ch_id}_thumb.jpg",
        seed=seed_base + 77,
        fallback_hero_path=long_imgs[0] if long_imgs else None,
    )

    print(f"[{ch_id}] توليد {total_v_shots} صورة طولية حادة 9:16 للـ 4 شورتس...", flush=True)
    all_v_imgs = generate_8sec_shots_batch(
        prompts=all_short_prompts,
        out_dir=work_root / "img_shorts",
        prefix="vshot",
        width=720,
        height=1280,
        seed_base=seed_base + 3200,
        max_workers=5,
    )
    idx_1 = n_s1
    idx_2 = idx_1 + n_s2
    idx_3 = idx_2 + n_s3
    s1_imgs = all_v_imgs[:idx_1]
    s2_imgs = all_v_imgs[idx_1:idx_2]
    s3_imgs = all_v_imgs[idx_2:idx_3]
    s4_imgs = all_v_imgs[idx_3 : idx_3 + n_s4]

    s1_prompts = all_short_prompts[:idx_1]
    s2_prompts = all_short_prompts[idx_1:idx_2]
    s3_prompts = all_short_prompts[idx_2:idx_3]
    s4_prompts = all_short_prompts[idx_3 : idx_3 + n_s4]

    # 5.5) توليد افتتاحيات فيديو سينمائية متحركة حقيقية 100% (LTX-Video عبر ZeroGPU) لأول ثواني الخطف
    print(f"[{ch_id}] توليد لقطات افتتاحية متحركة حقيقية (LTX-Video AI Motion Hooks)...", flush=True)
    motion_dir = work_root / "motion_hooks"
    s3_motion = generate_opening_motion_clip(
        prompt=s3_prompts[0] if s3_prompts else ep["thumbnail_prompt"],
        first_frame_path=s3_imgs[0] if s3_imgs else None,
        out_mp4=motion_dir / "s3_hook.mp4",
        is_vertical=True,
        duration_sec=4.2,
        seed=seed_base + 11,
        call_idx=0,
    )
    s4_motion = generate_opening_motion_clip(
        prompt=s4_prompts[0] if s4_prompts else ep["thumbnail_prompt"],
        first_frame_path=s4_imgs[0] if s4_imgs else None,
        out_mp4=motion_dir / "s4_hook.mp4",
        is_vertical=True,
        duration_sec=4.2,
        seed=seed_base + 22,
        call_idx=1,
    )
    s1_motion = generate_opening_motion_clip(
        prompt=s1_prompts[0] if s1_prompts else ep["thumbnail_prompt"],
        first_frame_path=s1_imgs[0] if s1_imgs else None,
        out_mp4=motion_dir / "s1_hook.mp4",
        is_vertical=True,
        duration_sec=4.8,
        seed=seed_base + 33,
        call_idx=2,
    )
    s2_motion = generate_opening_motion_clip(
        prompt=s2_prompts[0] if s2_prompts else ep["thumbnail_prompt"],
        first_frame_path=s2_imgs[0] if s2_imgs else None,
        out_mp4=motion_dir / "s2_hook.mp4",
        is_vertical=True,
        duration_sec=4.8,
        seed=seed_base + 44,
        call_idx=3,
    )
    long_motion = generate_opening_motion_clip(
        prompt=long_prompts[0] if long_prompts else ep["thumbnail_prompt"],
        first_frame_path=long_imgs[0] if long_imgs else None,
        out_mp4=motion_dir / "long_hook.mp4",
        is_vertical=False,
        duration_sec=5.0,
        seed=seed_base + 55,
        call_idx=0,
    )

    long_mp4 = out_dir / f"{ch_id}_full_episode.mp4"
    s1_mp4 = out_dir / f"{ch_id}_short_1.mp4"
    s2_mp4 = out_dir / f"{ch_id}_short_2.mp4"
    s3_mp4 = out_dir / f"{ch_id}_short_3.mp4"
    s4_mp4 = out_dir / f"{ch_id}_short_4.mp4"

    # 6) المونتاج السينمائي للحلقة الكاملة HD (1280x720) مع دمج الغلاف السينمائي المشرق في الإطار الأول
    print(f"[{ch_id}] مونتاج الحلقة الكاملة HD (1280x720)...", flush=True)
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
        opening_motion_mp4=long_motion,
        cover_jpg=thumb_jpg,
    )

    # 7) تصميم الأغلفة الطولية المخصصة (720x1280) + مونتاج الـ 4 شورتس 9:16 بدون أي شاشة داكنة أو بنية
    short_covers = {}
    short_specs = [
        (1, s1_imgs, "short_1_windows", "short_1_mp3", "short_1_words", "short_1_hook_end", "short_1_banner_top", "short_1_title", s1_mp4, s1_motion),
        (2, s2_imgs, "short_2_windows", "short_2_mp3", "short_2_words", "short_2_hook_end", "short_2_banner_top", "short_2_title", s2_mp4, s2_motion),
        (3, s3_imgs, "short_3_windows", "short_3_mp3", "short_3_words", "short_3_hook_end", "short_3_banner_top", "short_3_title", s3_mp4, s3_motion),
        (4, s4_imgs, "short_4_windows", "short_4_mp3", "short_4_words", "short_4_hook_end", "short_4_banner_top", "short_4_title", s4_mp4, s4_motion),
    ]
    for s_num, s_im, w_key, m_key, wd_key, hk_key, bn_key, tl_key, out_p, mot_p in short_specs:
        hb_txt = _clean_hook_banner(str(ep.get(bn_key) or ep.get(tl_key) or ep["youtube_title"]))
        s_cov = out_dir / f"{ch_id}_short_{s_num}_cover.jpg"
        if s_im:
            build_viral_short_cover(
                hero_img_path=s_im[0],
                hook_text=hb_txt,
                badge_text=ep["thumbnail_badge_text"],
                brand_name=ch["brand_name"],
                language=ch["language"],
                out_path=s_cov,
            )
            short_covers[s_num] = s_cov
        print(f"[{ch_id}] مونتاج الشورت رقم {s_num} (720x1280 + غلاف مخصص 9:16 | متحرك افتتاحي={'نعم' if mot_p else 'تلقائي'})...", flush=True)
        render_vertical_short_mp4(
            vertical_images=s_im,
            short_windows=audio_pack[w_key],
            short_mp3=audio_pack[m_key],
            short_words=audio_pack[wd_key],
            brand_name=ch["brand_name"],
            hook_banner=hb_txt,
            hook_end_sec=float(audio_pack[hk_key]),
            cta_banner=ep["cta_banner"],
            out_mp4=out_p,
            work_dir=work_root / f"render_s{s_num}",
            opening_motion_mp4=mot_p,
            cover_jpg=short_covers.get(s_num),
        )

    # 8) النشر والجدولة التلقائية الموزعة على مدار اليوم (إن لم يكن dry-run)
    if dry_run:
        print(
            f"[{ch_id}] DRY-RUN V13.3 مكتمل بنجاح:\n"
            f" - Thumbnail: {thumb_jpg} ({thumb_jpg.stat().st_size / 1024:.1f} KB)\n"
            f" - Long MP4 : {long_mp4} ({long_mp4.stat().st_size / (1024*1024):.2f} MB)\n"
            f" - Short 1  : {s1_mp4} ({s1_mp4.stat().st_size / (1024*1024):.2f} MB)\n"
            f" - Short 2  : {s2_mp4} ({s2_mp4.stat().st_size / (1024*1024):.2f} MB)\n"
            f" - Short 3  : {s3_mp4} ({s3_mp4.stat().st_size / (1024*1024):.2f} MB)\n"
            f" - Short 4  : {s4_mp4} ({s4_mp4.stat().st_size / (1024*1024):.2f} MB)",
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
            short3_mp4=s3_mp4,
            short4_mp4=s4_mp4,
            short1_cover=short_covers.get(1),
            short2_cover=short_covers.get(2),
            short3_cover=short_covers.get(3),
            short4_cover=short_covers.get(4),
            target_slot_utc=target_slot_utc,
        )
        print(f"CDN_AUDIT_URLS: {json.dumps(pub_res.get('cdn_urls', {}), ensure_ascii=False)}", flush=True)
        print(
            f"[{ch_id}] تم قفل/نشر الفيلم وجدولة الـ 4 شورتس بنجاح! الموعد المرجعي: {pub_res.get('scheduled_anchor_utc')} | رابط يوتيوب: {pub_res.get('youtube_watch_url')}",
            flush=True,
        )

    if not keep_output_dir:
        shutil.rmtree(work_root, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Media Empire Autopilot V14.0")
    parser.add_argument("--channel", type=str, default="smart-sync", help="معرف القناة أو all أو smart-sync أو catchup-all")
    parser.add_argument("--max-per-sweep", type=int, default=1, help="أقصى عدد قنوات لكل مسحة جدولة دورية")
    parser.add_argument("--dry-run", action="store_true", help="توليد بدون نشر")
    parser.add_argument("--output-dir", type=str, default="", help="مجلد حفظ المخرجات عند الاختبار")
    args = parser.parse_args()

    if args.channel in ("smart-sync", "catchup-all"):
        now_utc = dt.datetime.now(dt.timezone.utc)
        sweep_cap = 4 if args.channel == "catchup-all" else max(1, args.max_per_sweep)
        print(f"=== [{args.channel.upper()} V14.0] فحص حالة القنوات الأربع عند {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')} ===", flush=True)
        pending = []
        for cid, ch_cfg in CHANNELS.items():
            st = resolve_channel_slot_status(ch_cfg, now_utc=now_utc)
            print(f"  • [{cid}] ({ch_cfg['brand_name']}): needs_run={st['needs_run']} | overdue={st['is_overdue']} | {st['reason']}", flush=True)
            if st["needs_run"]:
                pending.append((cid, st))

        if not pending:
            print("✅ جميع القنوات المستحقة منشورة أو مقفولة بموعدها الرسمي بالثانية داخل سحابة Zernio — لا حاجة لأي إجراء.", flush=True)
            return

        # الأولوية القصوى لأي قناة متأخرة (Overdue)، ثم الأقرب موعداً
        pending.sort(key=lambda item: (0 if item[1]["is_overdue"] else 1, item[1]["target_slot_utc"]))
        selected = pending[:sweep_cap]
        print(f"🚀 سيتم إنتاج وقفل/نشر {len(selected)} قناة في هذه المسحة: {[x[0] for x in selected]}", flush=True)

        failures = 0
        for cid, st in selected:
            try:
                run_single_channel(
                    cid,
                    dry_run=args.dry_run,
                    keep_output_dir=args.output_dir,
                    target_slot_utc=st["target_slot_utc"],
                )
            except Exception as exc:
                failures += 1
                print(f"[ERROR] فشل تشغيل القناة {cid}: {exc}", file=sys.stderr, flush=True)
                traceback.print_exc()

        if failures == len(selected):
            sys.exit(1)
        return

    targets = list(CHANNELS.keys()) if args.channel == "all" else [args.channel]
    failures = 0
    for cid in targets:
        try:
            st = resolve_channel_slot_status(CHANNELS[cid]) if (not args.dry_run and cid in CHANNELS) else {}
            run_single_channel(
                cid,
                dry_run=args.dry_run,
                keep_output_dir=args.output_dir,
                target_slot_utc=st.get("target_slot_utc"),
            )
        except Exception as exc:
            failures += 1
            print(f"[ERROR] فشل تشغيل القناة {cid}: {exc}", file=sys.stderr, flush=True)
            traceback.print_exc()

    if failures == len(targets):
        sys.exit(1)


if __name__ == "__main__":
    main()
