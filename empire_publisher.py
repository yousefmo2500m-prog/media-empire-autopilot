# -*- coding: utf-8 -*-
"""
الناشر السحابي الرسمي عبر Zernio API v1 (متوافق 100% مع مواصفات https://zernio.com/llms.txt)
لكل قناة يومياً:
1) يرفع وينشر الفيلم الكامل (+16 دقيقة، 16:9) على يوتيوب وفيسبوك لتفعيل إعلانات الفواصل المتعددة (Mid-Roll Ads).
2) يلتقط رابط الفيلم الكامل المنشور تلقائياً (أو يسترجعه من GET /v1/posts/{postId}).
3) ينشر الشورت التشويقي الأول (Short #1) فوراً على YouTube Shorts + TikTok مع وضع رابط الفيلم الكامل في أول تعليق.
4) يجدول الشورت التشويقي الثاني (Short #2 — بعد 3 ساعات) على YouTube Shorts + TikTok مع وضع نفس رابط الفيلم الكامل في أول تعليق!
"""

import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ZERNIO_BASE = "https://zernio.com/api/v1"


def _zernio_req(
    method: str,
    path: str,
    api_key: str,
    payload: Optional[Dict[str, Any]] = None,
    timeout: int = 240,
) -> tuple[int, Dict[str, Any]]:
    url = f"{ZERNIO_BASE}{path}"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "MediaEmpire-Autopilot/7.6",
    }
    if data is not None:
        headers["Content-Type"] = "application/json; charset=utf-8"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.getcode(), (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw)
        except Exception:
            return exc.code, {"raw_error": raw[:500]}


def upload_asset_to_zernio(file_path: Path, content_type: str, api_key: str) -> str:
    data = file_path.read_bytes()
    st, presign = _zernio_req(
        "POST",
        "/media/presign",
        api_key,
        payload={
            "filename": file_path.name,
            "contentType": content_type,
        },
        timeout=60,
    )
    if st not in (200, 201) or "uploadUrl" not in presign:
        raise RuntimeError(f"فشل حجز مساحة رفع Zernio ({st}): {presign}")

    put_req = urllib.request.Request(
        presign["uploadUrl"],
        data=data,
        headers={"Content-Type": content_type},
        method="PUT",
    )
    with urllib.request.urlopen(put_req, timeout=480) as resp:
        if resp.getcode() not in (200, 201, 204):
            raise RuntimeError(f"فشل رفع الملف إلى سحابة Zernio: HTTP {resp.getcode()}")
    return str(presign["publicUrl"])


def get_zernio_accounts(api_key: str, profile_id: str = "") -> Dict[str, str]:
    paths = [f"/accounts?profileId={profile_id}", "/accounts"] if profile_id else ["/accounts"]
    out: Dict[str, str] = {}
    for p in paths:
        st, data = _zernio_req("GET", p, api_key, timeout=30)
        if st != 200:
            continue
        rows = data.get("accounts") or data.get("data") or []
        for acc in rows:
            if isinstance(acc, dict) and acc.get("isActive", True) is not False:
                plat = str(acc.get("platform", "")).lower().strip()
                aid = acc.get("_id") or acc.get("id") or acc.get("accountId")
                if plat and aid and plat not in out:
                    out[plat] = str(aid)
        if out and profile_id and p.startswith("/accounts?profileId="):
            break
    return out


def _extract_published_url(resp_data: Dict[str, Any]) -> str:
    raw_str = json.dumps(resp_data)
    for pat in (
        r"https?://(?:www\.)?youtube\.com/watch\?v=[A-Za-z0-9_\-]+",
        r"https?://youtu\.be/[A-Za-z0-9_\-]+",
        r"https?://(?:www\.)?facebook\.com/[^\s\"'\\]+",
    ):
        m = re.search(pat, raw_str)
        if m:
            return m.group(0)
    return ""


