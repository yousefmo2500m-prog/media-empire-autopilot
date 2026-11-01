# -*- coding: utf-8 -*-
"""
الناشر السحابي لمنظومة التحويل الثلاثية V4.0 (YouTube + Facebook Long-Form -> Shorts + TikTok First-Comment Funnel)
لكل قناة من القنوات الأربع:
1) يرفع وينشر الحلقة الكاملة (15+ دقيقة 16:9) على يوتيوب وفيسبوك لتفعيل إعلانات الفواصل (Mid-Roll Ads).
2) يلتقط رابط الحلقة المنشورة تلقائياً.
3) يرفع وينشر الشورت التشويقي الحماسي (9:16) على YouTube Shorts + TikTok + Facebook Reels،
   ويضع رابط الحلقة الكاملة تلقائياً في **أول تعليق** لتحويل المشاهدات السريعة فوراً إلى الفيديو الطويل!
"""

import json
import os
import urllib.error
import urllib.request
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
        "User-Agent": "MediaEmpire-Autopilot/4.0",
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
            "size": len(data),
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
    with urllib.request.urlopen(put_req, timeout=420) as resp:
        if resp.getcode() not in (200, 201, 204):
            raise RuntimeError(f"فشل رفع الملف إلى سحابة Zernio: HTTP {resp.getcode()}")
    return str(presign["publicUrl"])


def get_zernio_accounts(api_key: str) -> Dict[str, str]:
    st, data = _zernio_req("GET", "/accounts", api_key, timeout=30)
    if st != 200:
        raise RuntimeError(f"تعذر قراءة حسابات Zernio ({st}): {data}")
    rows = data.get("accounts") or data.get("data") or []
    out: Dict[str, str] = {}
    for acc in rows:
        if isinstance(acc, dict):
            plat = str(acc.get("platform", "")).lower().strip()
            aid = acc.get("_id") or acc.get("id") or acc.get("accountId")
            if plat and aid and plat not in out:
                out[plat] = str(aid)
    return out


def _extract_published_url(resp_data: Dict[str, Any]) -> str:
    """يستخرج رابط الفيديو المنشور على يوتيوب أو فيسبوك لوضعه في أول تعليق على الشورتس والتيك توك."""
    raw_str = json.dumps(resp_data)
    import re
    for pat in (
        r"https?://(?:www\.)?youtube\.com/watch\?v=[A-Za-z0-9_\-]+",
        r"https?://youtu\.be/[A-Za-z0-9_\-]+",
        r"https?://(?:www\.)?facebook\.com/[^\s\"']+",
    ):
        m = re.search(pat, raw_str)
        if m:
            return m.group(0)
    return ""


def publish_full_and_short_funnel(
    channel_cfg: Dict[str, Any],
    episode_data: Dict[str, Any],
    long_video_path: Path,
    short_video_path: Path,
) -> Dict[str, Any]:
    prefix = channel_cfg["env_prefix"]
    main_key = os.environ.get(f"{prefix}_ZERNIO_KEY", "").strip()
    tiktok_key = os.environ.get(f"{prefix}_TIKTOK_ZERNIO_KEY", "").strip() or main_key
    fallback_channel_url = os.environ.get(f"{prefix}_CHANNEL_URL", "").strip()
    is_ar = channel_cfg["language"] == "ar"

    if not main_key:
        print(f"⏭️ [{channel_cfg['id']}] لم يتم ضبط {prefix}_ZERNIO_KEY بعد — الفيديوهات جاهزة للنشر فور ربط الحسابات.")
        return {"skipped_no_key": True}

    results: Dict[str, Any] = {}
    main_accounts = get_zernio_accounts(main_key)

    # 1) نشر الفيلم الكامل (15+ دقيقة) على يوتيوب + فيسبوك
    long_url_cloud = upload_asset_to_zernio(long_video_path, "video/mp4", main_key)
    long_platforms: List[Dict[str, Any]] = []
    if "youtube" in main_accounts:
        long_platforms.append({
            "platform": "youtube",
            "accountId": main_accounts["youtube"],
            "platformSpecificData": {
                "title": episode_data["youtube_title"][:100],
                "visibility": "public",
                "containsSyntheticMedia": True,
                "firstComment": (
                    "لو وصلت لهنا قولي رأيك في التصرف ده في التعليقات! واشترك عشان متفوتكش حلقة بكرة 🔥"
                    if is_ar
                    else "Drop your thoughts in the comments below and subscribe for tomorrow's full story! 🔥"
                ),
            },
        })
    if "facebook" in main_accounts:
        long_platforms.append({
            "platform": "facebook",
            "accountId": main_accounts["facebook"],
            "platformSpecificData": {
                "title": episode_data["youtube_title"][:100],
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
                "publishNow": True,
                "mediaItems": [{"type": "video", "url": long_url_cloud}],
                "platforms": long_platforms,
            },
            timeout=300,
        )
        results["long_post"] = {"status": st_l, "response": res_l}
        detected = _extract_published_url(res_l)
        if detected:
            full_episode_link = detected

    comment_cta = (
        f"🎬 اسمع القصة كاملة (16 دقيقة) بالتفصيل من الرابط ده:\n{full_episode_link}".strip()
        if is_ar
        else f"🎬 Watch the FULL 16-minute story right here:\n{full_episode_link}".strip()
    )
    short_caption = (
        f"الرابط في أول تعليق 👇\n{episode_data['short_title']}"
        if is_ar
        else f"Full video link in the first comment 👇\n{episode_data['short_title']}"
    )

    # 2) نشر الشورت الحماسي على YouTube Shorts (+ Facebook Reels) مع رابط الفيديو الطويل في أول تعليق
    short_url_main = upload_asset_to_zernio(short_video_path, "video/mp4", main_key)
    short_platforms: List[Dict[str, Any]] = []
    if "youtube" in main_accounts:
        short_platforms.append({
            "platform": "youtube",
            "accountId": main_accounts["youtube"],
            "platformSpecificData": {
                "title": episode_data["short_title"][:100],
                "visibility": "public",
                "containsSyntheticMedia": True,
                "firstComment": comment_cta,
            },
        })
    if short_platforms:
        st_s, res_s = _zernio_req(
            "POST",
            "/posts",
            main_key,
            payload={
                "content": f"{short_caption}\n\n{comment_cta}",
                "publishNow": True,
                "mediaItems": [{"type": "video", "url": short_url_main}],
                "platforms": short_platforms,
            },
            timeout=240,
        )
        results["youtube_short"] = {"status": st_s, "response": res_s}

    # 3) نشر نفس الجزء الحماسي على حساب التيك توك الخاص بالقناة مع تعليق الرابط الكامل
    tt_accounts = main_accounts if tiktok_key == main_key else get_zernio_accounts(tiktok_key)
    if "tiktok" in tt_accounts:
        short_url_tt = short_url_main if tiktok_key == main_key else upload_asset_to_zernio(short_video_path, "video/mp4", tiktok_key)
        st_t, res_t = _zernio_req(
            "POST",
            "/posts",
            tiktok_key,
            payload={
                "content": short_caption,
                "publishNow": True,
                "mediaItems": [{"type": "video", "url": short_url_tt}],
                "platforms": [
                    {
                        "platform": "tiktok",
                        "accountId": tt_accounts["tiktok"],
                        "platformSpecificData": {
                            "privacyLevel": "PUBLIC_TO_EVERYONE",
                            "allowComment": True,
                            "aigcLabel": True,
                            "firstComment": comment_cta,
                        },
                    }
                ],
            },
            timeout=240,
        )
        results["tiktok_short"] = {"status": st_t, "response": res_t}

    return results
