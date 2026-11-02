# -*- coding: utf-8 -*-
"""
الناشر الخوارزمي الذكي V10.0 (2026 YouTube / Facebook / TikTok Algorithm & SEO Growth Engine):
1) هندسة وصف يوتيوب وفيسبوك بأقوى حيل الخوارزميات لعام 2026:
   - أول سطرين قبل زر «عرض المزيد» (Above-the-Fold SEO + Curiosity Hook) لرفع معدل البقاء والبحث.
   - فقرة سيو دلالية غنية بأعلى الكلمات البحثية طلباً لتوجيه خوارزمية الاقتراحات (Suggested Videos) للجمهور المستهدف بدقة.
   - فصول يوتيوب تفاعلية رسمية (`00:00`) + صيغة «من الدقيقة كذا لكذا» لتفعيل Key Moments في جوجل وزيادة إعادة المشاهدة.
   - سؤال تحدي ذكاء مرتبط بالحلقة (في الوصف وفي أول تعليق مثبت!) لتفجير التعليقات وإعادة تشغيل اللقطات (Rewinds).
   - تمرير مصفوفة التاجات البحثية الأصلية (`tags` <= 480 حرفاً) مباشرة لحقل تاجات يوتيوب.
2) غلاف مصغّر مخصص عالي النقر (`1280x720`) + قمع شورتين يومياً مع رابط الحلقة الكاملة في أول تعليق.
"""

import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from sound_studio import format_mmss

ZERNIO_BASE = "https://zernio.com/api/v1"


