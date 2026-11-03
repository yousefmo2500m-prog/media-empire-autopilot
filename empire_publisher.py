# -*- coding: utf-8 -*-
"""
ناشر الإمبراطورية V14.0 — محرك الانضباط الزمني بالثانية والشفاء الذاتي (Zero-Miss Exact-Minute Cloud Scheduler)
- يقفل الموعد اليومي الرسمي بالثانية (`scheduledFor` بتوقيت الذروة) داخل سحابة Zernio عند التحضير المبكر، وينشر فوراً (`publishNow`) لأي قناة تأخر موعدها!
- يفحص سحابة Zernio مباشرة (`resolve_channel_slot_status`) لاكتشاف أي قناة لم تُجدول أو لم تُنشر اليوم وتعويضها تلقائياً بدون أي تكرار!
- يضع فاصل أمان 8–10 دقائق بين الفيلم الطويل والموجة الأولى من الشورتس لمنع تصادم جلسات رفع يوتيوب المتزامنة (`400 session init`) نهائياً!
- يرفع الأغلفة المخصصة لكل من الفيلم الطويل (`16:9` المتمركز) والشورتس/الريلز/تيك توك (`9:16` الطولي) مع إعادة المحاولة التلقائية ضد أي خطأ شبكي عابر!
"""

import datetime as dt
import os
import re
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


def _parse_iso_utc(raw_ts: Any) -> Optional[dt.datetime]:
    if not raw_ts:
        return None
    s = str(raw_ts).strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        parsed = dt.datetime.fromisoformat(s)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc)
    except Exception:
        return None


def _is_long_episode_post(post_obj: Dict[str, Any]) -> bool:
    status = str(post_obj.get("status") or "").lower()
    if status in ("failed", "cancelled", "canceled", "rejected", "draft"):
        return False

    media = post_obj.get("mediaItems") or []
    if not any(str(m.get("type") or "").lower() == "video" for m in media):
        return False

    for m in media:
        m_url = str(m.get("url") or "").lower()
        if "_short_" in m_url or "short_" in m_url:
            return False

    title_txt = str(post_obj.get("title") or "").lower()
    content_txt = str(post_obj.get("content") or "").lower()
    combined_head = f"{title_txt}\n{content_txt[:220]}"
    if any(tag in combined_head for tag in ("#shorts", "#شورتس", "#ريلز", "#reels")):
        return False

    plats = post_obj.get("platforms") or []
    has_valid_platform = False
    for pl in plats:
        spec = pl.get("platformSpecificData") or {}
        if str(spec.get("contentType") or "").lower() == "reel":
            return False
        pl_title = str(spec.get("title") or "").lower()
        if "#shorts" in pl_title:
            return False
        pl_st = str(pl.get("status") or status).lower()
        if pl_st not in ("failed", "cancelled", "canceled", "rejected"):
            has_valid_platform = True

    return has_valid_platform or (not plats)


