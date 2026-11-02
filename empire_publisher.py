# -*- coding: utf-8 -*-
"""
ناشر الإمبراطورية V11.0 — أقصى توافق مع خوارزميات 2026 للانتشار العضوي السريع (YouTube + Facebook + TikTok)
- يفعّل شريط الفصول التفاعلي رسمياً على يوتيوب بدءاً من `00:00 المقدمة التشويقية` ثم الـ 12 مشهداً بلا حرق!
- يطابق أول سطرين في الوصف (`seo_hook_2lines`) مع العنوان والصورة المصغرة والمقدمة التشويقية لرفع تقييم الفهم الدلالي (Multimodal SEO)!
- يرفع الصورة المصغرة السينمائية (1280x720) ويمرر مصفوفة الكلمات المفتاحية الأصلية (`tags`) + سؤال التفاعل (`engagement_question`) في أول تعليق!
- ينشر مقطعي الشورتس على يوتيوب شورتس + فيسبوك ريلز + تيك توك مع رابط الحلقة الكاملة في أول تعليق!
"""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

ZERNIO_BASE = "https://zernio.com/api/v1"


def _fmt_yt_timestamp(sec: float) -> str:
    sec = max(0, int(round(sec)))
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def build_chapters_block(scene_timings: List[Dict[str, Any]], lang: str) -> str:
    if not scene_timings:
        return ""
    lines = []
    header = "فصول الحلقة الزمنية (بدون حرق):" if lang == "ar" else "EPISODE CHAPTERS (NO SPOILERS):"
    lines.append(header)
    last_sec = -15.0
    for idx, st in enumerate(scene_timings):
        start_s = 0.0 if idx == 0 else float(st.get("start", 0.0))
        if idx > 0 and (start_s - last_sec) < 10.0:
            continue
        last_sec = start_s
        ts = _fmt_yt_timestamp(start_s)
        title = str(st.get("scene_title", f"Scene {idx}")).strip()
        lines.append(f"{ts} {title}")
    return "\n".join(lines)


def sanitize_tags_list(raw_tags: Any, fallback_tags: List[str]) -> List[str]:
    merged: List[str] = []
    if isinstance(raw_tags, list):
        for t in raw_tags:
            s = str(t).strip().lstrip("#").replace(",", " ")
            if s and s.lower() not in [x.lower() for x in merged]:
                merged.append(s)
    for t in fallback_tags:
        s = str(t).strip().lstrip("#")
        if s and s.lower() not in [x.lower() for x in merged]:
            merged.append(s)

    final_tags: List[str] = []
    total_chars = 0
    for t in merged:
        add_len = len(t) + (1 if final_tags else 0)
        if total_chars + add_len > 460 or len(final_tags) >= 24:
            break
        final_tags.append(t)
        total_chars += add_len
    return final_tags


