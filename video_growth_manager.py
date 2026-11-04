# -*- coding: utf-8 -*-
"""Evidence-gated YouTube video lifecycle manager (V16.0).

Tracks every YouTube upload found through the paginated Zernio analytics feed,
rotates through public view-count checks, uses YouTube's delayed per-video
Analytics API for watch/retention signals, and makes only sparse, reversible
metadata experiments.  It never re-uploads, deletes, or changes video files.
"""

import datetime as dt
import json
import math
import os
import re
import statistics
import tempfile
import time
import unicodedata
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import quote

import requests

ZERNIO_BASE = "https://zernio.com/api/v1"
UTC = dt.timezone.utc
PAGE_SIZE = 100
PUBLIC_VIEW_BUDGET = 2
MIN_SAMPLE_INTERVAL_HOURS = 12.0
MAX_TITLE_EDITS_PER_VIDEO = 2
TITLE_EDIT_COOLDOWN_HOURS = 24.0 * 14.0
MAX_THUMBNAIL_EDITS_PER_VIDEO = 1
MAX_TRACKED_VIDEOS_PER_CHANNEL = 5000
DETAIL_FETCH_COOLDOWN_HOURS = 24.0
RETENTION_FETCH_COOLDOWN_HOURS = 24.0 * 7.0

YT_PAGE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _utc_now() -> dt.datetime:
    return dt.datetime.now(UTC)


def _iso_utc(value: Optional[dt.datetime] = None) -> str:
    return (value or _utc_now()).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(value: Any) -> Optional[dt.datetime]:
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        elif re.search(r"[+-]\d{4}$", raw):
            raw = raw[:-2] + ":" + raw[-2:]
        parsed = dt.datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except Exception:
        return None