def _publish_one_short(
    short_video_path: Path,
    short_title: str,
    comment_cta: str,
    is_ar: bool,
    main_key: str,
    tiktok_key: str,
    main_accounts: Dict[str, str],
    tt_accounts: Dict[str, str],
    delay_hours: int = 0,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    short_caption = (
        f"الرابط في أول تعليق 👇\n{short_title}"
        if is_ar
        else f"Full video link in the first comment 👇\n{short_title}"
    )
    sched_iso = (
        (datetime.now(timezone.utc) + timedelta(hours=delay_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
        if delay_hours > 0
        else None
    )

    short_url_main = upload_asset_to_zernio(short_video_path, "video/mp4", main_key)
    if "youtube" in main_accounts:
        yt_payload: Dict[str, Any] = {
            "content": f"{short_caption}\n\n{comment_cta}",
            "title": short_title[:98],
            "visibility": "public",
            "mediaItems": [{"type": "video", "url": short_url_main}],
            "platforms": [
                {
                    "platform": "youtube",
                    "accountId": main_accounts["youtube"],
                    "platformSpecificData": {
                        "title": short_title[:98],
                        "visibility": "public",
                        "containsSyntheticMedia": True,
                        "firstComment": comment_cta,
                    },
                }
            ],
        }
        if sched_iso:
            yt_payload["scheduledFor"] = sched_iso
            yt_payload["timezone"] = "UTC"
        else:
            yt_payload["publishNow"] = True

        st_s, res_s = _zernio_req("POST", "/posts", main_key, payload=yt_payload, timeout=240)
        if st_s not in (200, 201) and sched_iso:
            yt_payload.pop("scheduledFor", None)
            yt_payload.pop("timezone", None)
            yt_payload["publishNow"] = True
            st_s, res_s = _zernio_req("POST", "/posts", main_key, payload=yt_payload, timeout=240)
        out["youtube_short"] = {"status": st_s, "response": res_s}

    if "tiktok" in tt_accounts:
        short_url_tt = short_url_main if tiktok_key == main_key else upload_asset_to_zernio(short_video_path, "video/mp4", tiktok_key)
        tt_payload: Dict[str, Any] = {
            "content": f"{short_caption}\n{comment_cta}"[:2100],
            "mediaItems": [{"type": "video", "url": short_url_tt}],
            "platforms": [
                {
                    "platform": "tiktok",
                    "accountId": tt_accounts["tiktok"],
                    "platformSpecificData": {
                        "firstComment": comment_cta,
                    },
                }
            ],
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
            tt_payload["scheduledFor"] = sched_iso
            tt_payload["timezone"] = "UTC"
        else:
            tt_payload["publishNow"] = True

        st_t, res_t = _zernio_req("POST", "/posts", tiktok_key, payload=tt_payload, timeout=240)
        if st_t not in (200, 201) and sched_iso:
            tt_payload.pop("scheduledFor", None)
            tt_payload.pop("timezone", None)
            tt_payload["publishNow"] = True
            st_t, res_t = _zernio_req("POST", "/posts", tiktok_key, payload=tt_payload, timeout=240)
        out["tiktok_short"] = {"status": st_t, "response": res_t}

    return out


def publish_full_and_short_funnel(
    channel_cfg: Dict[str, Any],
    episode_data: Dict[str, Any],
    long_video_path: Path,
    short_video_path: Path,
    short_2_video_path: Optional[Path] = None,
) -> Dict[str, Any]:
    prefix = channel_cfg["env_prefix"]
    main_key = os.environ.get(f"{prefix}_ZERNIO_KEY", "").strip()
    tiktok_key = os.environ.get(f"{prefix}_TIKTOK_ZERNIO_KEY", "").strip() or main_key
    explicit_tt_id = os.environ.get(f"{prefix}_TIKTOK_ACCOUNT_ID", "").strip()
    fallback_channel_url = os.environ.get(f"{prefix}_CHANNEL_URL", "").strip()
    is_ar = channel_cfg["language"] == "ar"

    if not main_key:
        print(f"⏭️ [{channel_cfg['id']}] لم يتم ضبط {prefix}_ZERNIO_KEY بعد — الفيديوهات جاهزة للنشر فور ربط الحسابات.")
        return {"skipped_no_key": True}

    results: Dict[str, Any] = {}
    main_accounts = get_zernio_accounts(main_key, channel_cfg.get("main_profile_id", ""))
    tt_accounts = dict(
        main_accounts
        if (tiktok_key == main_key and not channel_cfg.get("tiktok_profile_id"))
        else get_zernio_accounts(tiktok_key, channel_cfg.get("tiktok_profile_id", ""))
    )
    if explicit_tt_id:
        tt_accounts["tiktok"] = explicit_tt_id

    if not main_accounts and not tt_accounts:
        print(f"⚠️ [{channel_cfg['id']}] المفتاح صحيح لكن لم يتم الضغط على رابط ربط يوتيوب/فيسبوك/تيك توك بعد.")
        return {"waiting_oauth_connection": True}

    # 1) نشر الفيلم الكامل (+16 دقيقة) على يوتيوب + فيسبوك
    long_url_cloud = upload_asset_to_zernio(long_video_path, "video/mp4", main_key)
    engage_comment = (
        "لو وصلت لهنا قولي رأيك أو استنتاجك في التعليقات! واشترك عشان متفوتكش حلقة بكرة 🔥"
        if is_ar
        else "Drop your thoughts or theory in the comments below and subscribe for tomorrow's full story! 🔥"
    )
    long_platforms: List[Dict[str, Any]] = []
    if "youtube" in main_accounts:
        long_platforms.append({
            "platform": "youtube",
            "accountId": main_accounts["youtube"],
            "platformSpecificData": {
                "title": episode_data["youtube_title"][:98],
                "visibility": "public",
                "containsSyntheticMedia": True,
                "firstComment": engage_comment,
            },
        })
    if "facebook" in main_accounts:
        long_platforms.append({
            "platform": "facebook",
            "accountId": main_accounts["facebook"],
            "platformSpecificData": {
                "title": episode_data["youtube_title"][:98],
                "firstComment": engage_comment,
            },
        })

    full_episode_link = fallback_channel_url
    if long_platforms:
        st_l, res_l = _zernio_req(
            "POST",
            "/posts",
            main_key,
            payload={
                "content": f"{episode_data['youtube_title']}\n\n{episode_data['description']}",
                "title": episode_data["youtube_title"][:98],
                "visibility": "public",
                "publishNow": True,
                "mediaItems": [{"type": "video", "url": long_url_cloud}],
                "platforms": long_platforms,
            },
            timeout=300,
        )
        results["long_post"] = {"status": st_l, "response": res_l}
        detected = _extract_published_url(res_l)
        if not detected:
            post_id = (res_l.get("post") or {}).get("_id")
            if post_id:
                for _ in range(4):
                    time.sleep(6.0)
                    st_p, res_p = _zernio_req("GET", f"/posts/{post_id}", main_key, timeout=30)
                    if st_p == 200:
                        detected = _extract_published_url(res_p)
                        if detected:
                            break
        if detected:
            full_episode_link = detected

    if full_episode_link:
        comment_cta = (
            f"🎬 اسمع القصة كاملة (+16 دقيقة) بالتفصيل من الرابط ده:\n{full_episode_link}"
            if is_ar
            else f"🎬 Watch the FULL 16-minute story right here:\n{full_episode_link}"
        )
    else:
        comment_cta = (
            f"🎬 اسمع القصة كاملة (+16 دقيقة) دلوقتي على قناتنا الرسمية على يوتيوب وفيسبوك: «{channel_cfg['brand_name']}» 🔥"
            if is_ar
            else f"🎬 Watch the FULL 16-minute story right now on our official YouTube & Facebook channel: {channel_cfg['brand_name']} 🔥"
        )

    # 2) الشورت الأول فوراً على YouTube Shorts + TikTok
    results["short_1"] = _publish_one_short(
        short_video_path=short_video_path,
        short_title=episode_data.get("short_1_title") or episode_data["short_title"],
        comment_cta=comment_cta,
        is_ar=is_ar,
        main_key=main_key,
        tiktok_key=tiktok_key,
        main_accounts=main_accounts,
        tt_accounts=tt_accounts,
        delay_hours=0,
    )

    # 3) الشورت الثاني بعد 3 ساعات لنفس الفيديو الطويل لمضاعفة المشاهدات اليومية!
    if short_2_video_path and short_2_video_path.exists():
        results["short_2"] = _publish_one_short(
            short_video_path=short_2_video_path,
            short_title=episode_data.get("short_2_title") or episode_data["short_title"],
            comment_cta=comment_cta,
            is_ar=is_ar,
            main_key=main_key,
            tiktok_key=tiktok_key,
            main_accounts=main_accounts,
            tt_accounts=tt_accounts,
            delay_hours=3,
        )

    return results