def _headers(api_key: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def upload_media_to_zernio(api_key: str, file_path: Path, mime_type: str = "video/mp4") -> str:
    last_err = None
    for attempt in range(4):
        try:
            presign = requests.post(
                f"{ZERNIO_BASE}/media/presign",
                headers=_headers(api_key),
                json={"filename": file_path.name, "contentType": mime_type},
                timeout=45,
            )
            presign.raise_for_status()
            pdata = presign.json()
            upload_url = pdata["uploadUrl"]
            public_url = pdata["publicUrl"]

            with open(file_path, "rb") as fh:
                put_resp = requests.put(
                    upload_url,
                    data=fh,
                    headers={"Content-Type": mime_type},
                    timeout=600,
                )
            put_resp.raise_for_status()
            return public_url
        except Exception as exc:
            last_err = exc
            time.sleep(4 * (attempt + 1))
    raise RuntimeError(f"فشل رفع الملف {file_path.name} إلى Zernio: {last_err}")


def _poll_youtube_url(api_key: str, post_id: str, wait_seconds: int = 90) -> Optional[str]:
    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        try:
            r = requests.get(f"{ZERNIO_BASE}/posts/{post_id}", headers=_headers(api_key), timeout=25)
            if r.status_code == 200:
                post_obj = r.json().get("post", r.json())
                for p in post_obj.get("platforms", []):
                    if p.get("platform") == "youtube" and p.get("platformPostUrl"):
                        return str(p["platformPostUrl"])
        except Exception:
            pass
        time.sleep(6)
    return None


def _trim_youtube_tags(raw_tags: List[str], max_total_chars: int = 460) -> List[str]:
    clean_tags: List[str] = []
    used_chars = 0
    for t in raw_tags:
        s = str(t).strip().lstrip("#")
        if not s or len(s) > 45 or s in clean_tags:
            continue
        add_len = len(s) + (2 if clean_tags else 0)
        if used_chars + add_len > max_total_chars:
            break
        clean_tags.append(s)
        used_chars += add_len
    return clean_tags


def _build_algorithm_master_description(
    episode: Dict[str, Any],
    scene_timings: List[Dict[str, Any]],
    channel_cfg: Dict[str, Any],
) -> str:
    is_ar = channel_cfg["language"] == "ar"
    brand = channel_cfg["brand_name"]
    ch_url = channel_cfg["channel_url"]

    hook_2lines = episode.get("seo_hook_2lines") or episode["youtube_title"]
    synopsis = episode.get("seo_synopsis") or ""
    question = episode.get("engagement_question") or (
        "تفتكر إيه التفصيلة اللي كشفت الحقيقة قبل النهاية؟ اكتب توقعك في التعليقات قبل ما تشوف آخر مشهد!"
        if is_ar
        else "Which tiny clue gave away the truth before the ending? Drop your theory in the comments!"
    )
    hashtags = episode.get("hashtags") or ""

    yt_chapters: List[str] = []
    human_ranges: List[str] = []
    for idx, st in enumerate(scene_timings):
        t0 = "00:00" if idx == 0 else format_mmss(st["start"])
        t1 = format_mmss(st["end"])
        title = st["scene_title"]
        yt_chapters.append(f"{t0} {title}")
        if is_ar:
            human_ranges.append(f"• من الدقيقة {t0} إلى {t1} — {title}")
        else:
            human_ranges.append(f"• From {t0} to {t1} — {title}")

    if is_ar:
        body = (
            f"{hook_2lines}\n\n"
            f"{synopsis}\n\n"
            f"💬 تحدي الحلقة للأذكياء (اكتب رأيك في التعليقات 👇):\n"
            f"{question}\n\n"
            f"⏱️ تقسيم مشاهد وفصول الحلقة الكاملة:\n"
            + "\n".join(yt_chapters)
            + "\n\n📌 تفاصيل توقيت كل مشهد:\n"
            + "\n".join(human_ranges)
            + f"\n\n🔔 اشترك في قناة «{brand}» وفعل الجرس عشان توصلك أقوى القصص والتحقيقات يومياً:\n{ch_url}\n\n"
            f"{hashtags}"
        )
    else:
        body = (
            f"{hook_2lines}\n\n"
            f"{synopsis}\n\n"
            f"💬 EPISODE CHALLENGE (Comment your theory below 👇):\n"
            f"{question}\n\n"
            f"⏱️ EPISODE CHAPTERS:\n"
            + "\n".join(yt_chapters)
            + "\n\n📌 DETAILED SCENE TIMELINE:\n"
            + "\n".join(human_ranges)
            + f"\n\n🔔 Subscribe to {brand} & turn on notifications for daily realistic thrillers & mysteries:\n{ch_url}\n\n"
            f"{hashtags}"
        )
    return body[:4850]


def publish_channel_funnel(
    channel_cfg: Dict[str, Any],
    episode: Dict[str, Any],
    scene_timings: List[Dict[str, Any]],
    long_mp4: Path,
    thumbnail_jpg: Path,
    short_1_mp4: Path,
    short_2_mp4: Path,
) -> Dict[str, Any]:
    prefix = channel_cfg["env_prefix"]
    main_key = (
        os.environ.get(f"{prefix}_ZERNIO_KEY", "").strip()
        or os.environ.get(f"ZERNIO_KEY_{prefix}", "").strip()
    )
    tt_key = (
        os.environ.get(f"{prefix}_TIKTOK_ZERNIO_KEY", "").strip()
        or os.environ.get(f"ZERNIO_KEY_{prefix}_TIKTOK", "").strip()
        or main_key
    )

    accounts = channel_cfg.get("accounts") or {}
    yt_acc = accounts.get("youtube") or os.environ.get(f"{prefix}_YT_ACC", "").strip()
    fb_acc = accounts.get("facebook") or os.environ.get(f"{prefix}_FB_ACC", "").strip()
    tt_acc = (
        accounts.get("tiktok")
        or os.environ.get(f"{prefix}_TIKTOK_ACCOUNT_ID", "").strip()
        or os.environ.get(f"{prefix}_TT_ACC", "").strip()
    )

    is_ar = channel_cfg["language"] == "ar"
    results: Dict[str, Any] = {"channel": channel_cfg["brand_name"], "long_post": None, "short_posts": []}

    if not main_key or not (yt_acc or fb_acc):
        results["status"] = "skipped_missing_credentials"
        return results

    # 1) رفع الحلقة الكاملة + الغلاف المخصص عالي النقر (1280x720) ونشرهما بالوصف الخوارزمي الكامل والتاجات وأول تعليق تفاعلي
    long_video_url = upload_media_to_zernio(main_key, long_mp4, mime_type="video/mp4")
    thumb_public_url = upload_media_to_zernio(main_key, thumbnail_jpg, mime_type="image/jpeg")

    long_platforms: List[Dict[str, Any]] = []
    full_desc = _build_algorithm_master_description(episode, scene_timings, channel_cfg)
    yt_tags = _trim_youtube_tags(episode.get("seo_tags") or channel_cfg.get("base_tags") or [])

    debate_comment = (
        f"🔥 سؤال الحلقة للأذكياء: {episode.get('engagement_question', '')}\nاكتب توقعك في رد هنا قبل ما تشوف المشهد الأخير 👇"
        if is_ar
        else f"🔥 Episode Challenge: {episode.get('engagement_question', '')}\nDrop your guess below before watching the final scene 👇"
    )

    if yt_acc:
        long_platforms.append({
            "platform": "youtube",
            "accountId": yt_acc,
            "platformSpecificData": {
                "title": episode["youtube_title"][:98],
                "visibility": "public",
                "madeForKids": False,
                "categoryId": "24",
                "containsSyntheticMedia": True,
                "notifySubscribers": True,
                "firstComment": debate_comment[:480],
            },
        })
    if fb_acc:
        long_platforms.append({
            "platform": "facebook",
            "accountId": fb_acc,
            "platformSpecificData": {
                "title": episode["youtube_title"][:98],
                "firstComment": debate_comment[:480],
            },
        })

    long_payload: Dict[str, Any] = {
        "content": full_desc,
        "mediaItems": [{"type": "video", "url": long_video_url, "thumbnail": thumb_public_url}],
        "platforms": long_platforms,
        "publishNow": True,
    }
    if yt_tags:
        long_payload["tags"] = yt_tags

    long_resp = requests.post(f"{ZERNIO_BASE}/posts", headers=_headers(main_key), json=long_payload, timeout=90)
    long_resp.raise_for_status()
    long_data = long_resp.json()
    long_post_id = long_data.get("post", long_data).get("_id") or long_data.get("id")
    results["long_post"] = {"post_id": long_post_id, "thumbnail_url": thumb_public_url, "tags_count": len(yt_tags)}

    # 2) استخراج الرابط المباشر للحلقة الكاملة لوضعه في أول تعليق على الشورتين
    yt_watch_url = _poll_youtube_url(main_key, str(long_post_id), wait_seconds=90) if long_post_id else None
    funnel_url = yt_watch_url or channel_cfg["channel_url"]
    results["youtube_full_url"] = funnel_url

    first_comment_cta = (
        f"🔥 اسمع القصة الكاملة (+16 دقيقة) وكشف السر للنهاية من هنا 👈 {funnel_url}"
        if is_ar
        else f"🔥 Watch the FULL 16-minute story & final reveal right here 👉 {funnel_url}"
    )

    shorts_plan = [
        {"mp4": short_1_mp4, "title": episode.get("short_1_title") or episode["short_title"], "delay_hours": 0},
        {"mp4": short_2_mp4, "title": episode.get("short_2_title") or episode["short_title"], "delay_hours": 6},
    ]

    for idx, sh in enumerate(shorts_plan, start=1):
        mp4_path = sh["mp4"]
        sh_title = sh["title"]
        delay_h = sh["delay_hours"]

        short_caption = (
            f"{sh_title}\n"
            f"{'👇 رابط الحلقة الكاملة (+16 دقيقة) مثبت في أول تعليق!' if is_ar else '👇 Full 16-minute episode link pinned in the first comment!'}\n"
            f"{episode.get('hashtags', '')}"
        ).strip()

        sched_iso: Optional[str] = None
        if delay_h > 0:
            sched_dt = datetime.now(timezone.utc) + timedelta(hours=delay_h)
            sched_iso = sched_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        short_main_url = upload_media_to_zernio(main_key, mp4_path, mime_type="video/mp4")
        short_main_platforms: List[Dict[str, Any]] = []
        if yt_acc:
            short_main_platforms.append({
                "platform": "youtube",
                "accountId": yt_acc,
                "platformSpecificData": {
                    "title": sh_title[:98],
                    "visibility": "public",
                    "madeForKids": False,
                    "categoryId": "24",
                    "containsSyntheticMedia": True,
                    "firstComment": first_comment_cta,
                },
            })
        if fb_acc:
            short_main_platforms.append({
                "platform": "facebook",
                "accountId": fb_acc,
                "platformSpecificData": {
                    "firstComment": first_comment_cta,
                },
            })

        if short_main_platforms:
            sp_body: Dict[str, Any] = {
                "content": short_caption[:2000],
                "mediaItems": [{"type": "video", "url": short_main_url}],
                "platforms": short_main_platforms,
            }
            if yt_tags:
                sp_body["tags"] = yt_tags[:12]
            if sched_iso:
                sp_body["scheduledFor"] = sched_iso
                sp_body["timezone"] = "UTC"
            else:
                sp_body["publishNow"] = True

            r_sm = requests.post(f"{ZERNIO_BASE}/posts", headers=_headers(main_key), json=sp_body, timeout=90)
            if r_sm.status_code < 300:
                d_sm = r_sm.json()
                results["short_posts"].append({
                    "short_num": idx,
                    "group": "yt_fb",
                    "scheduled": sched_iso or "immediate",
                    "post_id": d_sm.get("post", d_sm).get("_id"),
                })

        if tt_acc and tt_key:
            short_tt_url = short_main_url if tt_key == main_key else upload_media_to_zernio(tt_key, mp4_path, mime_type="video/mp4")
            tt_caption = f"{short_caption}\n🔗 {funnel_url}"[:2100]
            tt_body: Dict[str, Any] = {
                "content": tt_caption,
                "mediaItems": [{"type": "video", "url": short_tt_url}],
                "platforms": [{"platform": "tiktok", "accountId": tt_acc}],
                "tiktokSettings": {
                    "privacy_level": "PUBLIC_TO_EVERYONE",
                    "allow_comment": True,
                    "allow_duet": True,
                    "allow_stitch": True,
                    "commercial_content_type": "none",
                    "content_preview_confirmed": True,
                    "express_consent_given": True,
                    "media_type": "video",
                    "auto_add_music": False,
                    "video_made_with_ai": True,
                },
            }
            if sched_iso:
                tt_body["scheduledFor"] = sched_iso
                tt_body["timezone"] = "UTC"
            else:
                tt_body["publishNow"] = True

            r_tt = requests.post(f"{ZERNIO_BASE}/posts", headers=_headers(tt_key), json=tt_body, timeout=90)
            if r_tt.status_code < 300:
                d_tt = r_tt.json()
                results["short_posts"].append({
                    "short_num": idx,
                    "group": "tiktok",
                    "scheduled": sched_iso or "immediate",
                    "post_id": d_tt.get("post", d_tt).get("_id"),
                })

    results["status"] = "published"
    return results