def _headers(api_key: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def load_video_growth_state(channel_ids: List[str]) -> Dict[str, Any]:
    """Load compact line-oriented per-video ledgers separately from the small director summary."""
    root = Path(__file__).resolve().parent / "state"
    state: Dict[str, Any] = {"channels": {}}
    for channel_id in channel_ids:
        path = root / f"youtube_growth_{channel_id}.jsonl"
        channel_state: Dict[str, Any] = {"youtube_video_ledger": {}}
        if path.exists():
            try:
                for line in path.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    item = json.loads(line)
                    if not isinstance(item, dict):
                        continue
                    if "__meta__" in item and isinstance(item["__meta__"], dict):
                        channel_state.update(item["__meta__"])
                    elif item.get("video_id"):
                        channel_state["youtube_video_ledger"][str(item["video_id"])] = item
            except Exception:
                # A corrupt/partial ledger must not stop a publishing run.
                channel_state = {"youtube_video_ledger": {}}
        state["channels"][channel_id] = channel_state
    return state


def save_video_growth_state(state: Dict[str, Any]) -> None:
    """Atomically save one compact JSON object per line so routine updates stay diffable."""
    root = Path(__file__).resolve().parent / "state"
    root.mkdir(parents=True, exist_ok=True)
    for channel_id, channel_state in (state.get("channels") or {}).items():
        ledger = channel_state.get("youtube_video_ledger") or {}
        metadata = {k: v for k, v in channel_state.items() if k != "youtube_video_ledger"}
        path = root / f"youtube_growth_{channel_id}.jsonl"
        if not ledger and not metadata:
            continue
        lines = [json.dumps({"__meta__": metadata}, ensure_ascii=False, separators=(",", ":"))]
        for video_id in sorted(ledger):
            record = ledger[video_id]
            if isinstance(record, dict):
                lines.append(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
        temp_path = path.with_suffix(path.suffix + ".tmp")
        temp_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.replace(temp_path, path)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _as_float(value: Any) -> Optional[float]:
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def _extract_video_id(url: str) -> str:
    raw = str(url or "")
    patterns = (
        r"(?:youtube\.com|youtube-nocookie\.com)/(?:.*?[?&]v=|shorts/|embed/|live/)([A-Za-z0-9_-]{11})",
        r"youtu\.be/([A-Za-z0-9_-]{11})",
    )
    for pattern in patterns:
        match = re.search(pattern, raw, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def _post_youtube_fields(post: Dict[str, Any], account_id: str) -> Tuple[str, str, str]:
    url = str(post.get("platformPostUrl") or "")
    title = ""
    for platform in post.get("platforms") or []:
        if str(platform.get("platform") or "").lower() != "youtube":
            continue
        if account_id and platform.get("accountId") and str(platform.get("accountId")) != account_id:
            continue
        specific = platform.get("platformSpecificData") or {}
        title = str(specific.get("title") or "").strip()
        url = str(platform.get("platformPostUrl") or url)
        if not url:
            native_id = str(platform.get("platformPostId") or "")
            if re.fullmatch(r"[A-Za-z0-9_-]{11}", native_id):
                url = f"https://www.youtube.com/watch?v={native_id}"
        if title or url:
            break
    if not title:
        title = str(post.get("title") or "").strip()
    content = str(post.get("content") or "").strip()
    if not title and content:
        title = content.splitlines()[0].strip()
    if not url:
        for item in post.get("mediaItems") or []:
            media_url = str(item.get("url") or "")
            vid = _extract_video_id(media_url)
            if vid:
                url = f"https://www.youtube.com/watch?v={vid}"
                break
    return title[:180], url, content


def _extract_ctr(analytics: Dict[str, Any]) -> Optional[float]:
    for key in (
        "impressionsClickThroughRate",
        "impressionClickThroughRate",
        "clickThroughRate",
        "ctr",
    ):
        value = _as_float(analytics.get(key))
        if value is not None:
            # YouTube commonly returns a percentage; tolerate providers that use a fraction.
            return value / 100.0 if value > 1.0 else value
    return None


def _get_media_thumbnail(post: Dict[str, Any], video_id: str) -> str:
    value = str(post.get("thumbnailUrl") or "").strip()
    if not value:
        for item in post.get("mediaItems") or []:
            value = str(item.get("thumbnail") or "").strip()
            if value:
                break
    return value or (f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" if video_id else "")


def _is_short_post(title: str, content: str, duration: int, url: str) -> bool:
    low = f"{title}\n{content[:500]}\n{url}".lower()
    if any(tag in low for tag in ("#shorts", "#شورتس", "/shorts/")):
        return True
    return 0 < duration <= 62


def _analytics_page(
    api_key: str,
    account_id: str,
    page: int,
    now: dt.datetime,
) -> Tuple[List[Dict[str, Any]], int, str]:
    start_day = (now.date() - dt.timedelta(days=364)).isoformat()
    params = {
        "accountId": account_id,
        "platform": "youtube",
        "limit": PAGE_SIZE,
        "page": page,
        "fromDate": start_day,
        "toDate": now.date().isoformat(),
    }
    try:
        response = requests.get(
            f"{ZERNIO_BASE}/analytics",
            headers=_headers(api_key),
            params=params,
            timeout=(2.5, 7.0),
        )
        if response.status_code != 200:
            return [], 0, f"analytics_http_{response.status_code}"
        payload = response.json()
        posts = payload.get("posts") or []
        pagination = payload.get("pagination") or {}
        pages = _as_int(pagination.get("pages"), 0)
        if pages <= 0:
            total = _as_int(pagination.get("total"), 0)
            limit = max(1, _as_int(pagination.get("limit"), PAGE_SIZE))
            pages = int(math.ceil(total / limit)) if total else (page + 1 if len(posts) >= PAGE_SIZE else page)
        return [p for p in posts if isinstance(p, dict)], max(1, pages), "ok"
    except Exception as exc:
        return [], 0, f"analytics_error_{type(exc).__name__}"


def _upsert_video_record(
    channel: Dict[str, Any],
    post: Dict[str, Any],
    ledger: Dict[str, Dict[str, Any]],
    now: dt.datetime,
) -> Optional[Dict[str, Any]]:
    if str(post.get("status") or "").lower() != "published":
        return None
    account_id = str((channel.get("accounts") or {}).get("youtube") or "")
    title, url, content = _post_youtube_fields(post, account_id)
    video_id = _extract_video_id(url)
    if not video_id:
        return None

    analytics = post.get("analytics") or {}
    duration = _as_int(analytics.get("videoDurationSeconds"), 0)
    published_at = str(post.get("publishedAt") or post.get("scheduledFor") or "")
    published_dt = _parse_iso(published_at)
    if not published_dt or published_dt > now + dt.timedelta(hours=2):
        return None

    record = ledger.setdefault(video_id, {
        "video_id": video_id,
        "snapshots": [],
        "actions": [],
        "title_edits": 0,
        "thumbnail_edits": 0,
        "playlist_added": False,
    })
    age_days = max(0.0, (now - published_dt).total_seconds() / 86400.0)
    post_ids = list(dict.fromkeys([
        str(post.get("latePostId") or "").strip(),
        str(post.get("_id") or "").strip(),
    ]))
    last_title_edit = _parse_iso(record.get("last_title_edit_utc"))
    keep_recent_edit = bool(
        last_title_edit
        and (now - last_title_edit).total_seconds() < TITLE_EDIT_COOLDOWN_HOURS
        and record.get("title")
        and str(record.get("title")) != title
    )
    record.update({
        "video_id": video_id,
        "post_ids": [post_id for post_id in post_ids if post_id][:2],
        "title": str(record.get("title"))[:180] if keep_recent_edit else title[:180],
        # Keep a tiny story fingerprint for every age; retain a slightly longer synopsis only for recent uploads.
        "story_seed": content[:240],
        "description_excerpt": content[:420] if age_days <= 180.0 else "",
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "thumbnail_url": _get_media_thumbnail(post, video_id),
        "published_at": published_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_seconds": duration,
        "is_short": _is_short_post(title, content, duration, url),
        "last_metadata_seen_utc": _iso_utc(now),
    })

    metric_update_dt = _parse_iso(analytics.get("lastUpdated"))
    record["last_analytics_metrics"] = {
        "views": max(0, _as_int(analytics.get("views"), 0)),
        "impressions": max(0, _as_int(analytics.get("impressions"), 0)),
        "likes": max(0, _as_int(analytics.get("likes"), 0)),
        "comments": max(0, _as_int(analytics.get("comments"), 0)),
        "shares": max(0, _as_int(analytics.get("shares"), 0)),
        "ctr": _extract_ctr(analytics),
        "metrics_updated_at_utc": metric_update_dt.strftime("%Y-%m-%dT%H:%M:%SZ") if metric_update_dt else "",
    }
    return record


def _public_youtube_views(video_id: str) -> Optional[Dict[str, int]]:
    try:
        response = requests.get(
            f"https://www.youtube.com/watch?v={video_id}",
            headers=YT_PAGE_HEADERS,
            timeout=(2.0, 3.5),
        )
        if response.status_code != 200:
            return None
        body = response.text
        views_match = re.search(r'"viewCount"\s*:\s*"(\d+)"', body)
        if not views_match:
            views_match = re.search(r'"videoViewCountRenderer"\s*:\s*\{[^}]*"viewCount"\s*:\s*\{"simpleText"\s*:\s*"([\d,]+)', body)
        likes_match = re.search(r'"likeCount"\s*:\s*"?(\d+)"?', body)
        if not views_match:
            return None
        return {
            "views": _as_int(views_match.group(1).replace(",", ""), 0),
            "likes": _as_int(likes_match.group(1), 0) if likes_match else 0,
        }
    except Exception:
        return None


def _push_snapshot(record: Dict[str, Any], snapshot: Dict[str, Any], min_interval_hours: float) -> bool:
    snapshots = record.setdefault("snapshots", [])
    latest = snapshots[-1] if snapshots else None
    if latest:
        latest_at = _parse_iso(latest.get("at_utc"))
        elapsed = (snapshot["_at_dt"] - latest_at).total_seconds() / 3600.0 if latest_at else 9999.0
        if elapsed < min_interval_hours:
            return False
        # Analytics API snapshots are only comparable when YouTube/Zernio supplied a newer sync time.
        if snapshot.get("source") == "zernio_analytics":
            current_sync = snapshot.get("metrics_updated_at_utc") or ""
            previous_sync = latest.get("metrics_updated_at_utc") or ""
            if not current_sync or current_sync == previous_sync:
                return False
    snapshot["at_utc"] = snapshot.pop("_at_dt").strftime("%Y-%m-%dT%H:%M:%SZ")
    snapshots.append(snapshot)
    record["snapshots"] = snapshots[-3:]
    return True


def _sample_public_views(ledger: Dict[str, Dict[str, Any]], now: dt.datetime) -> int:
    eligible: List[Tuple[int, float, str, Dict[str, Any]]] = []
    for video_id, record in ledger.items():
        published = _parse_iso(record.get("published_at"))
        if not published or published > now:
            continue
        last_check = _parse_iso(record.get("last_public_check_utc"))
        if last_check and (now - last_check).total_seconds() < 6.0 * 3600.0:
            continue
        age_hours = (now - published).total_seconds() / 3600.0
        # Keep the newest catalog moving while reserving a rotating slot for evergreen back-catalog videos.
        bucket = 0 if age_hours <= (60 * 24) else 1
        last_check_ts = last_check.timestamp() if last_check else 0.0
        eligible.append((bucket, last_check_ts, video_id, record))

    recent = sorted((x for x in eligible if x[0] == 0), key=lambda x: (x[1], x[2]))
    evergreen = sorted((x for x in eligible if x[0] == 1), key=lambda x: (x[1], x[2]))
    selected: List[Tuple[int, float, str, Dict[str, Any]]] = recent[:2]
    if evergreen:
        selected.extend(evergreen[:1])
    if len(selected) < PUBLIC_VIEW_BUDGET:
        selected.extend(recent[2 : 2 + (PUBLIC_VIEW_BUDGET - len(selected))])

    checked = 0
    for _, _, video_id, record in selected[:PUBLIC_VIEW_BUDGET]:
        record["last_public_check_utc"] = _iso_utc(now)
        checked += 1
        stats = _public_youtube_views(video_id)
        if not stats:
            continue
        metrics = record.get("last_analytics_metrics") or record.get("pending_metrics") or {}
        latest_views = max(stats["views"], _as_int(metrics.get("views"), 0))
        latest_likes = max(stats["likes"], _as_int(metrics.get("likes"), 0))
        record["latest_public_views"] = latest_views
        record["latest_public_likes"] = latest_likes
        snapshot = {
            "_at_dt": now,
            "source": "public_youtube",
            "views": latest_views,
            "impressions": max(0, _as_int(metrics.get("impressions"), 0)),
            "likes": latest_likes,
            "comments": max(0, _as_int(metrics.get("comments"), 0)),
            "shares": max(0, _as_int(metrics.get("shares"), 0)),
            "ctr": metrics.get("ctr"),
            "metrics_updated_at_utc": str(metrics.get("metrics_updated_at_utc") or ""),
        }
        _push_snapshot(record, snapshot, MIN_SAMPLE_INTERVAL_HOURS)
        time.sleep(0.15)
    return checked


def _fetch_daily_views(api_key: str, account_id: str, video_id: str, published_at: str, now: dt.datetime) -> Optional[Dict[str, Any]]:
    published_dt = _parse_iso(published_at)
    earliest = now.date() - dt.timedelta(days=87)  # YouTube's daily-views endpoint caps the range at 90 days.
    from_date = max(published_dt.date(), earliest).isoformat() if published_dt else earliest.isoformat()
    to_date = (now.date() - dt.timedelta(days=3)).isoformat()
    if from_date > to_date:
        return None
    try:
        response = requests.get(
            f"{ZERNIO_BASE}/analytics/youtube/daily-views",
            headers=_headers(api_key),
            params={"accountId": account_id, "videoId": video_id, "fromDate": from_date, "toDate": to_date},
            timeout=(2.5, 6.0),
        )
        if response.status_code != 200:
            return None
        payload = response.json()
        days = [d for d in (payload.get("dailyViews") or []) if isinstance(d, dict)]
        total_views = sum(max(0, _as_int(d.get("views"), 0)) for d in days)
        total_weight = sum(max(0, _as_int(d.get("views"), 0)) for d in days)
        if total_weight:
            avp_num = sum((_as_float(d.get("averageViewPercentage")) or 0.0) * max(0, _as_int(d.get("views"), 0)) for d in days)
            avd_num = sum((_as_float(d.get("averageViewDuration")) or 0.0) * max(0, _as_int(d.get("views"), 0)) for d in days)
            avp = avp_num / total_weight
            avd = avd_num / total_weight
        else:
            avp = avd = None
        last_7 = sorted(days, key=lambda d: str(d.get("date") or ""))[-7:]
        return {
            "checked_at_utc": _iso_utc(now),
            "from_date": from_date,
            "to_date": to_date,
            "finalized_views_90d": max(total_views, _as_int(payload.get("totalViews"), 0)),
            "last_7d_views": sum(max(0, _as_int(d.get("views"), 0)) for d in last_7),
            "average_view_percentage": round(avp, 2) if avp is not None else None,
            "average_view_duration_seconds": round(avd, 2) if avd is not None else None,
            "subscribers_gained": sum(max(0, _as_int(d.get("subscribersGained"), 0)) for d in days),
            "last_synced_at": str(payload.get("lastSyncedAt") or ""),
            "has_analytics_scope": bool((payload.get("scopeStatus") or {}).get("hasAnalyticsScope", False)),
            "days_with_data": len(days),
        }
    except Exception:
        return None


def _fetch_retention(api_key: str, account_id: str, video_id: str, published_at: str, now: dt.datetime) -> Optional[Dict[str, Any]]:
    published_dt = _parse_iso(published_at)
    if not published_dt:
        return None
    to_date = now.date() - dt.timedelta(days=3)
    if published_dt.date() > to_date:
        return None
    from_date = max(published_dt.date(), now.date() - dt.timedelta(days=87))
    try:
        response = requests.get(
            f"{ZERNIO_BASE}/analytics/youtube/video-retention",
            headers=_headers(api_key),
            params={
                "accountId": account_id,
                "videoId": video_id,
                "fromDate": from_date.isoformat(),
                "toDate": to_date.isoformat(),
            },
            timeout=(2.5, 6.0),
        )
        if response.status_code != 200:
            return None
        payload = response.json()
        curve = [p for p in (payload.get("retentionCurve") or []) if isinstance(p, dict)]
        duration = _as_int(payload.get("durationSeconds"), 0)
        target_ratio = min(1.0, 3.0 / duration) if duration > 0 else 0.02
        first_point = min(curve, key=lambda p: abs((_as_float(p.get("elapsedVideoTimeRatio")) or 0.0) - target_ratio)) if curve else None
        early_relative = [
            _as_float(p.get("relativeRetentionPerformance"))
            for p in curve
            if (_as_float(p.get("elapsedVideoTimeRatio")) or 1.0) <= 0.15
            and _as_float(p.get("relativeRetentionPerformance")) is not None
        ]
        return {
            "checked_at_utc": _iso_utc(now),
            "relative_retention_early_median": round(statistics.median(early_relative), 4) if early_relative else None,
            "audience_watch_ratio_near_3s": round(_as_float(first_point.get("audienceWatchRatio")) or 0.0, 4) if first_point else None,
            "segment_metrics_available": bool(payload.get("segmentMetricsAvailable", False)),
            "point_count": len(curve),
            "note": str(payload.get("note") or "")[:240],
            "has_analytics_scope": bool((payload.get("scopeStatus") or {}).get("hasAnalyticsScope", False)),
        }
    except Exception:
        return None


def _refresh_one_detailed_signal(
    api_key: str,
    account_id: str,
    ledger: Dict[str, Dict[str, Any]],
    now: dt.datetime,
) -> Tuple[int, int]:
    eligible: List[Tuple[int, float, str, Dict[str, Any]]] = []
    for video_id, record in ledger.items():
        published = _parse_iso(record.get("published_at"))
        if not published or (now - published).total_seconds() < 72.0 * 3600.0:
            continue
        daily = record.get("youtube_daily_analytics") or {}
        ret = record.get("youtube_retention") or {}
        last_daily = _parse_iso(daily.get("checked_at_utc") or record.get("last_daily_analytics_attempt_utc"))
        last_ret = _parse_iso(ret.get("checked_at_utc") or record.get("last_retention_attempt_utc"))
        daily_due = not last_daily or (now - last_daily).total_seconds() >= DETAIL_FETCH_COOLDOWN_HOURS * 3600.0
        avg_pct = _as_float(daily.get("average_view_percentage"))
        retention_worthwhile = (
            _as_int(daily.get("finalized_views_90d"), 0) >= 50
            and (avg_pct is None or avg_pct < (50.0 if record.get("is_short") else 30.0))
        )
        ret_due = retention_worthwhile and (
            not last_ret or (now - last_ret).total_seconds() >= RETENTION_FETCH_COOLDOWN_HOURS * 3600.0
        )
        if daily_due or ret_due:
            oldest_check = min(
                [x.timestamp() for x in (last_daily, last_ret) if x is not None] or [0.0]
            )
            eligible.append((0 if not daily else 1, oldest_check, video_id, record))
    if not eligible:
        return 0, 0

    _, _, video_id, record = min(eligible, key=lambda x: (x[0], x[1], x[2]))
    daily_count = retention_count = 0
    daily = record.get("youtube_daily_analytics") or {}
    last_daily = _parse_iso(daily.get("checked_at_utc"))
    if not last_daily or (now - last_daily).total_seconds() >= DETAIL_FETCH_COOLDOWN_HOURS * 3600.0:
        result = _fetch_daily_views(api_key, account_id, video_id, record.get("published_at", ""), now)
        record["last_daily_analytics_attempt_utc"] = _iso_utc(now)
        if result:
            record["youtube_daily_analytics"] = result
            daily_count = 1
        else:
            # Store an attempt timestamp even when YouTube has no finalized data, to avoid noisy retries.
            record["youtube_daily_analytics"] = {"checked_at_utc": _iso_utc(now), "days_with_data": 0}

    ret = record.get("youtube_retention") or {}
    last_ret = _parse_iso(ret.get("checked_at_utc"))
    daily_result = record.get("youtube_daily_analytics") or {}
    avg_pct = _as_float(daily_result.get("average_view_percentage"))
    # Query the more detailed curve only after daily analytics indicate enough audience to diagnose retention.
    should_fetch_retention = (
        _as_int(daily_result.get("finalized_views_90d"), 0) >= 50
        and (avg_pct is None or avg_pct < (50.0 if record.get("is_short") else 30.0))
    )
    if should_fetch_retention and (not last_ret or (now - last_ret).total_seconds() >= RETENTION_FETCH_COOLDOWN_HOURS * 3600.0):
        result = _fetch_retention(api_key, account_id, video_id, record.get("published_at", ""), now)
        record["last_retention_attempt_utc"] = _iso_utc(now)
        if result:
            record["youtube_retention"] = result
            retention_count = 1
        else:
            record["youtube_retention"] = {"checked_at_utc": _iso_utc(now), "point_count": 0}
    time.sleep(0.1)
    return daily_count, retention_count


def _velocity(a: Dict[str, Any], b: Dict[str, Any]) -> Optional[float]:
    if not a or not b or a.get("source") != b.get("source"):
        return None
    ta, tb = _parse_iso(a.get("at_utc")), _parse_iso(b.get("at_utc"))
    if not ta or not tb:
        return None
    span = (tb - ta).total_seconds() / 3600.0
    if span < 12.0 or span > 45.0 * 24.0:
        return None
    delta = max(0, _as_int(b.get("views"), 0) - _as_int(a.get("views"), 0))
    return (delta * 24.0) / span


def _median(values: List[float]) -> Optional[float]:
    clean = [v for v in values if math.isfinite(v) and v >= 0]
    return statistics.median(clean) if clean else None


def _derive_diagnostics(ledger: Dict[str, Dict[str, Any]], now: dt.datetime) -> Dict[str, Any]:
    peers: Dict[bool, List[Dict[str, Any]]] = {True: [], False: []}
    for vid, rec in ledger.items():
        snaps = rec.get("snapshots") or []
        if len(snaps) >= 2 and not rec.get("is_short") == "unknown":
            age = (now - (_parse_iso(rec.get("published_at")) or now)).total_seconds() / 3600.0
            if age <= 180.0 * 24.0:
                peers[bool(rec.get("is_short"))].append(rec)

    baseline_velocity: Dict[bool, Optional[float]] = {}
    baseline_ctr: Dict[bool, Optional[float]] = {}
    baseline_retention: Dict[bool, Optional[float]] = {}
    for short_flag in (True, False):
        velocities: List[float] = []
        ctrs: List[float] = []
        retentions: List[float] = []
        for rec in peers[short_flag]:
            snaps = rec.get("snapshots") or []
            if len(snaps) >= 2:
                rate = _velocity(snaps[-2], snaps[-1])
                if rate is not None:
                    velocities.append(rate)
            cur = snaps[-1] if snaps else {}
            ctr = _as_float(cur.get("ctr"))
            impressions = _as_int(cur.get("impressions"), 0)
            if ctr is not None and impressions >= 500:
                ctrs.append(ctr)
            avg_pct = _as_float((rec.get("youtube_daily_analytics") or {}).get("average_view_percentage"))
            if avg_pct is not None:
                retentions.append(avg_pct)
        baseline_velocity[short_flag] = _median(velocities)
        baseline_ctr[short_flag] = _median(ctrs)
        baseline_retention[short_flag] = _median(retentions)

    stalled: List[Dict[str, Any]] = []
    for video_id, rec in ledger.items():
        published = _parse_iso(rec.get("published_at"))
        age_hours = (now - published).total_seconds() / 3600.0 if published else 0.0
        snaps = rec.get("snapshots") or []
        rec["age_hours"] = round(max(0.0, age_hours), 1)
        if age_hours < 72.0:
            rec["growth_diagnosis"] = {"status": "too_new", "reason": "analytics_window_not_mature"}
            continue
        if not snaps:
            rec["growth_diagnosis"] = {"status": "insufficient_data", "reason": "no_comparable_snapshot"}
            continue
        current = snaps[-1]
        views = _as_int(current.get("views"), 0)
        minimum_views = 35 if rec.get("is_short") else 50
        if views < minimum_views:
            rec["growth_diagnosis"] = {"status": "low_sample", "reason": "views_below_safe_threshold", "views": views}
            continue

        b_short = bool(rec.get("is_short"))
        min_base_interval = _velocity(snaps[-2], snaps[-1]) if len(snaps) >= 2 else None
        old_interval = _velocity(snaps[-3], snaps[-2]) if len(snaps) >= 3 else None
        base = baseline_velocity.get(b_short)
        threshold = max(2.0, views * 0.01)
        recent_flat = min_base_interval is not None and min_base_interval <= threshold
        older_flat = old_interval is not None and old_interval <= threshold
        if base is not None and base >= 4.0:
            recent_flat = recent_flat and min_base_interval <= (base * 0.25)
            older_flat = older_flat and old_interval <= (base * 0.25) if old_interval is not None else False
        stall_streak = (2 if older_flat and recent_flat else (1 if recent_flat else 0))

        impressions = _as_int(current.get("impressions"), 0)
        ctr = _as_float(current.get("ctr"))
        ctr_base = baseline_ctr.get(b_short)
        ctr_sync = _parse_iso(current.get("metrics_updated_at_utc"))
        ctr_fresh = bool(ctr_sync and (now - ctr_sync).total_seconds() <= 14.0 * 86400.0)
        weak_ctr = bool(
            not rec.get("is_short")
            and impressions >= 500
            and ctr is not None
            and ctr_fresh
            and (ctr < 0.02 or (ctr_base is not None and ctr < 0.72 * ctr_base))
        )
        daily = rec.get("youtube_daily_analytics") or {}
        retention = rec.get("youtube_retention") or {}
        avg_pct = _as_float(daily.get("average_view_percentage"))
        retention_base = baseline_retention.get(b_short)
        weak_retention = False
        if avg_pct is not None and _as_int(daily.get("finalized_views_90d"), 0) >= 50:
            if retention_base is not None and retention_base > 0:
                weak_retention = avg_pct < 0.72 * retention_base
            elif rec.get("is_short"):
                weak_retention = avg_pct < 45.0
            else:
                weak_retention = avg_pct < 20.0
        relative_curve = _as_float(retention.get("relative_retention_early_median"))
        if relative_curve is not None and relative_curve < 0.36:
            weak_retention = True

        if min_base_interval is None:
            status = "insufficient_data"
            reason = "need_two_fresh_samples_at_least_12h_apart"
        elif stall_streak < 2:
            status = "growing_or_slowing"
            reason = "not_two_consecutive_stalled_intervals"
        else:
            status = "plateau"
            if weak_ctr:
                reason = "weak_click_packaging_signal"
            elif weak_retention:
                reason = "weak_viewer_retention_signal"
            elif impressions < 100:
                reason = "limited_or_unmeasured_distribution"
            else:
                reason = "view_growth_flat_cause_not_proven"

        rate = round(min_base_interval, 2) if min_base_interval is not None else None
        rec["growth_diagnosis"] = {
            "status": status,
            "reason": reason,
            "views": views,
            "views_per_day_recent": rate,
            "channel_format_median_views_per_day": round(base, 2) if base is not None else None,
            "stalled_intervals": stall_streak,
            "impressions": impressions,
            "ctr": round(ctr, 4) if ctr is not None else None,
            "weak_ctr": weak_ctr,
            "average_view_percentage": round(avg_pct, 2) if avg_pct is not None else None,
            "weak_retention": weak_retention,
            "has_retention_curve": bool(retention.get("point_count")),
        }
        if status == "plateau":
            stalled.append({"video_id": video_id, "record": rec, "diagnosis": rec["growth_diagnosis"]})

    return {
        "baseline_velocity": baseline_velocity,
        "baseline_ctr": baseline_ctr,
        "baseline_retention": baseline_retention,
        "stalled": stalled,
    }


def _playlist_spec(channel: Dict[str, Any]) -> Tuple[str, str]:
    brand = str(channel.get("brand_name") or "القناة").strip()
    if channel.get("language") == "ar":
        if "mystery" in str(channel.get("id") or ""):
            title = f"ألغاز القضايا والتفاصيل الخفية كاملة | {brand}"
            description = f"حلقات كاملة من ألغاز القضايا والتفاصيل المنطقية المشوقة على قناة {brand}."
        else:
            title = f"حكايات التشويق النفسي كاملة | {brand}"
            description = f"حلقات كاملة من حكايات التشويق النفسي الواقعي على قناة {brand}."
    else:
        title = f"Complete Mystery and Suspense Stories | {brand}"
        description = f"Full-length grounded mystery and suspense stories from {brand}."
    return title[:150], description[:4500]


def _ensure_playlist(channel: Dict[str, Any], ch_state: Dict[str, Any], api_key: str, account_id: str) -> str:
    saved_id = str(ch_state.get("growth_playlist_id") or "").strip()
    if saved_id:
        return saved_id
    target_title, description = _playlist_spec(channel)
    brand = str(channel.get("brand_name") or "").strip().casefold()
    try:
        response = requests.get(
            f"{ZERNIO_BASE}/accounts/{quote(account_id, safe='')}/youtube-playlists",
            headers=_headers(api_key),
            timeout=(2.5, 6.0),
        )
        if response.status_code == 200:
            playlists = response.json().get("playlists") or []
            matching = next((p for p in playlists if brand and brand in str(p.get("title") or "").casefold()), None)
            if matching and matching.get("id"):
                ch_state["growth_playlist_id"] = str(matching["id"])
                ch_state["growth_playlist_title"] = str(matching.get("title") or target_title)
                return str(matching["id"])
        else:
            return ""
        created = requests.post(
            f"{ZERNIO_BASE}/accounts/{quote(account_id, safe='')}/youtube-playlists",
            headers=_headers(api_key),
            json={"title": target_title, "description": description, "privacy": "public"},
            timeout=(2.5, 7.0),
        )
        if created.status_code not in (200, 201):
            return ""
        playlist = created.json().get("playlist") or {}
        playlist_id = str(playlist.get("id") or "").strip()
        if playlist_id:
            ch_state["growth_playlist_id"] = playlist_id
            ch_state["growth_playlist_title"] = str(playlist.get("title") or target_title)
        return playlist_id
    except Exception:
        return ""


def _update_youtube_metadata(
    api_key: str,
    record: Dict[str, Any],
    account_id: str,
    fields: Dict[str, Any],
) -> Tuple[bool, str]:
    post_ids = [str(p).strip() for p in (record.get("post_ids") or []) if str(p).strip()]
    if not post_ids:
        return False, "missing_zernio_post_id"
    body = {"platform": "youtube", "accountId": account_id, **fields}
    last_status = ""
    for idx, post_id in enumerate(dict.fromkeys(post_ids)):
        try:
            response = requests.post(
                f"{ZERNIO_BASE}/posts/{quote(post_id, safe='')}/update-metadata",
                headers=_headers(api_key),
                json=body,
                timeout=(2.5, 10.0),
            )
            if response.status_code < 400:
                return True, f"http_{response.status_code}"
            last_status = f"http_{response.status_code}"
            # The analytics feed can expose either the original Zernio id or its synced copy id.
            # Retry the alternate identifier only when the first is not found.
            if response.status_code != 404 or idx >= len(post_ids) - 1:
                break
        except Exception as exc:
            last_status = type(exc).__name__
            break
    return False, last_status or "update_failed"


def _make_thumbnail_variant(source_url: str, phrase: str, brand: str, language: str, output_path: Path) -> bool:
    if not source_url or not phrase.strip():
        return False
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageOps

        response = requests.get(source_url, headers=YT_PAGE_HEADERS, timeout=(2.5, 8.0))
        response.raise_for_status()
        if len(response.content) > 12 * 1024 * 1024 or len(response.content) < 2048:
            return False
        from io import BytesIO
        image = Image.open(BytesIO(response.content)).convert("RGB")
        if image.width < 640 or image.height < 360:
            return False
        image = ImageOps.fit(image, (1280, 720), method=Image.Resampling.LANCZOS)
        canvas = image.convert("RGBA")
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        draw.rounded_rectangle((32, 412, 1248, 706), radius=34, fill=(6, 10, 24, 218), outline=(255, 213, 54, 245), width=4)
        canvas = Image.alpha_composite(canvas, overlay)
        draw = ImageDraw.Draw(canvas)

        root = Path(__file__).resolve().parent
        preferred = root / "fonts" / "Cairo-Variable.ttf" if language == "ar" else Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
        fallback = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
        font_path = preferred if preferred.exists() else fallback
        phrase = re.sub(r"\s+", " ", phrase.strip())[:48]
        words = phrase.split()
        if not words or len(words) > 6:
            return False
        lines: List[str] = []
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if len(candidate) > 22 and line:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
        if len(lines) > 3:
            return False
        text = "\n".join(lines)
        direction = {"direction": "rtl", "language": "ar"} if language == "ar" else {}
        font = None
        for size in (84, 76, 68, 60):
            try:
                font = ImageFont.truetype(str(font_path), size, layout_engine=ImageFont.Layout.RAQM)
            except Exception:
                font = ImageFont.truetype(str(font_path), size)
            max_width = 1150
            widths = []
            for part in lines:
                try:
                    bbox = draw.textbbox((0, 0), part, font=font, stroke_width=3, **direction)
                except Exception:
                    direction = {}
                    bbox = draw.textbbox((0, 0), part, font=font, stroke_width=3)
                widths.append(bbox[2] - bbox[0])
            if max(widths or [0]) <= max_width:
                break
        if font is None:
            return False
        step = int(font.size * 1.08)
        first_y = 555 - ((len(lines) - 1) * step // 2)
        for idx, text_line in enumerate(lines):
            try:
                draw.text((640, first_y + idx * step), text_line, font=font, fill=(255, 255, 255, 255), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0, 255), **direction)
            except Exception:
                draw.text((640, first_y + idx * step), text_line, font=font, fill=(255, 255, 255, 255), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0, 255))
        brand_font = ImageFont.truetype(str(font_path), 27)
        try:
            draw.text((640, 674), brand[:45], font=brand_font, fill=(255, 222, 65, 255), anchor="mm", **direction)
        except Exception:
            draw.text((640, 674), brand[:45], font=brand_font, fill=(255, 222, 65, 255), anchor="mm")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.convert("RGB").save(output_path, format="JPEG", quality=93, optimize=True)
        return output_path.exists() and output_path.stat().st_size > 10_000
    except Exception:
        return False


def _playlist_target(ledger: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    candidates = []
    for rec in ledger.values():
        if rec.get("playlist_added") or rec.get("is_short"):
            continue
        duration = _as_int(rec.get("duration_seconds"), 0)
        title = str(rec.get("title") or "").lower()
        if duration < 300 and not any(x in title for x in ("قصة كاملة", "full story", "complete story", "full episode")):
            continue
        if not rec.get("post_ids"):
            continue
        published = _parse_iso(rec.get("published_at")) or _utc_now()
        candidates.append((published, rec))
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1] if candidates else None


def _title_prompt(
    channel: Dict[str, Any],
    record: Dict[str, Any],
    diagnosis: Dict[str, Any],
    winners: List[Dict[str, Any]],
) -> Tuple[str, str]:
    const = channel.get("constitution") or {}
    lang = channel.get("language", "ar")
    winner_titles = [str(w.get("title") or "") for w in winners[:3]]
    metrics = {
        "views": diagnosis.get("views"),
        "recent_views_per_day": diagnosis.get("views_per_day_recent"),
        "format": "short" if record.get("is_short") else "long-form",
        "reason": diagnosis.get("reason"),
    }
    if lang == "ar":
        system = (
            f"أنت محرر يوتيوب مسؤول لقناة {channel.get('brand_name')}، وتلتزم بالدستور التالي حرفياً: "
            f"{const.get('core_identity', '')} لا تخترع أحداثاً أو حقائق أو وعوداً لا تظهر في النص، ولا تحرق النهاية، "
            "ولا تستخدم تضليلاً أو مبالغة أو عبارات سبام. مهمتك تعديل تغليف العنوان فقط لنفس الفيديو ونفس القصة."
        )
        user = (
            f"العنوان الحالي: {record.get('title', '')}\n"
            f"بصمة القصة الأصلية: {str(record.get('story_seed') or '')[:240]}\n"
            f"ملخص/وصف الفيديو الأصلي: {str(record.get('description_excerpt') or '')[:420]}\n"
            f"بيانات النمو: {metrics}\n"
            f"عناوين ناجحة داخل القناة للاستلهام من الإيقاع فقط، لا للتكرار: {winner_titles}\n"
            "اكتب عنواناً مصرياً واضحاً ومحدداً، واعداً بما يقدمه الفيديو فعلاً، فضولياً من غير حرق أو ادعاء كاذب، وبحد أقصى 95 حرفاً. "
            "لا تغيّر التخصص أو اللهجة، ولا تكرر عنواناً منشوراً. أخرج JSON فقط بالشكل: {\"new_title\":\"...\",\"thumbnail_phrase\":\"عبارة غلاف من 2 إلى 4 كلمات\"}. اجعل عبارة الغلاف مطابقة للقصة وبلا حرق أو ادعاء زائد."
        )
    else:
        system = (
            f"You are a responsible YouTube metadata editor for {channel.get('brand_name')}. Immutable channel constitution: "
            f"{const.get('core_identity', '')} Do not invent plot facts, claims, or promises; do not spoil the ending or use spam/caps. "
            "Edit the packaging of this same video only."
        )
        user = (
            f"Current title: {record.get('title', '')}\n"
            f"Original story fingerprint: {str(record.get('story_seed') or '')[:240]}\n"
            f"Original video description: {str(record.get('description_excerpt') or '')[:420]}\n"
            f"Growth signals: {metrics}\n"
            f"Winning channel titles for rhythm only (do not copy): {winner_titles}\n"
            "Write one clear, specific, truthful, non-spoiler title, max 95 characters, aligned with the video's actual story and channel niche. "
            "Do not repeat a published title. Return JSON only: {\"new_title\":\"...\",\"thumbnail_phrase\":\"a truthful 2-4 word cover phrase\"}. The cover phrase must match the same story and avoid spoilers or overclaims."
        )
    return system, user


def _anchor_terms(text: str) -> set:
    normalized = unicodedata.normalize("NFKC", str(text or "")).casefold()
    normalized = re.sub(r"[\u064b-\u065f\u0670]", "", normalized)
    normalized = normalized.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي"}))
    stop = {
        "the", "and", "that", "this", "with", "from", "into", "when", "what", "who", "where", "your", "their", "full", "story", "episode", "true", "real",
        "قصة", "قصه", "كاملة", "كامله", "حقيقية", "حقيقيه", "اللي", "الذي", "التي", "هذا", "هذه", "كان", "كانت", "في", "من", "على", "إلى", "عن", "مع", "قبل", "بعد",
    }
    terms = set()
    for token in re.findall(r"[a-z0-9]+|[\u0600-\u06ff]+", normalized):
        if len(token) < 3 or token in stop:
            continue
        terms.add(token)
        if token.startswith("ال") and len(token) > 4:
            terms.add(token[2:])
    return terms


def _shares_story_anchor(candidate: str, record: Dict[str, Any]) -> bool:
    source = f"{record.get('title', '')} {record.get('story_seed', '')} {record.get('description_excerpt', '')}"
    return bool(_anchor_terms(candidate) & _anchor_terms(source))


def _try_thumbnail_experiment(
    channel: Dict[str, Any],
    record: Dict[str, Any],
    phrase: str,
    api_key: str,
    account_id: str,
    playlist_id: str = "",
) -> Tuple[bool, str]:
    if record.get("is_short") or _as_int(record.get("thumbnail_edits"), 0) >= MAX_THUMBNAIL_EDITS_PER_VIDEO:
        return False, "thumbnail_change_limit_or_short"
    source_url = str(record.get("thumbnail_url") or "")
    if not source_url:
        return False, "no_current_thumbnail"
    with tempfile.TemporaryDirectory(prefix="video-growth-thumb-") as temp_dir:
        image_path = Path(temp_dir) / f"{record.get('video_id', 'video')}-alternate.jpg"
        if not _make_thumbnail_variant(source_url, phrase, str(channel.get("brand_name") or ""), channel.get("language", "ar"), image_path):
            return False, "thumbnail_render_unavailable"
        try:
            from empire_publisher import upload_media_to_zernio
            uploaded_url = upload_media_to_zernio(api_key, image_path, mime_type="image/jpeg")
        except Exception as exc:
            return False, f"thumbnail_upload_{type(exc).__name__}"
        fields: Dict[str, Any] = {"thumbnailUrl": uploaded_url}
        if playlist_id and _playlist_target_is_record(record):
            fields["playlistId"] = playlist_id
        ok, status = _update_youtube_metadata(api_key, record, account_id, fields)
        if not ok:
            return False, f"thumbnail_metadata_{status}"
        record["thumbnail_url"] = uploaded_url
        record["thumbnail_edits"] = _as_int(record.get("thumbnail_edits"), 0) + 1
        record["snapshots"] = (record.get("snapshots") or [])[-1:]
        record["playlist_added"] = bool(record.get("playlist_added") or "playlistId" in fields)
        record.setdefault("actions", []).append({
            "at_utc": _iso_utc(),
            "field": "thumbnail",
            "reason": "weak_click_packaging_signal",
            "thumbnail_phrase": phrase[:80],
            "status": status,
        })
        record["actions"] = record["actions"][-8:]
        record["last_growth_action_utc"] = _iso_utc()
        return True, status


def _playlist_target_is_record(record: Dict[str, Any]) -> bool:
    duration = _as_int(record.get("duration_seconds"), 0)
    title = str(record.get("title") or "").lower()
    return not record.get("is_short") and (duration >= 300 or any(x in title for x in ("قصة كاملة", "full story", "complete story", "full episode")))


def _apply_one_growth_action(
    channel: Dict[str, Any],
    ch_state: Dict[str, Any],
    director_state: Dict[str, Any],
    ledger: Dict[str, Dict[str, Any]],
    stalled: List[Dict[str, Any]],
    api_key: str,
    account_id: str,
    llm_json_fn: Optional[Callable[..., Dict[str, Any]]],
    llm_key: str,
    text_validator: Optional[Callable[..., Tuple[bool, str]]],
    playlist_id: str,
    now: dt.datetime,
) -> Dict[str, Any]:
    # A measured low CTR can justify a cover experiment; otherwise start with one title experiment.
    candidates = sorted(
        stalled,
        key=lambda item: (
            0 if item["diagnosis"].get("weak_ctr") else 1,
            -_as_int(item["diagnosis"].get("views"), 0),
            -_as_float(item["record"].get("age_hours")) if _as_float(item["record"].get("age_hours")) is not None else 0,
        ),
    )
    if llm_json_fn and llm_key and text_validator:
        for item in candidates[:3]:
            record = item["record"]
            diagnosis = item["diagnosis"]
            # Don't change metadata when retention is the bottleneck or distribution is too small to diagnose.
            if diagnosis.get("reason") in ("weak_viewer_retention_signal", "limited_or_unmeasured_distribution"):
                continue
            if not any(str(x).strip() for x in (record.get("post_ids") or [])):
                continue
            last_action = _parse_iso(record.get("last_growth_action_utc"))
            if last_action and (now - last_action).total_seconds() < TITLE_EDIT_COOLDOWN_HOURS * 0.5:
                continue
            prior_ids = set(str(x) for x in director_state.get("rescued_post_ids", []))
            post_id = next((str(x).strip() for x in (record.get("post_ids") or []) if str(x).strip()), "")
            actions = record.get("actions") or []
            title_edits = max(_as_int(record.get("title_edits"), 0), sum(1 for a in actions if a.get("field") == "title"))
            # V15 rescue history counts as an earlier title experiment.
            if post_id and post_id in prior_ids:
                title_edits = max(1, title_edits)
            title_cooldown_ok = not last_action or (now - last_action).total_seconds() >= TITLE_EDIT_COOLDOWN_HOURS
            weak_ctr = bool(diagnosis.get("weak_ctr"))
            if title_edits >= MAX_TITLE_EDITS_PER_VIDEO and (
                not weak_ctr or _as_int(record.get("thumbnail_edits"), 0) >= MAX_THUMBNAIL_EDITS_PER_VIDEO
            ):
                continue
            system, user = _title_prompt(channel, record, diagnosis, ch_state.get("top_winners") or [])
            try:
                result = llm_json_fn(llm_key, system, user, 350)
                if not isinstance(result, dict):
                    continue
            except Exception:
                continue

            if weak_ctr and not record.get("is_short") and _as_int(record.get("thumbnail_edits"), 0) < MAX_THUMBNAIL_EDITS_PER_VIDEO:
                phrase = str(result.get("thumbnail_phrase") or "").strip()
                if phrase and len(phrase.split()) <= 5 and _shares_story_anchor(phrase, record):
                    valid_phrase, _ = text_validator(phrase, channel, require_language_match=True)
                    if valid_phrase:
                        ok_thumb, thumb_status = _try_thumbnail_experiment(
                            channel, record, phrase, api_key, account_id, playlist_id=playlist_id
                        )
                        if ok_thumb:
                            return {"action": "thumbnail", "video_id": record.get("video_id"), "status": thumb_status}
                        # A network error after metadata submission is ambiguous; do not risk a second edit this pass.
                        if str(thumb_status).startswith("thumbnail_metadata_"):
                            return {"action": "none", "reason": thumb_status}

            if title_edits >= MAX_TITLE_EDITS_PER_VIDEO or not title_cooldown_ok:
                continue
            try:
                new_title = re.sub(r"\s+", " ", str(result.get("new_title") or "")).strip()
                if not new_title or len(new_title) > 100 or len(new_title) < 12 or new_title == str(record.get("title") or ""):
                    continue
                normalized_title = re.sub(r"[^\w\u0600-\u06FF]+", " ", new_title.casefold()).strip()
                duplicate = any(
                    other_id != record.get("video_id")
                    and re.sub(r"[^\w\u0600-\u06FF]+", " ", str(other.get("title") or "").casefold()).strip() == normalized_title
                    for other_id, other in ledger.items()
                )
                if duplicate or not _shares_story_anchor(new_title, record):
                    continue
                valid, _ = text_validator(new_title, channel, require_language_match=True)
                if not valid:
                    continue
                fields: Dict[str, Any] = {"title": new_title}
                add_playlist = bool(playlist_id and _playlist_target_is_record(record) and not record.get("playlist_added"))
                if add_playlist:
                    fields["playlistId"] = playlist_id
                ok, status = _update_youtube_metadata(api_key, record, account_id, fields)
                if ok:
                    old_title = str(record.get("title") or "")
                    record["title"] = new_title
                    record["title_edits"] = title_edits + 1
                    record["last_title_edit_utc"] = _iso_utc(now)
                    record["snapshots"] = (record.get("snapshots") or [])[-1:]
                    record["playlist_added"] = bool(record.get("playlist_added") or add_playlist)
                    record.setdefault("actions", []).append({
                        "at_utc": _iso_utc(now),
                        "field": "title",
                        "reason": str(diagnosis.get("reason") or "confirmed_plateau"),
                        "old_title": old_title[:150],
                        "new_title": new_title[:150],
                        "status": status,
                    })
                    record["actions"] = record["actions"][-8:]
                    record["last_growth_action_utc"] = _iso_utc(now)
                    director_state.setdefault("rescued_post_ids", []).append(post_id)
                    director_state["rescued_post_ids"] = list(dict.fromkeys(director_state["rescued_post_ids"]))[-200:]
                    return {"action": "title", "video_id": record.get("video_id"), "status": status}
            except Exception:
                continue

    # If no evidence-gated title/thumbnail edit was ready, add one long-form video to its
    # channel-owned public playlist. This is a session-navigation improvement, not an algorithm guarantee.
    target = _playlist_target(ledger) if playlist_id else None
    if target:
        fields = {"playlistId": playlist_id}
        ok, status = _update_youtube_metadata(api_key, target, account_id, fields)
        if ok:
            target["playlist_added"] = True
            target["playlist_added_utc"] = _iso_utc(now)
            target.setdefault("actions", []).append({"at_utc": _iso_utc(now), "field": "playlist", "status": status})
            target["actions"] = target["actions"][-8:]
            return {"action": "playlist", "video_id": target.get("video_id"), "status": status}
        return {"action": "none", "reason": f"playlist_update_{status}"}
    return {"action": "none", "reason": "no_eligible_metadata_change"}


def _lessons_from_stalls(channel: Dict[str, Any], stalled: List[Dict[str, Any]]) -> List[str]:
    lang = channel.get("language", "ar")
    reasons = {item["diagnosis"].get("reason") for item in stalled}
    lessons: List[str] = []
    if "weak_viewer_retention_signal" in reasons:
        lessons.append(
            "في فيديوهات ناضجة ظهر احتفاظ أضعف من خط القناة: شدّدوا أول لقطة/جملة، وابدؤوا بالفعل أو الدليل فوراً، من غير تغيير التخصص أو حرق النهاية."
            if lang == "ar" else
            "Mature uploads show weaker-than-channel retention: tighten the first visual and sentence, start on the concrete event/clue, and keep the same niche with no spoilers."
        )
    if "weak_click_packaging_signal" in reasons:
        lessons.append(
            "في بعض الفيديوهات ذات بيانات نقر كافية، التغليف أضعف من خط القناة: اجعلوا العنوان/الغلاف يقدمان وعداً محدداً وصادقاً للقصة نفسها."
            if lang == "ar" else
            "Some videos with adequate click data have weaker packaging: make the title/cover promise more specific and truthful to the same story."
        )
    if "limited_or_unmeasured_distribution" in reasons or "view_growth_flat_cause_not_proven" in reasons:
        lessons.append(
            "التوزيع بطيء لكن السبب غير مثبت من البيانات الحالية؛ لا تغيّروا الهوية ولا تكرروا التعديل عشوائياً، واستخدموا موضوعاً وعنواناً أدق للحلقات القادمة."
            if lang == "ar" else
            "Distribution is slow but the available data does not prove why; do not drift niches or churn metadata—use a more specific topic/title on future uploads."
        )
    return lessons[:3]


def run_video_growth_cycle(
    channel: Dict[str, Any],
    director_state: Dict[str, Any],
    growth_state: Optional[Dict[str, Any]] = None,
    llm_json_fn: Optional[Callable[..., Dict[str, Any]]] = None,
    llm_key: str = "",
    text_validator: Optional[Callable[..., Tuple[bool, str]]] = None,
) -> Dict[str, Any]:
    """One bounded, fail-open growth review for a channel; never blocks publishing on API errors."""
    now = _utc_now()
    cid = str(channel.get("id") or "unknown")
    prefix = str(channel.get("env_prefix") or "")
    api_key = os.environ.get(f"{prefix}_ZERNIO_KEY", "").strip()
    account_id = str((channel.get("accounts") or {}).get("youtube") or "")
    ch_state = director_state.setdefault("channels", {}).setdefault(cid, {})
    growth_channel_state = (
        growth_state.setdefault("channels", {}).setdefault(cid, {})
        if growth_state is not None else ch_state
    )
    ledger = growth_channel_state.setdefault("youtube_video_ledger", {})
    summary: Dict[str, Any] = {
        "last_run_utc": _iso_utc(now),
        "available": bool(api_key and account_id),
        "tracked_videos": len(ledger),
        "analytics_page": 0,
        "live_views_checked": 0,
        "daily_analytics_checked": 0,
        "retention_checked": 0,
        "plateau_videos": 0,
        "title_experiments": 0,
        "thumbnail_experiments": 0,
        "playlist_additions": 0,
        "latest_action": "none",
        "cases": [],
        "lessons": [],
    }
    if not api_key or not account_id:
        ch_state["video_growth_summary"] = summary
        return summary

    # Fetch one 100-post page per pass, rotating through the channel's full one-year Zernio archive.
    page = max(1, _as_int(growth_channel_state.get("video_growth_page_cursor"), 1))
    posts, pages, page_status = _analytics_page(api_key, account_id, page, now)
    if page_status != "ok" and page != 1:
        posts, pages, page_status = _analytics_page(api_key, account_id, 1, now)
        page = 1
    if pages and page > pages:
        posts, pages, page_status = _analytics_page(api_key, account_id, 1, now)
        page = 1
    if page_status == "ok":
        growth_channel_state["video_growth_page_cursor"] = 1 if page >= max(1, pages) else page + 1
        summary["analytics_page"] = page
        for post in posts:
            _upsert_video_record(channel, post, ledger, now)
    else:
        summary["analytics_warning"] = page_status

    # Every pass samples a few live counters across the catalog; failed fetches are cooled down too.
    summary["live_views_checked"] = _sample_public_views(ledger, now)

    daily_count, retention_count = _refresh_one_detailed_signal(api_key, account_id, ledger, now)
    summary["daily_analytics_checked"] = daily_count
    summary["retention_checked"] = retention_count

    diagnostics = _derive_diagnostics(ledger, now)
    stalled = diagnostics["stalled"]
    summary["tracked_videos"] = len(ledger)
    summary["plateau_videos"] = len(stalled)
    summary["lessons"] = _lessons_from_stalls(channel, stalled)

    # Keep a small, readable case list instead of copying the full archive into every report.
    ranked = sorted(
        stalled,
        key=lambda item: (
            0 if item["diagnosis"].get("weak_ctr") else 1,
            0 if item["diagnosis"].get("weak_retention") else 1,
            -_as_int(item["diagnosis"].get("views"), 0),
        ),
    )
    for item in ranked[:5]:
        rec, diag = item["record"], item["diagnosis"]
        prev = (rec.get("snapshots") or [])[-2] if len(rec.get("snapshots") or []) > 1 else {}
        delta = max(0, _as_int(diag.get("views"), 0) - _as_int(prev.get("views"), 0)) if prev else None
        summary["cases"].append({
            "video_id": rec.get("video_id"),
            "title": str(rec.get("title") or "")[:110],
            "url": rec.get("url", ""),
            "age_hours": rec.get("age_hours"),
            "views": diag.get("views"),
            "views_delta_since_sample": delta,
            "views_per_day_recent": diag.get("views_per_day_recent"),
            "diagnosis": diag.get("reason"),
            "ctr": diag.get("ctr"),
            "average_view_percentage": diag.get("average_view_percentage"),
        })

    # Prepare a channel-owned playlist once and make at most one metadata mutation per pass.
    playlist_id = _ensure_playlist(channel, growth_channel_state, api_key, account_id)
    action = _apply_one_growth_action(
        channel=channel,
        ch_state=ch_state,
        director_state=director_state,
        ledger=ledger,
        stalled=stalled,
        api_key=api_key,
        account_id=account_id,
        llm_json_fn=llm_json_fn,
        llm_key=llm_key,
        text_validator=text_validator,
        playlist_id=playlist_id,
        now=now,
    )
    summary["latest_action"] = str(action.get("action") or "none")
    if action.get("action") == "title":
        summary["title_experiments"] = 1
    elif action.get("action") == "thumbnail":
        summary["thumbnail_experiments"] = 1
    elif action.get("action") == "playlist":
        summary["playlist_additions"] = 1
    if action.get("reason"):
        summary["action_note"] = action["reason"]
    if action.get("video_id"):
        summary["action_video_id"] = action["video_id"]

    title_total = sum(_as_int(rec.get("title_edits"), 0) for rec in ledger.values())
    thumb_total = sum(_as_int(rec.get("thumbnail_edits"), 0) for rec in ledger.values())
    playlist_total = sum(1 for rec in ledger.values() if rec.get("playlist_added"))
    summary["title_experiments_total"] = title_total
    summary["thumbnail_experiments_total"] = thumb_total
    summary["playlist_additions_total"] = playlist_total

    ch_state["growth_lessons"] = summary["lessons"]
    ch_state["video_growth_summary"] = summary
    # Bound action history; retain a two-year-plus catalog without copying it into the pretty director report.
    for rec in ledger.values():
        rec.pop("pending_metrics", None)
        rec["actions"] = (rec.get("actions") or [])[-8:]
    if len(ledger) > MAX_TRACKED_VIDEOS_PER_CHANNEL:
        oldest = sorted(
            ledger,
            key=lambda vid: _parse_iso((ledger[vid] or {}).get("published_at")) or dt.datetime.min.replace(tzinfo=UTC),
        )[: len(ledger) - MAX_TRACKED_VIDEOS_PER_CHANNEL]
        for video_id in oldest:
            ledger.pop(video_id, None)
    growth_channel_state["youtube_video_ledger"] = ledger
    return summary