def resolve_channel_slot_status(
    ch: Dict[str, Any],
    now_utc: Optional[dt.datetime] = None,
    pre_schedule_horizon_hours: float = 14.5,
) -> Dict[str, Any]:
    """
    يفحص سحابة Zernio مباشرة ليحدد بدقة 100%:
    1) هل فات موعد الأمس القريب (مثلاً قناة 23:45 UTC عند الفحص بعد منتصف الليل) ولم يُنشر؟ -> تعويض فوري!
    2) هل موعد اليوم الرسمي مجدول أو منشور بالفعل في نافذته؟ -> تخطي آمن بدون تكرار!
    3) هل حان وقت التحضير المبكر لموعد اليوم أو فات موعد اليوم؟ -> إنتاج وجدولة بالثانية أو نشر فوري!
    """
    if now_utc is None:
        now_utc = dt.datetime.now(dt.timezone.utc)

    prefix = ch["env_prefix"]
    main_key = os.environ.get(f"{prefix}_ZERNIO_KEY", "").strip()
    t_hour = int(ch.get("target_utc_hour", 16))
    t_min = int(ch.get("target_utc_minute", 15))

    today_slot = dt.datetime(
        now_utc.year, now_utc.month, now_utc.day, t_hour, t_min, 0, tzinfo=dt.timezone.utc
    )
    yesterday_slot = today_slot - dt.timedelta(days=1)

    long_post_times: List[dt.datetime] = []
    if main_key:
        try:
            r = requests.get(f"{ZERNIO_BASE}/posts?limit=45", headers=_headers(main_key), timeout=25)
            if r.status_code == 200:
                pdata = r.json()
                plist = pdata.get("posts", pdata.get("data", pdata if isinstance(pdata, list) else []))
                for p in plist:
                    if _is_long_episode_post(p):
                        ts = _parse_iso_utc(p.get("scheduledFor")) or _parse_iso_utc(p.get("createdAt"))
                        if ts is not None:
                            long_post_times.append(ts)
        except Exception as exc:
            print(f"[{ch['id']}][WARN] تعذر قراءة سجل Zernio للفحص المسبق ({exc}) — سنعتمد التوقيت المحلي.", flush=True)

    def _slot_fulfilled(slot_dt: dt.datetime) -> bool:
        win_start = slot_dt - dt.timedelta(hours=9.0)
        win_end = slot_dt + dt.timedelta(hours=9.0)
        return any(win_start <= ts <= win_end for ts in long_post_times)

    # 1) فحص ما بعد منتصف الليل للقنوات الليلية (مثل 23:45 UTC خلال أول 6 ساعات من اليوم التالي)
    since_yesterday_h = (now_utc - yesterday_slot).total_seconds() / 3600.0
    if 0.0 <= since_yesterday_h <= 6.0 and not _slot_fulfilled(yesterday_slot):
        return {
            "needs_run": True,
            "target_slot_utc": yesterday_slot,
            "is_overdue": True,
            "hours_until_slot": -since_yesterday_h,
            "reason": f"تعويض فوري لموعد الليلة الفائت ({yesterday_slot.strftime('%Y-%m-%d %H:%M UTC')})",
        }

    # 2) فحص موعد اليوم الرسمي
    if _slot_fulfilled(today_slot):
        return {
            "needs_run": False,
            "target_slot_utc": today_slot,
            "is_overdue": False,
            "hours_until_slot": (today_slot - now_utc).total_seconds() / 3600.0,
            "reason": f"مجدولة/منشورة بالفعل لموعد اليوم ({today_slot.strftime('%Y-%m-%d %H:%M UTC')})",
        }

    hours_until_today = (today_slot - now_utc).total_seconds() / 3600.0
    if hours_until_today <= pre_schedule_horizon_hours:
        overdue = hours_until_today <= 0.07
        return {
            "needs_run": True,
            "target_slot_utc": today_slot,
            "is_overdue": overdue,
            "hours_until_slot": hours_until_today,
            "reason": (
                f"تعويض فوري لموعد اليوم المتأخر ({today_slot.strftime('%H:%M UTC')})"
                if overdue
                else f"تحضير مبكر وقفل بالثانية لموعد الذروة ({today_slot.strftime('%H:%M UTC')})"
            ),
        }

    return {
        "needs_run": False,
        "target_slot_utc": today_slot,
        "is_overdue": False,
        "hours_until_slot": hours_until_today,
        "reason": f"موعد التحضير لم يحن بعد (متبقي {hours_until_today:.1f} ساعة على {today_slot.strftime('%H:%M UTC')})",
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


def wait_for_youtube_url(api_key: str, post_id: str, max_wait_sec: int = 120) -> Optional[str]:
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


def _strip_hashtags(txt: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"#\S+", "", txt)).strip(" -—|")


def _apply_exact_schedule(
    payload: Dict[str, Any],
    target_dt_utc: Optional[dt.datetime],
) -> Dict[str, Any]:
    now_utc = dt.datetime.now(dt.timezone.utc)
    if target_dt_utc is None or (target_dt_utc - now_utc).total_seconds() <= 90.0:
        payload["publishNow"] = True
    else:
        payload["scheduledFor"] = target_dt_utc.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return payload