def _headers(api_key: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def upload_media_to_zernio(api_key: str, file_path: Path, mime_type: str = "video/mp4") -> str:
    for attempt in range(4):
        try:
            r = requests.post(
                f"{ZERNIO_BASE}/media/presign",
                headers=_headers(api_key),
                json={"filename": file_path.name, "contentType": mime_type},
                timeout=45,
            )
            r.raise_for_status()
            pdata = r.json()
            upload_url = pdata["uploadUrl"]
            public_url = pdata["publicUrl"]

            with file_path.open("rb") as fh:
                put_r = requests.put(
                    upload_url,
                    data=fh,
                    headers={"Content-Type": mime_type},
                    timeout=600,
                )
                put_r.raise_for_status()
            return public_url
        except Exception as exc:
            if attempt == 3:
                raise RuntimeError(f"فشل رفع الملف {file_path.name}: {exc}") from exc
            time.sleep(4 * (attempt + 1))
    raise RuntimeError("Unreachable")


def _extract_youtube_url(post_resp: Dict[str, Any]) -> Optional[str]:
    post_obj = post_resp.get("post", post_resp)
    for p in post_obj.get("platforms", []):
        if p.get("platform") == "youtube" and p.get("platformPostUrl"):
            return p["platformPostUrl"]
    return None


def wait_for_youtube_url(api_key: str, post_id: str, max_wait_sec: int = 150) -> Optional[str]:
    deadline = time.time() + max_wait_sec
    while time.time() < deadline:
        try:
            r = requests.get(f"{ZERNIO_BASE}/posts/{post_id}", headers=_headers(api_key), timeout=30)
            if r.status_code == 200:
                url = _extract_youtube_url(r.json())
                if url:
                    return url
        except Exception:
            pass
        time.sleep(8)
    return None


def publish_channel_funnel(
    ch: Dict[str, Any],
    episode_meta: Dict[str, Any],
    scene_timings: List[Dict[str, Any]],
    long_mp4: Path,
    thumbnail_jpg: Path,
    short1_mp4: Path,
    short2_mp4: Path,
) -> Dict[str, Any]:
    prefix = ch["env_prefix"]  # CH1 / CH2 / CH3 / CH4
    main_key = os.environ.get(f"{prefix}_ZERNIO_KEY", "").strip()
    if not main_key:
        raise RuntimeError(f"مفتاح {prefix}_ZERNIO_KEY غير موجود في Secrets")

    accounts = ch.get("accounts", {})
    yt_acc = accounts.get("youtube") or os.environ.get(f"{prefix}_YOUTUBE_ID", "").strip()
    fb_acc = accounts.get("facebook") or os.environ.get(f"{prefix}_FACEBOOK_ID", "").strip()

    tt_key = os.environ.get(f"{prefix}_TIKTOK_ZERNIO_KEY", "").strip() or main_key
    tt_acc = os.environ.get(f"{prefix}_TIKTOK_ACCOUNT_ID", "").strip() or accounts.get("tiktok", "")

    lang = ch["language"]
    yt_handle = ch["handle"]

    tags_list = sanitize_tags_list(
        episode_meta.get("seo_tags", []),
        ch.get("base_tags", []),
    )

    print(f"[{ch['id']}] رفع الصورة المصغرة والحلقة الكاملة والمقطعين التشويقيين إلى سحابة النشر...")
    thumb_url = upload_media_to_zernio(main_key, thumbnail_jpg, mime_type="image/jpeg")
    long_url = upload_media_to_zernio(main_key, long_mp4, mime_type="video/mp4")
    s1_url = upload_media_to_zernio(main_key, short1_mp4, mime_type="video/mp4")
    s2_url = upload_media_to_zernio(main_key, short2_mp4, mime_type="video/mp4")

    s1_tt_url = upload_media_to_zernio(tt_key, short1_mp4, mime_type="video/mp4") if (tt_acc and tt_key != main_key) else s1_url
    s2_tt_url = upload_media_to_zernio(tt_key, short2_mp4, mime_type="video/mp4") if (tt_acc and tt_key != main_key) else s2_url

    ep_title = str(episode_meta.get("youtube_title") or episode_meta.get("episode_title") or ch["brand_name"])[:95]
    seo_hook_2lines = str(episode_meta.get("seo_hook_2lines", "")).strip()
    seo_synopsis = str(episode_meta.get("seo_synopsis", "")).strip()
    chapters_txt = build_chapters_block(scene_timings, lang)
    comment_question = str(episode_meta.get("engagement_question", "")).strip()
    raw_hashtags = str(episode_meta.get("hashtags", "")).strip()

    if lang == "ar":
        subscribe_block = (
            f"اشترك في قناة «{ch['brand_name']}» ({yt_handle}) وفعل الجرس لتصلك أقوى الحلقات الدرامية والقصص الغامضة يومياً!\n"
            f"{comment_question if comment_question else 'اكتب توقعك في التعليقات قبل أن تصل للمشهد الأخير.. هل كشفت الخيط المخفي من البداية؟'}"
        )
        first_comment_long = (
            comment_question
            if comment_question
            else "في أي دقيقة من الحلقة اكتشفت الحقيقة؟ شاركنا تحليلك في الردود!"
        )
        hashtags_line = raw_hashtags or " ".join(f"#{t.replace(' ', '_')}" for t in tags_list[:8])
    else:
        subscribe_block = (
            f"Subscribe to {ch['brand_name']} ({yt_handle}) and turn on notifications for daily full-length thrillers & mysteries!\n"
            f"{comment_question if comment_question else 'Drop your theory in the comments before the final twist — did you catch the hidden clue early?'}"
        )
        first_comment_long = (
            comment_question
            if comment_question
            else "At what exact timestamp did you figure out the truth? Tell us your theory below!"
        )
        hashtags_line = raw_hashtags or " ".join(f"#{t.replace(' ', '')}" for t in tags_list[:8])

    full_yt_description = "\n\n".join(
        part for part in [seo_hook_2lines, seo_synopsis, chapters_txt, subscribe_block, hashtags_line] if part
    )

    results: Dict[str, Any] = {
        "long_video": None,
        "short_1": None,
        "short_2": None,
        "youtube_watch_url": None,
        "cdn_urls": {"thumb": thumb_url, "long": long_url, "short_1": s1_url, "short_2": s2_url},
    }

    # 1) نشر الحلقة الكاملة على يوتيوب + فيسبوك مع الصورة المصغرة والفصول والكلمات المفتاحية وسؤال التفاعل
    long_platforms = []
    if yt_acc:
        long_platforms.append({
            "platform": "youtube",
            "accountId": yt_acc,
            "platformSpecificData": {
                "title": ep_title,
                "visibility": "public",
                "madeForKids": False,
                "containsSyntheticMedia": True,
                "categoryId": "24",
                "firstComment": first_comment_long,
            },
        })
    if fb_acc:
        long_platforms.append({
            "platform": "facebook",
            "accountId": fb_acc,
            "platformSpecificData": {
                "title": ep_title,
                "firstComment": first_comment_long,
            },
        })

    if long_platforms:
        payload_long = {
            "title": ep_title,
            "content": full_yt_description,
            "tags": tags_list,
            "publishNow": True,
            "mediaItems": [{
                "type": "video",
                "url": long_url,
                "thumbnailUrl": thumb_url,
            }],
            "platforms": long_platforms,
        }
        r_long = requests.post(f"{ZERNIO_BASE}/posts", headers=_headers(main_key), json=payload_long, timeout=180)
        r_long.raise_for_status()
        long_data = r_long.json()
        results["long_video"] = long_data
        post_id = long_data.get("post", long_data).get("_id") or long_data.get("post", long_data).get("id")
        yt_watch = _extract_youtube_url(long_data)
        if not yt_watch and post_id and yt_acc:
            yt_watch = wait_for_youtube_url(main_key, post_id, max_wait_sec=140)
        results["youtube_watch_url"] = yt_watch

    yt_link_text = results["youtube_watch_url"] or ch.get("channel_url") or f"https://www.youtube.com/{yt_handle}"
    if lang == "ar":
        first_comment_cta = f"شاهد الحلقة الكاملة بكل تفاصيلها ونهايتها الصادمة الآن على قناتنا ({yt_handle}):\n{yt_link_text}"
        short_desc_suffix = f"\n\nالحلقة الكاملة متاحة الآن على قناتنا {yt_handle} — الرابط المباشر في أول تعليق!\n#شورتس #قصص_واقعية #تشويق #غموض #{ch['brand_name'].replace(' ', '_')}"
    else:
        first_comment_cta = f"Watch the full episode & shocking ending right now on our YouTube channel ({yt_handle}):\n{yt_link_text}"
        short_desc_suffix = f"\n\nFull episode streaming now on {yt_handle} — direct link in the first comment!\n#shorts #thriller #mystery #plotwist #{ch['brand_name'].replace(' ', '')}"

    # 2) نشر مقطعي الشورتس (Short 1 + Short 2) مع تحويل مباشر للحلقة الكاملة
    for idx_s, (s_title_key, m_url, tt_m_url) in enumerate(
        [
            ("short_1_title", s1_url, s1_tt_url),
            ("short_2_title", s2_url, s2_tt_url),
        ],
        start=1,
    ):
        raw_st = str(episode_meta.get(s_title_key) or ep_title).strip()
        s_title = raw_st[:92]
        yt_s_title = s_title if "#shorts" in s_title.lower() else f"{s_title[:84]} #shorts"
        s_caption = f"{s_title}{short_desc_suffix}"

        s_platforms = []
        if yt_acc:
            s_platforms.append({
                "platform": "youtube",
                "accountId": yt_acc,
                "platformSpecificData": {
                    "title": yt_s_title[:98],
                    "visibility": "public",
                    "madeForKids": False,
                    "containsSyntheticMedia": True,
                    "categoryId": "24",
                    "firstComment": first_comment_cta,
                },
            })
        if fb_acc:
            s_platforms.append({
                "platform": "facebook",
                "accountId": fb_acc,
                "platformSpecificData": {
                    "contentType": "reel",
                    "firstComment": first_comment_cta,
                },
            })

        short_res: Dict[str, Any] = {}
        if s_platforms:
            payload_s = {
                "title": s_title,
                "content": s_caption,
                "tags": tags_list[:16],
                "publishNow": True,
                "mediaItems": [{"type": "video", "url": m_url}],
                "platforms": s_platforms,
            }
            if idx_s == 2:
                time.sleep(6)
            rs = requests.post(f"{ZERNIO_BASE}/posts", headers=_headers(main_key), json=payload_s, timeout=180)
            rs.raise_for_status()
            short_res["yt_fb"] = rs.json()

        if tt_acc and tt_key:
            tt_caption = f"{s_title}\n{'شاهد القصة الكاملة على يوتيوب ' + yt_handle if lang == 'ar' else 'Watch the full episode on YouTube ' + yt_handle} ({yt_link_text})"
            tt_payload: Dict[str, Any] = {
                "content": tt_caption[:2000],
                "mediaItems": [{"type": "video", "url": tt_m_url}],
                "platforms": [{
                    "platform": "tiktok",
                    "accountId": tt_acc,
                    "platformSpecificData": {
                        "privacyLevel": "PUBLIC_TO_EVERYONE",
                        "allowComment": True,
                        "allowDuet": True,
                        "allowStitch": True,
                        "contentPreviewConfirmed": True,
                        "expressConsentGiven": True,
                        "videoMadeWithAi": True,
                    },
                }],
            }
            if idx_s == 1:
                tt_payload["publishNow"] = True
            else:
                sched_epoch = time.time() + 4 * 3600
                tt_payload["scheduledFor"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(sched_epoch))

            rtt = requests.post(f"{ZERNIO_BASE}/posts", headers=_headers(tt_key), json=tt_payload, timeout=180)
            if rtt.status_code < 400:
                short_res["tiktok"] = rtt.json()
            else:
                short_res["tiktok_error"] = rtt.text[:300]

        results[f"short_{idx_s}"] = short_res

    return results
