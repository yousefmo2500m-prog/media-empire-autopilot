# -*- coding: utf-8 -*-
"""
الناشر السحابي المستقل للقنوات الربحية الأربع (Zero-Cost Multi-Channel Publisher)
- يرفع الفيديو والصورة المصغرة سحابياً عبر Zernio API المجاني (كل حساب مجاني يربط قناة يوتيوب + صفحة فيسبوك بنشر غير محدود مدى الحياة بدون بطاقة بنكية).
- يفعّل تلقائياً خيار الإفصاح عن المحتوى المولّد بالذكاء الاصطناعي (containsSyntheticMedia: True)
  التزاماً بتحديث يوتيوب (يوليو 2026) لحماية تفعيل الربح 100%.
- يكتب أول تعليق تفاعلي تلقائياً (ويدعم إضافة رابط/كود أفلييت اختياري في أول تعليق).
"""

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

ZERNIO_BASE = "https://zernio.com/api/v1"


def _zernio_req(
    method: str,
    path: str,
    api_key: str,
    payload: Optional[Dict[str, Any]] = None,
    timeout: int = 180,
) -> tuple[int, Dict[str, Any]]:
    url = f"{ZERNIO_BASE}{path}"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "MediaEmpire-Autopilot/1.0",
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
        timeout=45,
    )
    if st not in (200, 201) or "uploadUrl" not in presign:
        raise RuntimeError(f"فشل حجز مساحة رفع Zernio ({st}): {presign}")

    put_req = urllib.request.Request(
        presign["uploadUrl"],
        data=data,
        headers={"Content-Type": content_type},
        method="PUT",
    )
    with urllib.request.urlopen(put_req, timeout=240) as resp:
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


def publish_channel_episode(
    channel_cfg: Dict[str, Any],
    script_data: Dict[str, Any],
    video_path: Path,
    thumbnail_path: Optional[Path] = None,
) -> Dict[str, Any]:
    prefix = channel_cfg["env_prefix"]
    api_key = os.environ.get(f"{prefix}_ZERNIO_KEY", "").strip()
    affiliate_footer = os.environ.get("AFFILIATE_COMMENT_FOOTER", "").strip()

    if not api_key:
        print(f"[{channel_cfg['id']}] لم يتم ضبط {prefix}_ZERNIO_KEY بعد — تم حفظ الفيديو محلياً وجاهز للنشر فور إضافة المفتاح.")
        return {"skipped_no_key": True}

    accounts = get_zernio_accounts(api_key)
    video_url = upload_asset_to_zernio(video_path, "video/mp4", api_key)
    thumb_url = None
    if thumbnail_path and thumbnail_path.exists():
        try:
            thumb_url = upload_asset_to_zernio(thumbnail_path, "image/jpeg", api_key)
        except Exception as exc:
            print(f"[Thumbnail Upload Warning] {exc}")

    first_comment = script_data.get("first_comment", "").strip()
    if affiliate_footer:
        first_comment = f"{first_comment}\n\n{affiliate_footer}".strip()

    yt_title = script_data.get("youtube_title") or script_data.get("episode_title", channel_cfg["brand_name"])
    desc = script_data.get("description", "")
    results: Dict[str, Any] = {"video_url": video_url, "platforms": {}}

    # 1) النشر على يوتيوب (Public + إفصاح AI رسمي + أول تعليق + صورة مصغرة)
    if "youtube" in accounts:
        yt_spec: Dict[str, Any] = {
            "title": yt_title[:95],
            "visibility": "public",
            "categoryId": "24" if channel_cfg["id"] == "ch1_novels" else "27",
            "madeForKids": False,
            "containsSyntheticMedia": True,  # التزام كامل بسياسة يوتيوب يوليو 2026
            "firstComment": first_comment[:1900],
        }
        if thumb_url:
            yt_spec["thumbnailUrl"] = thumb_url

        st, resp = _zernio_req(
            "POST",
            "/posts",
            api_key,
            payload={
                "content": desc[:4800],
                "mediaItems": [{"type": "video", "url": video_url}],
                "platforms": [
                    {
                        "platform": "youtube",
                        "accountId": accounts["youtube"],
                        "platformSpecificData": yt_spec,
                    }
                ],
                "publishNow": True,
            },
        )
        results["platforms"]["youtube"] = {"status": st, "response": resp}
        print(f"[{channel_cfg['id']} -> YouTube] HTTP {st}")

    # 2) النشر على صفحة فيسبوك (للتأهل لربح Facebook Content Monetization في مصر)
    if "facebook" in accounts:
        fb_caption = f"{yt_title}\n\n{desc}"
        st, resp = _zernio_req(
            "POST",
            "/posts",
            api_key,
            payload={
                "content": fb_caption[:4500],
                "mediaItems": [{"type": "video", "url": video_url}],
                "platforms": [
                    {
                        "platform": "facebook",
                        "accountId": accounts["facebook"],
                        "platformSpecificData": {
                            "firstComment": first_comment[:1900],
                        },
                    }
                ],
                "publishNow": True,
            },
        )
        results["platforms"]["facebook"] = {"status": st, "response": resp}
        print(f"[{channel_cfg['id']} -> Facebook] HTTP {st}")

    return results