def _post_zernio_resilient(
    api_key: str,
    payload: Dict[str, Any],
    label: str,
    max_attempts: int = 3,
) -> requests.Response:
    """يرسل طلب النشر/الجدولة إلى Zernio مع إعادة محاولة ذكية ضد أخطاء الشبكة وجلسات الرفع العابرة."""
    last_resp: Optional[requests.Response] = None
    for attempt in range(max_attempts):
        try:
            resp = requests.post(
                f"{ZERNIO_BASE}/posts",
                headers=_headers(api_key),
                json=payload,
                timeout=180,
            )
            last_resp = resp
            if resp.status_code < 400:
                # إذا كان نشراً فورياً، نتحقق سريعاً بعد 9 ثوانٍ من عدم حدوث خطأ تهيئة جلسة يوتيوب عابر (400 session init)
                if payload.get("publishNow") and attempt < max_attempts - 1:
                    p_obj = resp.json().get("post", resp.json())
                    pid = p_obj.get("_id") or p_obj.get("id")
                    if pid:
                        time.sleep(9)
                        chk = requests.get(f"{ZERNIO_BASE}/posts/{pid}", headers=_headers(api_key), timeout=25)
                        if chk.status_code == 200:
                            c_plats = chk.json().get("post", chk.json()).get("platforms") or []
                            transient_fail = any(
                                str(cp.get("status") or "").lower() == "failed"
                                and "session initialization failed" in str(cp.get("error") or cp.get("errorMessage") or "").lower()
                                for cp in c_plats
                            )
                            if transient_fail:
                                print(f"[RETRY] {label}: اكتشاف تعثر عابر في جلسة رفع يوتيوب — إعادة الإرسال بعد 12 ثانية...", flush=True)
                                time.sleep(12)
                                continue
                return resp
            if resp.status_code in (400, 408, 429, 500, 502, 503, 504) and attempt < max_attempts - 1:
                wait_s = 10 * (attempt + 1)
                print(f"[RETRY] {label}: استجابة {resp.status_code} — إعادة المحاولة بعد {wait_s}ث...", flush=True)
                time.sleep(wait_s)
                continue
            return resp
        except Exception as exc:
            if attempt == max_attempts - 1:
                raise
            wait_s = 10 * (attempt + 1)
            print(f"[RETRY] {label}: خطأ اتصال عابر ({exc}) — إعادة المحاولة بعد {wait_s}ث...", flush=True)
            time.sleep(wait_s)
    assert last_resp is not None
    return last_resp


def publish_channel_funnel(
    ch: Dict[str, Any],
    episode_meta: Dict[str, Any],
    scene_timings: List[Dict[str, Any]],
    long_mp4: Path,
    thumbnail_jpg: Path,
    short1_mp4: Path,
    short2_mp4: Path,
    short3_mp4: Optional[Path] = None,
    short4_mp4: Optional[Path] = None,
    short1_cover: Optional[Path] = None,
    short2_cover: Optional[Path] = None,
    short3_cover: Optional[Path] = None,
    short4_cover: Optional[Path] = None,
    target_slot_utc: Optional[dt.datetime] = None,
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
    brand_name = ch["brand_name"]

    tags_list = sanitize_tags_list(
        episode_meta.get("seo_tags", []),
        ch.get("base_tags", []),
    )

    print(f"[{ch['id']}] رفع الأغلفة المخصصة والحلقة الكاملة والـ 4 مقاطع شورتس إلى سحابة النشر...", flush=True)
    thumb_url = upload_media_to_zernio(main_key, thumbnail_jpg, mime_type="image/jpeg")
    long_url = upload_media_to_zernio(main_key, long_mp4, mime_type="video/mp4")

    # حساب نقطة ارتكاز النشر بالثانية:
    # - لو التحضير مبكر قبل موعد القناة بـ 4 دقائق على الأقل: نقفل الفيلم في موعد الذروة بالثانية داخل Zernio!
    # - لو موعد القناة فات أو تشغيل تعويضي فوري: ننشر الفيلم الآن فوراً (`publishNow`)، ونبدأ الموجة الأولى من الشورتس بعد 8 دقائق لمنع تصادم رفع يوتيوب!
    now_utc = dt.datetime.now(dt.timezone.utc)
    if target_slot_utc is None:
        t_h = int(ch.get("target_utc_hour", 16))
        t_m = int(ch.get("target_utc_minute", 15))
        cand_slot = dt.datetime(now_utc.year, now_utc.month, now_utc.day, t_h, t_m, 0, tzinfo=dt.timezone.utc)
        target_slot_utc = cand_slot

    is_future_locked = (target_slot_utc - now_utc).total_seconds() > 240.0
    anchor_dt = target_slot_utc if is_future_locked else now_utc
    long_sched_dt: Optional[dt.datetime] = target_slot_utc if is_future_locked else None

    if is_future_locked:
        print(
            f"[{ch['id']}] ⏰ قفل زمني دقيق داخل سحابة Zernio: سينطلق الفيلم الطويل بالثانية عند {target_slot_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}!",
            flush=True,
        )
    else:
        print(
            f"[{ch['id']}] ⚡ نشر تعويضي فوري الآن ({now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}) + توزيع الشورتس الأربع!",
            flush=True,
        )

    # الموجة 1 تبدأ بعد 8 دقائق من الفيلم الطويل لضمان اكتمال جلسة رفع الفيلم الطويل على يوتيوب بنسبة 100% دون أي تصادم!
    shorts_files = [
        ("short_3", "short_3_title", "cta_spoken_3", short3_mp4, short3_cover, 0.14),  # الموجة 1 (+8 دقائق): الشورت الخاطف الأول
        ("short_1", "short_1_title", "cta_spoken_1", short1_mp4, short1_cover, 3.0),   # الموجة 2 (+3 ساعات): الشورت الدرامي العميق الأول
        ("short_4", "short_4_title", "cta_spoken_4", short4_mp4, short4_cover, 6.0),   # الموجة 3 (+6 ساعات): الشورت الخاطف الثاني
        ("short_2", "short_2_title", "cta_spoken_2", short2_mp4, short2_cover, 9.0),   # الموجة 4 (+9 ساعات): الشورت الدرامي العميق الثاني
    ]

    cdn_urls: Dict[str, str] = {"thumb": thumb_url, "long": long_url}
    uploaded_shorts: List[Dict[str, Any]] = []
    for s_id, s_title_key, s_cta_key, s_path, s_cov_path, delay_h in shorts_files:
        if s_path is None or not s_path.exists():
            continue
        m_url = upload_media_to_zernio(main_key, s_path, mime_type="video/mp4")
        tt_m_url = (
            upload_media_to_zernio(tt_key, s_path, mime_type="video/mp4")
            if (tt_acc and tt_key != main_key)
            else m_url
        )
        cov_url = None
        tt_cov_url = None
        if s_cov_path is not None and s_cov_path.exists():
            cov_url = upload_media_to_zernio(main_key, s_cov_path, mime_type="image/jpeg")
            tt_cov_url = (
                upload_media_to_zernio(tt_key, s_cov_path, mime_type="image/jpeg")
                if (tt_acc and tt_key != main_key)
                else cov_url
            )
            cdn_urls[f"{s_id}_cover"] = cov_url
        cdn_urls[s_id] = m_url
        uploaded_shorts.append({
            "id": s_id,
            "title_key": s_title_key,
            "cta_key": s_cta_key,
            "main_url": m_url,
            "tt_url": tt_m_url,
            "cover_url": cov_url,
            "tt_cover_url": tt_cov_url,
            "delay_hours": delay_h,
        })

    ep_title = str(episode_meta.get("youtube_title") or episode_meta.get("episode_title") or brand_name)[:95]
    seo_hook_2lines = str(episode_meta.get("seo_hook_2lines", "")).strip()
    seo_synopsis = str(episode_meta.get("seo_synopsis", "")).strip()
    chapters_txt = build_chapters_block(scene_timings, lang)
    comment_question = str(episode_meta.get("engagement_question", "")).strip()
    raw_hashtags = str(episode_meta.get("hashtags", "")).strip()

    if lang == "ar":
        subscribe_block = (
            f"اشترك في قناة «{brand_name}» ({yt_handle}) وفعل الجرس لتصلك أقوى القصص الواقعية والألغاز الغامضة يومياً!\n"
            f"{comment_question if comment_question else 'اكتب توقعك في التعليقات قبل أن تصل للمشهد الأخير.. هل كشفت الخيط المخفي من البداية؟'}"
        )
        first_comment_long = (
            comment_question
            if comment_question
            else "في أي دقيقة من الحلقة اكتشفت الحقيقة؟ اكتب توقعك في الردود!"
        )
        hashtags_line = raw_hashtags or " ".join(f"#{t.replace(' ', '_')}" for t in tags_list[:8])
    else:
        subscribe_block = (
            f"Subscribe to {brand_name} ({yt_handle}) and turn on notifications for daily full-length true mysteries & thrillers!\n"
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
        "long_video": {},
        "youtube_watch_url": None,
        "cdn_urls": cdn_urls,
        "scheduled_anchor_utc": anchor_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    # 1) نشر أو قفل موعد الحلقة الكاملة على يوتيوب + فيسبوك مع الصورة المصغرة المخصصة ("thumbnail")
    if yt_acc:
        payload_yt_long = _apply_exact_schedule(
            {
                "title": ep_title,
                "content": full_yt_description,
                "tags": tags_list,
                "mediaItems": [{
                    "type": "video",
                    "url": long_url,
                    "thumbnail": thumb_url,
                }],
                "platforms": [{
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
                }],
            },
            long_sched_dt,
        )
        r_yt = _post_zernio_resilient(main_key, payload_yt_long, f"{ch['id']}:YT:long")
        if r_yt.status_code < 400:
            yt_data = r_yt.json()
            results["long_video"]["youtube"] = yt_data
            post_id = yt_data.get("post", yt_data).get("_id") or yt_data.get("post", yt_data).get("id")
            yt_watch = _extract_youtube_url(yt_data)
            # ننتظر رابط الفيديو المباشر فقط إذا كان النشر فورياً الآن
            if not yt_watch and post_id and not is_future_locked:
                yt_watch = wait_for_youtube_url(main_key, post_id, max_wait_sec=110)
            results["youtube_watch_url"] = yt_watch
        else:
            print(f"[{ch['id']}][WARN] تعذر رفع الفيلم الطويل على يوتيوب ({r_yt.status_code}): {r_yt.text[:240]}", flush=True)
            results["long_video"]["youtube_error"] = r_yt.text[:300]

    if fb_acc:
        payload_fb_long = _apply_exact_schedule(
            {
                "title": ep_title,
                "content": full_yt_description,
                "mediaItems": [{
                    "type": "video",
                    "url": long_url,
                    "thumbnail": thumb_url,
                }],
                "platforms": [{
                    "platform": "facebook",
                    "accountId": fb_acc,
                    "platformSpecificData": {
                        "title": ep_title,
                        "firstComment": first_comment_long,
                    },
                }],
            },
            long_sched_dt,
        )
        r_fb = _post_zernio_resilient(main_key, payload_fb_long, f"{ch['id']}:FB:long")
        if r_fb.status_code < 400:
            results["long_video"]["facebook"] = r_fb.json()
        else:
            print(f"[{ch['id']}][WARN] تعذر رفع الفيلم الطويل على فيسبوك ({r_fb.status_code}): {r_fb.text[:240]}", flush=True)
            results["long_video"]["facebook_error"] = r_fb.text[:300]

    yt_link_text = results["youtube_watch_url"] or ch.get("channel_url") or f"https://www.youtube.com/{yt_handle}"
    tt_hashtags = ch.get("tiktok_hashtags") or (
        "#قصص_واقعية #حكايات #غموض #قصص_حقيقية #تشويق"
        if lang == "ar"
        else "#storytime #truestory #mystery #plotwist #thriller"
    )

    # 2) جدولة الـ 4 مقاطع شورتس موزعة بدقة حول موعد الفيلم (+8د، +3س، +6س، +9س) بفصل مستقل لكل منصة
    for item in uploaded_shorts:
        s_id = item["id"]
        delay_h = float(item["delay_hours"])
        short_sched_dt = anchor_dt + dt.timedelta(hours=delay_h)
        raw_st = str(episode_meta.get(item["title_key"]) or ep_title).strip()
        clean_title_no_tags = _strip_hashtags(raw_st) or _strip_hashtags(ep_title)
        debate_line = str(episode_meta.get(item["cta_key"]) or "").strip()

        if lang == "ar":
            debate_prompt_short = "تختار ١ ولا ٢؟ اكتب رقمك في التعليقات!"
            first_comment_cta = (
                f"{debate_prompt_short}\n"
                f"شاهد الحلقة الكاملة بكل تفاصيلها ونهايتها الصادمة الآن على قناتنا ({yt_handle}):\n{yt_link_text}"
            )
            fb_reel_caption = (
                f"{clean_title_no_tags}\n"
                f"{debate_line or debate_prompt_short}\n"
                f"الحلقة الكاملة في أول تعليق!\n"
                f"#ريلز #قصص_واقعية #حكايات #غموض #{brand_name.replace(' ', '_')}"
            )
            tt_caption = (
                f"{clean_title_no_tags}\n"
                f"{debate_prompt_short} — القصة الكاملة على حسابنا «{brand_name}»\n"
                f"{tt_hashtags}"
            )
        else:
            debate_prompt_short = "Would you pick 1 or 2? Comment your number below!"
            first_comment_cta = (
                f"{debate_prompt_short}\n"
                f"Watch the full 16-minute story & shocking ending on our channel ({yt_handle}):\n{yt_link_text}"
            )
            fb_reel_caption = (
                f"{clean_title_no_tags}\n"
                f"{debate_line or debate_prompt_short}\n"
                f"Full episode link in the first comment!\n"
                f"#reels #truestory #mystery #plotwist #{brand_name.replace(' ', '')}"
            )
            tt_caption = (
                f"{clean_title_no_tags}\n"
                f"{debate_prompt_short} — Full story on {brand_name}\n"
                f"{tt_hashtags}"
            )

        yt_s_title = f"{clean_title_no_tags[:82]} #shorts"
        short_res: Dict[str, Any] = {
            "delay_hours": delay_h,
            "scheduled_utc": short_sched_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        s_media_item: Dict[str, Any] = {"type": "video", "url": item["main_url"]}
        if item.get("cover_url"):
            s_media_item["thumbnail"] = item["cover_url"]

        if yt_acc:
            yt_s_payload = _apply_exact_schedule(
                {
                    "title": yt_s_title[:98],
                    "content": fb_reel_caption,
                    "tags": tags_list[:15],
                    "mediaItems": [dict(s_media_item)],
                    "platforms": [{
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
                    }],
                },
                short_sched_dt,
            )
            ry = _post_zernio_resilient(main_key, yt_s_payload, f"{ch['id']}:YT:{s_id}")
            if ry.status_code < 400:
                short_res["youtube"] = ry.json()
            else:
                print(f"[{ch['id']}][WARN] يوتيوب {s_id} ({ry.status_code}): {ry.text[:200]}", flush=True)
                short_res["youtube_error"] = ry.text[:260]

        if fb_acc:
            fb_s_payload = _apply_exact_schedule(
                {
                    "title": clean_title_no_tags[:90],
                    "content": fb_reel_caption,
                    "mediaItems": [dict(s_media_item)],
                    "platforms": [{
                        "platform": "facebook",
                        "accountId": fb_acc,
                        "platformSpecificData": {
                            "contentType": "reel",
                            "title": clean_title_no_tags[:90],
                            "firstComment": first_comment_cta,
                        },
                    }],
                },
                short_sched_dt,
            )
            rf = _post_zernio_resilient(main_key, fb_s_payload, f"{ch['id']}:FB:{s_id}")
            if rf.status_code < 400:
                short_res["facebook"] = rf.json()
            else:
                print(f"[{ch['id']}][WARN] فيسبوك {s_id} ({rf.status_code}): {rf.text[:200]}", flush=True)
                short_res["facebook_error"] = rf.text[:260]

        if tt_acc and tt_key:
            tt_spec_data: Dict[str, Any] = {
                "privacyLevel": "PUBLIC_TO_EVERYONE",
                "allowComment": True,
                "allowDuet": True,
                "allowStitch": True,
                "contentPreviewConfirmed": True,
                "expressConsentGiven": True,
                "videoMadeWithAi": True,
            }
            if item.get("tt_cover_url"):
                tt_spec_data["videoCoverImageUrl"] = item["tt_cover_url"]
            else:
                tt_spec_data["videoCoverTimestampMs"] = 0

            tt_payload = _apply_exact_schedule(
                {
                    "content": tt_caption[:2000],
                    "mediaItems": [{"type": "video", "url": item["tt_url"]}],
                    "platforms": [{
                        "platform": "tiktok",
                        "accountId": tt_acc,
                        "platformSpecificData": tt_spec_data,
                    }],
                },
                short_sched_dt,
            )
            rtt = _post_zernio_resilient(tt_key, tt_payload, f"{ch['id']}:TT:{s_id}")
            if rtt.status_code < 400:
                short_res["tiktok"] = rtt.json()
            else:
                print(f"[{ch['id']}][WARN] تيك توك {s_id} ({rtt.status_code}): {rtt.text[:200]}", flush=True)
                short_res["tiktok_error"] = rtt.text[:260]

        results[s_id] = short_res
        time.sleep(3)

    return results
