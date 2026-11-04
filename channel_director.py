# -*- coding: utf-8 -*-
"""
المدير الذكي الذاتي المحكوم بالدستور V16.0 (Constitution-Locked Channel + Video Growth Director)
يقوم بدور مدير قنوات احترافي متكامل 24/7 بتكلفة $0.00 وبدون أي انحراف عن هوية القناة:
  1) حصاد إحصائيات الأداء الحقيقية ومنحنيات الاحتفاظ بالمشاهد (Retention Curves) من يوتيوب + فيسبوك + تيك توك عبر Zernio + فحص يوتيوب المباشر.
  2) تحسين المحتوى والعناوين والهوك بقاعدة (70% للركائز الأعلى نجاحاً + 30% استكشاف متجدد) داخل دستور الهوية الثابت لكل قناة (صفر خروج عن التخصص!).
  3) بوابة حماية دستورية صارمة (Constitutional Guardrail Gate) تمنع أي كلمة أو فكرة خارج هوية القناة ومبادئها.
  4) التفاعل الذكي التلقائي مع تعليقات الجمهور الحقيقية (إعجاب + رد بشري مشوق بشخصية القناة بدون حرق النهاية).
  5) سجل نمو مستقل لكل فيديو يوتيوب (الفيلم الطويل وكل الشورتس): نمو المشاهدات العام، التوقف المتكرر، تحديثات بيانات المشاهدة والاحتفاظ بعد اكتمال فترة المعالجة، مع تمييز قلة البيانات عن التعثر الحقيقي.
  6) تجارب تغليف محافظة: تغيير عنوان واحد فقط بعد ثبات التعثر ووجود بيانات كافية، وتغيير غلاف الفيلم الطويل فقط عند توفر إشارة CTR/انطباعات موثوقة؛ حد أقصى لتعديلات الفيديو وفاصل 14 يوماً لمنع تقليب البيانات.
  7) تنظيم حلقات الأفلام الطويلة في قائمة تشغيل عامة لكل قناة، إضافة تدريجية بحد أقصى حلقة واحدة لكل دورة؛ دون تغيير القائمة الافتراضية للحساب أو إعادة رفع الفيديو.
  8) الطبيب الذاتي للمنشورات (إعادة محاولة أي شورت مجدول تعثر مؤقتاً) + تحديث لوحة تقرير المدير بالعربية (`state/تقرير_مدير_القنوات.md`).
"""

import datetime as dt
import json
import os
import re
import statistics
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests

ZERNIO_BASE = "https://zernio.com/api/v1"
STATE_DIR = Path(__file__).resolve().parent / "state"
DIRECTOR_STATE_FILE = STATE_DIR / "empire_director.json"
DIRECTOR_REPORT_MD = STATE_DIR / "تقرير_مدير_القنوات.md"

YT_SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _zheaders(api_key: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _parse_iso(ts_raw: Any) -> Optional[dt.datetime]:
    if not ts_raw:
        return None
    s = str(ts_raw).strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        elif re.search(r"[+-]\d{4}$", s):
            s = s[:-2] + ":" + s[-2:]
        d = dt.datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d.astimezone(dt.timezone.utc)
    except Exception:
        return None


def load_director_state(path: Path = DIRECTOR_STATE_FILE) -> Dict[str, Any]:
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.setdefault("channels", {})
                data.setdefault("replied_comment_ids", [])
                data.setdefault("rescued_post_ids", [])
                data.setdefault("retried_post_ids", [])
                return data
        except Exception:
            pass
    return {
        "version": "16.0",
        "updated_at_utc": "",
        "channels": {},
        "replied_comment_ids": [],
        "rescued_post_ids": [],
        "retried_post_ids": [],
    }


def save_director_state(state: Dict[str, Any], path: Path = DIRECTOR_STATE_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state["version"] = "16.0"
    state["updated_at_utc"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # تقليم القوائم لضمان بقاء حجم الملف خفيفاً للأبد (<60 كيلوبايت)
    state["replied_comment_ids"] = list(dict.fromkeys(state.get("replied_comment_ids", [])))[-400:]
    state["rescued_post_ids"] = list(dict.fromkeys(state.get("rescued_post_ids", [])))[-200:]
    state["retried_post_ids"] = list(dict.fromkeys(state.get("retried_post_ids", [])))[-200:]
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


# ==============================================================================
# 1) بوابة الحماية الدستورية الصارمة (Constitutional Identity & Anti-Drift Gate)
# ==============================================================================

def validate_text_against_constitution(
    text_blob: str,
    channel_cfg: Dict[str, Any],
    require_language_match: bool = True,
) -> Tuple[bool, str]:
    """
    يتحقق برمجياً بنسبة 100% من عدم احتواء العنوان أو النص على أي انحراف خارج تخصص القناة ومبادئها.
    """
    if not text_blob or not text_blob.strip():
        return False, "empty_text"

    const = channel_cfg.get("constitution") or {}
    banned = const.get("forbidden_drift_keywords") or []
    low = text_blob.lower()

    for term in banned:
        t_clean = str(term).strip().lower()
        if not t_clean:
            continue
        if re.search(r"(?<!\w)" + re.escape(t_clean) + r"(?!\w)", low):
            return False, f"banned_drift_term:{t_clean}"

    # منع أي إشارات ملابس غير محتشمة أو كلمات محظورة بصرياً/سلوكياً
    immodest_markers = ["cleavage", "bikini", "lingerie", "seductive", "erotic", "nsfw"]
    for m in immodest_markers:
        if m in low:
            return False, f"immodest_term:{m}"

    if require_language_match:
        lang = channel_cfg.get("language", "ar")
        ar_chars = len(re.findall(r"[\u0600-\u06FF]", text_blob))
        en_chars = len(re.findall(r"[A-Za-z]", text_blob))
        if lang == "ar" and ar_chars < max(4, int(0.30 * (ar_chars + en_chars))):
            return False, "arabic_ratio_too_low"
        if lang == "en" and ar_chars > 2:
            return False, "unexpected_arabic_in_english_channel"

    return True, "ok"


def infer_pillar_id(text: str, channel_cfg: Dict[str, Any]) -> str:
    """يربط أي منشور بالركيزة القصصية المعتمدة الأقرب داخل دستور القناة."""
    pillars = (channel_cfg.get("constitution") or {}).get("approved_pillars") or []
    if not pillars:
        return "default_pillar"
    low = (text or "").lower()
    best_id = pillars[0]["id"]
    best_hits = 0
    for p in pillars:
        hits = sum(1 for kw in (p.get("keywords") or []) if str(kw).lower() in low)
        if hits > best_hits:
            best_hits = hits
            best_id = p["id"]
    return best_id


# ==============================================================================
# 2) حصاد الإحصائيات الحقيقية ومنحنيات الاحتفاظ عبر المنصات الثلاث
# ==============================================================================

def _fetch_live_youtube_watch_stats(url: str) -> Dict[str, int]:
    """فحص سريع لصفحة الفيديو العامة على يوتيوب لالتقاط المشاهدات واللايكات الأحدث."""
    out = {"views": 0, "likes": 0}
    if not url or "youtube.com/watch" not in url:
        return out
    try:
        r = requests.get(url, headers=YT_SCRAPE_HEADERS, timeout=6)
        if r.status_code == 200:
            vc = re.search(r'"viewCount"\s*:\s*"(\d+)"', r.text)
            if vc:
                out["views"] = int(vc.group(1))
            lk = re.search(r'"likeCount"\s*:\s*"?(\d+)"?', r.text)
            if lk:
                out["likes"] = int(lk.group(1))
    except Exception:
        pass
    return out


def _extract_hold_ratio(ret_curve: Any, sec_key: int) -> Optional[float]:
    if not isinstance(ret_curve, dict) or not ret_curve:
        return None
    for k in (str(sec_key), sec_key, str(sec_key - 1), str(sec_key + 1)):
        if k in ret_curve:
            try:
                val = float(ret_curve[k])
                return val / 100.0 if val > 1.5 else val
            except Exception:
                pass
    return None


def _classify_post_format(content: str, duration_sec: Any, media_url: str = "") -> str:
    low = f"{content}\n{media_url}".lower()
    dur = 0.0
    try:
        dur = float(duration_sec or 0)
    except Exception:
        dur = 0.0

    if dur >= 300:
        return "long_episode"
    is_short_hint = any(t in low for t in ("#shorts", "#ريلز", "#reels", "_short_", "تختار ١ ولا ٢", "pick 1 or 2", "type 1"))
    if not is_short_hint and dur == 0.0 and ("قصة واقعية كاملة" in low or "لغز جريمة" in low or "true mystery" in low or "detective" in low):
        return "long_episode"
    if 0 < dur <= 62:
        return "fast_short"
    if dur > 62:
        return "deep_short"
    # تصنيف تقريبي عند عدم توفر المدة من النص
    if "بسرعة" in low or "شغّل عقلك في ثانية" in low or "quick—" in low or "solve it in five" in low:
        return "fast_short"
    return "deep_short"


def _detect_title_style(title_line: str) -> str:
    t = title_line.strip()
    if "؟" in t or "?" in t:
        return "question_curiosity"
    if re.search(r"\d|[٠-٩]", t):
        return "number_timestamp_hook"
    if "!" in t:
        return "shock_exclamation"
    return "mystery_statement"


def harvest_channel_telemetry(
    ch: Dict[str, Any],
    memory: Dict[str, Any],
    director_state: Dict[str, Any],
) -> Dict[str, Any]:
    """يجمع إحصائيات يوتيوب وفيسبوك وتيك توك الحقيقية ويحدث سجل أداء الركائز والهوك."""
    cid = ch["id"]
    prefix = ch["env_prefix"]
    main_key = os.environ.get(f"{prefix}_ZERNIO_KEY", "").strip()
    tt_key = os.environ.get(f"{prefix}_TIKTOK_ZERNIO_KEY", "").strip() or main_key

    accounts = ch.get("accounts") or {}
    yt_acc = accounts.get("youtube", "")
    fb_acc = accounts.get("facebook", "")
    tt_acc = os.environ.get(f"{prefix}_TIKTOK_ACCOUNT_ID", "").strip() or accounts.get("tiktok", "")

    ch_state = director_state.setdefault("channels", {}).setdefault(cid, {})
    overview = ch_state.setdefault("account_overview", {
        "yt_views_30d": 0,
        "yt_watch_min_30d": 0,
        "yt_subs_30d": 0,
        "fb_views_30d": 0,
        "tt_views_30d": 0,
    })

    # 1) جلب نظرة الـ 30 يوماً على مستوى الحسابات
    if main_key and yt_acc:
        try:
            ry = requests.get(
                f"{ZERNIO_BASE}/analytics/youtube/channel-insights?accountId={yt_acc}",
                headers=_zheaders(main_key),
                timeout=14,
            )
            if ry.status_code == 200:
                m = (ry.json().get("metrics") or {})
                overview["yt_views_30d"] = int((m.get("views") or {}).get("total") or 0)
                overview["yt_watch_min_30d"] = int((m.get("estimatedMinutesWatched") or {}).get("total") or 0)
                overview["yt_subs_30d"] = int((m.get("subscribersGained") or {}).get("total") or 0)
        except Exception:
            pass

    if main_key and fb_acc:
        try:
            rf = requests.get(
                f"{ZERNIO_BASE}/analytics/facebook/page-insights?accountId={fb_acc}",
                headers=_zheaders(main_key),
                timeout=14,
            )
            if rf.status_code == 200:
                m = (rf.json().get("metrics") or {})
                overview["fb_views_30d"] = int((m.get("page_media_view") or {}).get("total") or 0)
        except Exception:
            pass

    if tt_key and tt_acc:
        try:
            rt = requests.get(
                f"{ZERNIO_BASE}/analytics/tiktok/account-insights?accountId={tt_acc}",
                headers=_zheaders(tt_key),
                timeout=14,
            )
            if rt.status_code == 200:
                m = (rt.json().get("metrics") or {})
                overview["tt_views_30d"] = int(
                    (m.get("video_views") or m.get("views") or {}).get("total") or 0
                )
        except Exception:
            pass

    # 2) جلب إحصائيات المنشورات التفصيلية لكل منصة على حدة
    raw_posts: List[Tuple[str, Dict[str, Any]]] = []
    platform_targets = [
        ("youtube", main_key, yt_acc),
        ("facebook", main_key, fb_acc),
        ("tiktok", tt_key, tt_acc),
    ]
    for plat_name, key_val, acc_id in platform_targets:
        if not key_val or not acc_id:
            continue
        try:
            rp = requests.get(
                f"{ZERNIO_BASE}/analytics?accountId={acc_id}&limit=50",
                headers=_zheaders(key_val),
                timeout=16,
            )
            if rp.status_code == 200:
                for p_item in (rp.json().get("posts") or []):
                    raw_posts.append((plat_name, p_item))
        except Exception:
            pass

    # خريطة الركائز المحفوظة من الحلقات السابقة في الذاكرة
    mem_pillar_map: Dict[str, str] = (memory.get(cid) or {}).get("title_pillar_map") or {}
    pillars_cfg = (ch.get("constitution") or {}).get("approved_pillars") or []
    pillar_acc: Dict[str, Dict[str, Any]] = {
        p["id"]: {"label": p["label"], "posts": 0, "total_vps": 0.0, "avg_vps": 0.0, "best_title": "", "best_vps": 0.0}
        for p in pillars_cfg
    }

    scored_posts: List[Dict[str, Any]] = []
    holds_3s: List[float] = []
    holds_15s: List[float] = []
    style_scores: Dict[str, List[float]] = {}
    format_scores: Dict[str, List[float]] = {"long_episode": [], "deep_short": [], "fast_short": []}
    # One fresh YouTube sample keeps the aggregate winner list current; V16 separately rotates through the full video catalog.
    yt_scrape_budget = 1
    now_utc = dt.datetime.now(dt.timezone.utc)

    for plat_name, p_obj in raw_posts:
        if str(p_obj.get("status") or "").lower() != "published":
            continue
        content = str(p_obj.get("content") or "").strip()
        first_line = re.sub(r"\s+", " ", content.split("\n")[0]).strip()[:95]
        if not first_line:
            continue

        an = p_obj.get("analytics") or {}
        views = int(an.get("views") or an.get("impressions") or an.get("reach") or 0)
        likes = int(an.get("likes") or 0)
        raw_comments = int(an.get("comments") or 0)
        # طرح التعليق الأول التلقائي الذي يضعه البوت على يوتيوب وفيسبوك لقياس تعليقات الجمهور الحقيقية فقط
        real_comments = max(0, raw_comments - (1 if plat_name in ("youtube", "facebook") else 0))
        shares = int(an.get("shares") or an.get("reposts") or 0)
        saves = int(an.get("saves") or 0)
        replays = int(an.get("replays") or 0)
        dur_sec = an.get("videoDurationSeconds")
        post_url = str(p_obj.get("platformPostUrl") or "")

        if plat_name == "youtube" and views == 0 and yt_scrape_budget > 0 and "youtube.com/watch" in post_url:
            yt_scrape_budget -= 1
            live_yt = _fetch_live_youtube_watch_stats(post_url)
            views = max(views, live_yt["views"])
            likes = max(likes, live_yt["likes"])

        ret_curve = an.get("retentionCurve") or {}
        h3 = _extract_hold_ratio(ret_curve, 3)
        h15 = _extract_hold_ratio(ret_curve, 15)
        if h3 is not None and views >= 10:
            holds_3s.append(h3)
        if h15 is not None and views >= 10:
            holds_15s.append(h15)

        hold_bonus = (40.0 * h3) if (h3 is not None and views >= 10) else 0.0
        vps = (
            float(views)
            + (8.0 * replays)
            + (12.0 * likes)
            + (25.0 * real_comments)
            + (30.0 * shares)
            + (20.0 * saves)
            + hold_bonus
        )

        media_items = p_obj.get("mediaItems") or []
        m_url = str(media_items[0].get("url") or "") if media_items else ""
        fmt = _classify_post_format(content, dur_sec, m_url)
        format_scores.setdefault(fmt, []).append(vps)

        t_style = _detect_title_style(first_line)
        style_scores.setdefault(t_style, []).append(vps)

        # مطابقة الركيزة القصصية وتنظيف العنوان من لواحق الدعوة للتعليق
        clean_head = re.sub(r"#\S+", "", first_line)
        for cut_marker in (
            "تختار ١ ولا ٢",
            "شاهد القصة الكاملة",
            "الحلقة الكاملة في أول تعليق",
            "Would you pick 1 or 2",
            "Watch the full",
            "Full episode link",
        ):
            if cut_marker.lower() in clean_head.lower():
                idx_m = clean_head.lower().find(cut_marker.lower())
                clean_head = clean_head[:idx_m]
        clean_head = clean_head.strip(" -—|،.")[:78]
        matched_pillar = ""
        for saved_title, saved_pid in mem_pillar_map.items():
            if saved_title and (saved_title[:24] in clean_head or clean_head[:24] in saved_title):
                matched_pillar = saved_pid
                break
        if not matched_pillar or matched_pillar not in pillar_acc:
            matched_pillar = infer_pillar_id(content, ch)

        if matched_pillar in pillar_acc:
            pa = pillar_acc[matched_pillar]
            pa["posts"] += 1
            pa["total_vps"] += vps
            pa["avg_vps"] = round(pa["total_vps"] / max(1, pa["posts"]), 2)
            if vps >= pa["best_vps"] and clean_head:
                pa["best_vps"] = round(vps, 2)
                pa["best_title"] = clean_head

        pub_dt = _parse_iso(p_obj.get("publishedAt") or p_obj.get("scheduledFor"))
        age_h = ((now_utc - pub_dt).total_seconds() / 3600.0) if pub_dt else 0.0

        scored_posts.append({
            "late_post_id": str(p_obj.get("latePostId") or p_obj.get("_id") or ""),
            "platform": plat_name,
            "format": fmt,
            "title": clean_head or first_line,
            "views": views,
            "replays": replays,
            "likes": likes,
            "real_comments": real_comments,
            "shares": shares,
            "hold_3s": round(h3, 3) if h3 is not None else None,
            "vps": round(vps, 2),
            "pillar_id": matched_pillar,
            "age_hours": round(age_h, 1),
            "url": post_url,
        })

    scored_posts.sort(key=lambda x: x["vps"], reverse=True)
    # إزالة تكرار نفس العنوان عبر المنصات في قائمة المتصدرين والضعفاء
    seen_win_titles = set()
    top_winners: List[Dict[str, Any]] = []
    for p in scored_posts:
        if p["vps"] <= 0:
            continue
        t_norm = p["title"][:32].lower()
        if t_norm in seen_win_titles:
            continue
        seen_win_titles.add(t_norm)
        top_winners.append(p)
        if len(top_winners) >= 5:
            break

    plat_totals = {}
    for p in scored_posts:
        plat_totals[p["platform"]] = plat_totals.get(p["platform"], 0) + int(p["views"])

    mature_posts = [
        p for p in scored_posts
        if p["age_hours"] >= 20.0
        and plat_totals.get(p["platform"], 0) >= 25
        and p["title"][:32].lower() not in seen_win_titles
    ]
    seen_lag_titles = set()
    bottom_laggards: List[Dict[str, Any]] = []
    for p in reversed(mature_posts):
        t_norm = p["title"][:32].lower()
        if t_norm in seen_lag_titles:
            continue
        seen_lag_titles.add(t_norm)
        bottom_laggards.append(p)
        if len(bottom_laggards) >= 3:
            break

    winning_style = "mystery_statement"
    best_style_avg = -1.0
    for st_name, vals in style_scores.items():
        if vals:
            avg_v = sum(vals) / len(vals)
            if avg_v > best_style_avg:
                best_style_avg = avg_v
                winning_style = st_name

    ret_diag = {
        "evaluated_posts": len(scored_posts),
        "total_tracked_views": sum(p["views"] for p in scored_posts),
        "avg_hold_3s": round(sum(holds_3s) / len(holds_3s), 3) if holds_3s else None,
        "avg_hold_15s": round(sum(holds_15s) / len(holds_15s), 3) if holds_15s else None,
        "long_avg_vps": round(sum(format_scores["long_episode"]) / len(format_scores["long_episode"]), 2) if format_scores["long_episode"] else 0.0,
        "deep_short_avg_vps": round(sum(format_scores["deep_short"]) / len(format_scores["deep_short"]), 2) if format_scores["deep_short"] else 0.0,
        "fast_short_avg_vps": round(sum(format_scores["fast_short"]) / len(format_scores["fast_short"]), 2) if format_scores["fast_short"] else 0.0,
        "winning_title_style": winning_style,
    }

    ch_state["last_sync_utc"] = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    ch_state["pillar_stats"] = pillar_acc
    ch_state["top_winners"] = top_winners
    ch_state["bottom_laggards"] = bottom_laggards
    ch_state["retention_diagnostics"] = ret_diag
    ch_state["recent_youtube_longs"] = [
        p for p in scored_posts if p["platform"] == "youtube" and p["format"] == "long_episode"
    ][:15]
    return ch_state


# ==============================================================================
# 3) محرك اختيار الاستراتيجية (70% رابح / 30% استكشاف) داخل الدستور الثابت
# ==============================================================================

def select_next_episode_strategy(
    ch: Dict[str, Any],
    memory: Dict[str, Any],
    director_state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    يختار الركيزة القصصية المعتمدة القادمة ويبني توجيه المدير الذكي للكاتب:
    - يستحيل الخروج عن الـ 6 ركائز المعتمدة داخل دستور القناة!
    - يمنع تكرار نفس الركيزة في يومين متتاليين.
    - يخصص ~70% من الحلقات لأعلى الركائز نجاحاً بالمشاهدات والاحتفاظ، و ~30% لاستكشاف أقل الركائز تجربة.
    """
    cid = ch["id"]
    const = ch.get("constitution") or {}
    pillars = const.get("approved_pillars") or []
    if not pillars:
        raise RuntimeError(f"القناة {cid} تفتقر إلى approved_pillars في الدستور!")

    ch_state = (director_state.get("channels") or {}).get(cid) or {}
    p_stats = ch_state.get("pillar_stats") or {}
    used_topics = (memory.get(cid) or {}).get("used_topics") or []
    ep_index = len(used_topics)
    last_pillar_id = str((memory.get(cid) or {}).get("last_pillar_id") or ch_state.get("last_pillar_id") or "")

    candidates = [p for p in pillars if p["id"] != last_pillar_id] or list(pillars)

    # حساب المتوسط المرجعي Bayesian Prior لمنع التحيز المبكر من منشور واحد
    all_totals = sum(float((p_stats.get(p["id"]) or {}).get("total_vps") or 0.0) for p in pillars)
    all_counts = sum(int((p_stats.get(p["id"]) or {}).get("posts") or 0) for p in pillars)
    prior_vps = (all_totals / all_counts) if all_counts > 0 else 25.0

    enriched: List[Tuple[float, int, Dict[str, Any]]] = []
    for p in candidates:
        st = p_stats.get(p["id"]) or {}
        cnt = int(st.get("posts") or 0)
        tot = float(st.get("total_vps") or 0.0)
        smoothed = (tot + 2.0 * prior_vps) / (cnt + 2.0)
        enriched.append((smoothed, cnt, p))

    # إذا لم تتوفر بيانات كافية بعد (<3 منشورات مسجلة)، ننوّع بالتناوب المتوازن
    if all_counts < 3:
        chosen_pillar = candidates[ep_index % len(candidates)]
        mode = "balanced_bootstrap"
    elif ep_index % 3 == 2:
        # 33% استكشاف: الأقل عدداً في التجربة (ثم الأعلى تقييماً عند التساوي)
        enriched.sort(key=lambda item: (item[1], -item[0]))
        chosen_pillar = enriched[0][2]
        mode = "explore_30pct"
    else:
        # 67%–70% استثمار للرابحين: التناوب الذكي بين أفضل ركيزتين في الأداء
        enriched.sort(key=lambda item: item[0], reverse=True)
        top_pool = enriched[: min(2, len(enriched))]
        chosen_pillar = top_pool[ep_index % len(top_pool)][2]
        mode = "exploit_winners_70pct"

    return {
        "mode": mode,
        "pillar": chosen_pillar,
        "top_winners": (ch_state.get("top_winners") or [])[:3],
        "bottom_laggards": (ch_state.get("bottom_laggards") or [])[:2],
        "retention_diagnostics": ch_state.get("retention_diagnostics") or {},
        "growth_lessons": (ch_state.get("growth_lessons") or [])[:3],
    }


def build_director_prompt_injection(
    ch: Dict[str, Any],
    strategy: Dict[str, Any],
) -> str:
    """يصوغ توجيه المدير التنفيذي المبني على أرقام القناة الحقيقية ليُحقن في عقل الكتابة."""
    lang = ch.get("language", "ar")
    const = ch.get("constitution") or {}
    winners = strategy.get("top_winners") or []
    laggards = strategy.get("bottom_laggards") or []
    growth_lessons = strategy.get("growth_lessons") or []
    ret = strategy.get("retention_diagnostics") or {}
    hold_3s = ret.get("avg_hold_3s")
    win_style = ret.get("winning_title_style", "mystery_statement")

    if lang == "ar":
        lines = [
            "=== توجيه المدير الذكي الذاتي للقناة (مبني على إحصائيات المشاهدين الحقيقية + دستور الهوية الثابت) ===",
            f"• الدستور الثابت غير القابل للمساس: {const.get('core_identity', '')}",
            "• تحذير صارم: ممنوع منعاً باتاً الخروج عن تخصص القناة أو إدخال خرافات/أشباح/سياسة/رياضة/أخبار أو تغيير اللهجة والأسلوب تحت أي ظرف!",
        ]
        if winners:
            win_str = " | ".join(
                f"«{w['title']}» ({w['views']} مشاهدة، {w['replays']} إعادة)" for w in winners
            )
            lines.append(
                f"• الأعلى نجاحاً لدى جمهور هذه القناة فعلياً: {win_str} — استلهمي نفس قوة الفضول والتحديد البصري الملموس في العنوان والهوك (بقصة جديدة تماماً 100% دون أي تكرار!)."
            )
        if laggards:
            lag_str = " | ".join(f"«{l['title']}»" for l in laggards)
            lines.append(f"• عناوين كانت أقل جذباً للنقرات (تجنبي العمومية المشابهة لها): {lag_str}.")
        if hold_3s is not None and hold_3s < 0.45:
            lines.append(
                f"• تشخيص منحنى الاحتفاظ الحقيقي: نسبة البقاء عند الثانية 3 هي {hold_3s*100:.0f}% — لذلك يجب أن تبدأ أول 4 كلمات من كل شورت ومن المقدمة التشويقية بفعل بصري صادم وملموس فوراً (مثل: فتحت الدولاب لقيت.. / الرسالة وصلت من جوه شقتي..) بدون أي تمهيد إنشائي!"
            )
        for lesson in growth_lessons[:3]:
            lines.append(f"• تعلّم من تعثر فيديوهات القناة (طبّقه على الفيديو القادم فقط، داخل الدستور): {lesson}")
        style_ar_map = {
            "question_curiosity": "السؤال الصادم المباشر أو التناقض المحير",
            "number_timestamp_hook": "تحديد رقم أو توقيت دقيق في العنوان (مثل: الساعة 3 الفجر / تفصيلة واحدة)",
            "shock_exclamation": "مفاجأة الاكتشاف المفاجئ بحدث ملموس",
            "mystery_statement": "اللغز الواقعي المحدد بمكان وأداة حقيقية",
        }
        lines.append(f"• نمط العناوين الأعلى تفاعلاً حالياً على القناة: {style_ar_map.get(win_style, 'اللغز الواقعي المحدد')}.")
        return "\n".join(lines)

    lines = [
        "=== AUTONOMOUS CHANNEL DIRECTOR BRIEF (REAL AUDIENCE TELEMETRY + IMMUTABLE CONSTITUTION) ===",
        f"• IMMUTABLE CHANNEL IDENTITY: {const.get('core_identity', '')}",
        "• ZERO-DRIFT RULE: Never drift outside this exact niche—strictly zero supernatural ghosts, sci-fi, politics, sports, or off-brand topics!",
    ]
    if winners:
        win_str = " | ".join(f"\"{w['title']}\" ({w['views']} views, {w['replays']} replays)" for w in winners)
        lines.append(
            f"• PROVEN TOP PERFORMERS ON THIS CHANNEL: {win_str} — match their sharp concrete curiosity gap and immediate stakes with a 100% brand-new plot."
        )
    if laggards:
        lag_str = " | ".join(f"\"{l['title']}\"" for l in laggards)
        lines.append(f"• LOWER-CTR PACKAGING TO AVOID (too vague/generic): {lag_str}.")
    if hold_3s is not None and hold_3s < 0.45:
        lines.append(
            f"• LIVE RETENTION CURVE ALERT: 3-second hold rate is {hold_3s*100:.0f}% — start the very first 4 words of the teaser and every Short with a concrete physical discovery or visual anomaly, zero slow throat-clearing!"
        )
    for lesson in growth_lessons[:3]:
        lines.append(f"• VIDEO-LIFECYCLE LEARNING (future uploads only, within the constitution): {lesson}")
    return "\n".join(lines)


# ==============================================================================
# 4) التفاعل الذكي مع تعليقات الجمهور الحقيقية (Autonomous Community Manager)
# ==============================================================================

def _is_genuine_viewer_comment(
    comment_obj: Dict[str, Any],
    brand_name: str,
    handle: str,
    account_id: str,
    account_username: str = "",
) -> bool:
    frm = comment_obj.get("from") or {}
    if bool(comment_obj.get("isOwner")) or bool(frm.get("isOwner")):
        return False
    author_name = str(frm.get("name") or comment_obj.get("authorName") or "").strip().lstrip("@").lower()
    own_names = {
        brand_name.strip().lstrip("@").lower(),
        handle.strip().lstrip("@").lower(),
        account_username.strip().lstrip("@").lower(),
    } - {""}
    if author_name and author_name in own_names:
        return False

    # إذا سبق للقناة الرد داخل نفس سلسلة الردود نتخطاه فوراً لمنع أي رد مزدوج
    for rep in (comment_obj.get("replies") or []):
        rep_frm = rep.get("from") or {}
        rep_name = str(rep_frm.get("name") or "").strip().lstrip("@").lower()
        if bool(rep_frm.get("isOwner")) or (rep_name and rep_name in own_names):
            return False

    msg = str(comment_obj.get("message") or comment_obj.get("content") or comment_obj.get("text") or "").strip()
    if len(msg) < 1 or len(msg) > 350:
        return False
    low = msg.lower()
    # استبعاد تعليقات البوت نفسه والروابط الترويجية المزعجة
    own_markers = [
        handle.lower(), "شاهد الحلقة الكاملة", "watch the full", "solve the full case",
        "http://", "https://", "www.", ".com", "whatsapp", "telegram", "crypto", "forex",
    ]
    if any(m in low for m in own_markers):
        return False
    return True


def _build_storyteller_reply(
    viewer_msg: str,
    post_excerpt: str,
    ch: Dict[str, Any],
    llm_json_fn: Optional[Callable[..., Dict[str, Any]]] = None,
    groq_key: str = "",
) -> str:
    lang = ch.get("language", "ar")
    clean_msg = viewer_msg.strip()

    # ردود ذكية سريعة وطبيعية إذا كتب المشاهد رقم التصويت الجدلي (1 أو 2) مباشرة
    only_choice_1 = re.fullmatch(r"[\s#*(]*(?:1|١|واحد|الاول|الأول|one)[\s!.)🎉🔥👍]*", clean_msg, flags=re.IGNORECASE)
    only_choice_2 = re.fullmatch(r"[\s#*(]*(?:2|٢|اتنين|اثنين|التاني|الثاني|two)[\s!.)🎉🔥👍]*", clean_msg, flags=re.IGNORECASE)

    if only_choice_1:
        if lang == "ar":
            return "اختيار جريء جداً 👀 بس يا ترى بعد اللي ظهر في آخر دقيقة هتفضل على اختيار رقم ١ ولا هتغير رأيك؟"
        return "Bold call picking #1 👀 After that final twist at the end, would you still stick with 1?"
    if only_choice_2:
        if lang == "ar":
            return "تفكير حذر وذكي جداً 👌 بس التفصيلة المستخبية في النهاية خلت رقم ٢ نفسه فيه مفاجأة متخطرش على البال!"
        return "Smart instinct going with #2 👌 Though that last hidden detail makes option 2 way trickier than it looks!"

    if llm_json_fn and groq_key:
        try:
            if lang == "ar":
                sys_p = (
                    f"أنت مقدم قناة «{ch['brand_name']}» للقصص والألغاز الواقعية بالعامية المصرية المهذبة الدافئة. "
                    "اكتب رداً قصيراً جداً (جملة واحدة من 8 إلى 16 كلمة بالعامية المصرية) يشكر المشاهد أو يناقش توقعه بذكاء وتشويق بدون حرق نهاية القصة نهائياً."
                )
                usr_p = f"منشور الحلقة: {post_excerpt[:140]}\nتعليق المشاهد: {clean_msg}\nأخرج JSON فقط: {{\"reply\": \"الرد القصير\"}}"
            else:
                sys_p = (
                    f"You are the host of '{ch['brand_name']}'. Write one warm, intriguing 8-16 word reply to this viewer's comment "
                    "without spoiling the ending. Return JSON only: {\"reply\": \"your short reply\"}"
                )
                usr_p = f"Post: {post_excerpt[:140]}\nViewer comment: {clean_msg}\nReturn JSON: {{\"reply\": \"...\"}}"
            res = llm_json_fn(groq_key, sys_p, usr_p, 350)
            rep = str(res.get("reply") or "").strip()
            ok, _ = validate_text_against_constitution(rep, ch, require_language_match=True)
            if ok and 5 <= len(rep) <= 180:
                return rep
        except Exception:
            pass

    if lang == "ar":
        return "ملاحظة ذكية جداً منك! 👏 ركز في التفصيلة اللي ظهرت قبل النهاية وقولنا توقعتها من الأول ولا لأ 👀"
    return "Sharp eye! 👏 Let us know if that final clue near the end matched your theory 👀"


def manage_audience_comments(
    ch: Dict[str, Any],
    director_state: Dict[str, Any],
    llm_json_fn: Optional[Callable[..., Dict[str, Any]]] = None,
    groq_key: str = "",
    max_replies_per_channel: int = 4,
) -> int:
    """يتفقد تعليقات الجمهور الحقيقية على يوتيوب وفيسبوك ويعطي إعجاباً + رداً مشوقاً بشخصية القناة."""
    prefix = ch["env_prefix"]
    main_key = os.environ.get(f"{prefix}_ZERNIO_KEY", "").strip()
    if not main_key:
        return 0

    replied_set = set(director_state.setdefault("replied_comment_ids", []))
    accounts = ch.get("accounts") or {}
    replies_sent = 0

    for plat_name in ("youtube", "facebook"):
        acc_id = accounts.get(plat_name, "")
        if not acc_id or replies_sent >= max_replies_per_channel:
            continue
        try:
            r_list = requests.get(
                f"{ZERNIO_BASE}/inbox/comments?accountId={acc_id}&minComments=1&limit=5",
                headers=_zheaders(main_key),
                timeout=12,
            )
            if r_list.status_code != 200:
                continue
            posts_data = r_list.json().get("data") or []
            for p_entry in posts_data:
                if replies_sent >= max_replies_per_channel:
                    break
                post_id = str(p_entry.get("id") or "").strip()
                acc_uname = str(p_entry.get("accountUsername") or "").strip()
                if not post_id:
                    continue

                r_sub = requests.get(
                    f"{ZERNIO_BASE}/inbox/comments/{post_id}?accountId={acc_id}&limit=10",
                    headers=_zheaders(main_key),
                    timeout=12,
                )
                if r_sub.status_code != 200:
                    continue
                comments = r_sub.json().get("comments") or r_sub.json().get("data") or []
                replied_authors_on_post = set()

                for cm in comments:
                    if replies_sent >= max_replies_per_channel:
                        break
                    cm_id = str(cm.get("id") or "").strip()
                    if not cm_id or cm_id in replied_set:
                        continue
                    if not _is_genuine_viewer_comment(cm, ch["brand_name"], ch["handle"], acc_id, acc_uname):
                        replied_set.add(cm_id)
                        continue

                    author_key = str((cm.get("from") or {}).get("id") or (cm.get("from") or {}).get("name") or cm_id)
                    if author_key in replied_authors_on_post:
                        continue

                    msg_txt = str(cm.get("message") or cm.get("content") or cm.get("text") or "").strip()
                    reply_txt = _build_storyteller_reply(
                        viewer_msg=msg_txt,
                        post_excerpt=str(p_entry.get("content") or ""),
                        ch=ch,
                        llm_json_fn=llm_json_fn,
                        groq_key=groq_key,
                    )

                    # 1) تسجيل إعجاب بتعليق المشاهد
                    try:
                        requests.post(
                            f"{ZERNIO_BASE}/inbox/comments/{post_id}/{cm_id}/like",
                            headers=_zheaders(main_key),
                            json={"accountId": acc_id},
                            timeout=12,
                        )
                    except Exception:
                        pass

                    # 2) إرسال الرد على تعليق المشاهد
                    try:
                        rr = requests.post(
                            f"{ZERNIO_BASE}/inbox/comments/{post_id}",
                            headers=_zheaders(main_key),
                            json={
                                "accountId": acc_id,
                                "commentId": cm_id,
                                "message": reply_txt,
                            },
                            timeout=15,
                        )
                        if rr.status_code < 400:
                            replied_set.add(cm_id)
                            replied_authors_on_post.add(author_key)
                            replies_sent += 1
                            print(f"[{ch['id']}][COMMUNITY] تم الرد على تعليق مشاهد على {plat_name}: «{msg_txt[:35]}» -> «{reply_txt[:45]}»", flush=True)
                    except Exception:
                        pass
        except Exception:
            pass

    director_state["replied_comment_ids"] = list(replied_set)[-400:]
    return replies_sent


# ==============================================================================
# 5) إنقاذ عناوين يوتيوب منخفضة النقر بعد 36 ساعة + الطبيب الذاتي للمنشورات
# ==============================================================================

def rescue_underperforming_youtube_titles(
    ch: Dict[str, Any],
    director_state: Dict[str, Any],
    llm_json_fn: Optional[Callable[..., Dict[str, Any]]] = None,
    groq_key: str = "",
) -> int:
    """
    يفحص الحلقات الكاملة على يوتيوب التي مر عليها 36–168 ساعة:
    إذا توفر للقناة خط أساس واضح (>=4 حلقات ناضجة بمتوسط >=15 مشاهدة) وحققت حلقة أقل من 42% من الوسيط،
    يعيد صياغة العنوان مرة واحدة فقط لرفع نسبة النقر (CTR) مع التزام 100% بدستور القناة وبأحداث نفس القصة.
    """
    if not llm_json_fn or not groq_key:
        return 0
    cid = ch["id"]
    prefix = ch["env_prefix"]
    main_key = os.environ.get(f"{prefix}_ZERNIO_KEY", "").strip()
    yt_acc = (ch.get("accounts") or {}).get("youtube", "")
    if not main_key or not yt_acc:
        return 0

    ch_state = (director_state.get("channels") or {}).get(cid) or {}
    yt_longs = ch_state.get("recent_youtube_longs") or []
    mature = [p for p in yt_longs if 36.0 <= float(p.get("age_hours") or 0) <= 168.0]
    if len(mature) < 4:
        return 0

    med_views = statistics.median([int(p.get("views") or 0) for p in mature])
    if med_views < 15:
        return 0

    rescued_ids = set(director_state.setdefault("rescued_post_ids", []))
    winners = [w["title"] for w in (ch_state.get("top_winners") or [])[:3]]
    const = ch.get("constitution") or {}
    suffix = (const.get("title_suffixes") or [""])[0]
    lang = ch.get("language", "ar")
    rescued_count = 0

    for cand in mature:
        pid = str(cand.get("late_post_id") or "").strip()
        if not pid or pid in rescued_ids:
            continue
        if int(cand.get("views") or 0) >= (0.42 * med_views):
            continue

        old_title = str(cand.get("title") or "").strip()
        if not old_title:
            continue

        try:
            if lang == "ar":
                sys_p = (
                    f"أنت خبير تحسين نسبة النقر (CTR) لقناة يوتيوب «{ch['brand_name']}». "
                    f"الدستور الثابت: {const.get('core_identity', '')}. "
                    "أعد صياغة عنوان هذه الحلقة فقط ليصبح أكثر إثارة للفضول بنسبة 300% مع الحفاظ التام على نفس موضوع القصة الأصلي بدون كذب أو حرق للنهاية."
                )
                usr_p = (
                    f"العنوان الحالي الضعيف: {old_title}\n"
                    f"أنجح عناوين القناة للاقتداء بإيقاعها: {winners}\n"
                    f"اجعل العنوان الجديد أقل من 85 حرفاً وينتهي بـ «{suffix}».\n"
                    "أخرج JSON فقط: {\"new_title\": \"العنوان المحسن\"}"
                )
            else:
                sys_p = (
                    f"You are an elite YouTube CTR Strategist for '{ch['brand_name']}'. "
                    f"Constitution: {const.get('core_identity', '')}. "
                    "Rewrite ONLY this video's title to maximize curiosity gap while staying 100% faithful to the same story premise with zero spoilers."
                )
                usr_p = (
                    f"Current underperforming title: {old_title}\n"
                    f"Channel top-performing titles for tone reference: {winners}\n"
                    f"Keep under 85 chars and end with '{suffix}'.\n"
                    "Return JSON only: {\"new_title\": \"Upgraded Title\"}"
                )
            res = llm_json_fn(groq_key, sys_p, usr_p, 400)
            new_title = str(res.get("new_title") or "").strip()[:95]
            ok, _ = validate_text_against_constitution(new_title, ch, require_language_match=True)
            if not ok or len(new_title) < 18 or new_title == old_title:
                continue

            ru = requests.post(
                f"{ZERNIO_BASE}/posts/{pid}/update-metadata",
                headers=_zheaders(main_key),
                json={
                    "platform": "youtube",
                    "accountId": yt_acc,
                    "title": new_title,
                },
                timeout=20,
            )
            if ru.status_code < 400:
                rescued_ids.add(pid)
                rescued_count += 1
                print(f"[{cid}][CTR-RESCUE] ترقية عنوان يوتيوب: «{old_title}» -> «{new_title}»", flush=True)
                break  # ترقية عنوان واحد كحد أقصى في المسحة الواحدة لتجنب حدود يوتيوب
        except Exception:
            pass

    director_state["rescued_post_ids"] = list(rescued_ids)[-200:]
    return rescued_count


def heal_failed_scheduled_posts(
    ch: Dict[str, Any],
    director_state: Dict[str, Any],
) -> int:
    """يكتشف أي منشور/شورت حديث تعثر رفعه مؤقتاً ويعيد محاولته تلقائياً مرة واحدة."""
    prefix = ch["env_prefix"]
    main_key = os.environ.get(f"{prefix}_ZERNIO_KEY", "").strip()
    tt_key = os.environ.get(f"{prefix}_TIKTOK_ZERNIO_KEY", "").strip()
    retried = set(director_state.setdefault("retried_post_ids", []))
    now_utc = dt.datetime.now(dt.timezone.utc)
    healed = 0

    for key_val in dict.fromkeys([k for k in (main_key, tt_key) if k]):
        try:
            r = requests.get(f"{ZERNIO_BASE}/posts?limit=25", headers=_zheaders(key_val), timeout=15)
            if r.status_code != 200:
                continue
            for p in (r.json().get("posts") or []):
                pid = str(p.get("_id") or p.get("id") or "").strip()
                if not pid or pid in retried:
                    continue
                st = str(p.get("status") or "").lower()
                if st != "failed":
                    continue
                created_dt = _parse_iso(p.get("createdAt") or p.get("scheduledFor"))
                if created_dt and (now_utc - created_dt).total_seconds() > (36.0 * 3600):
                    continue
                rr = requests.post(f"{ZERNIO_BASE}/posts/{pid}/retry", headers=_zheaders(key_val), timeout=20)
                retried.add(pid)
                if rr.status_code < 400:
                    healed += 1
                    print(f"[{ch['id']}][SELF-HEAL] تمت إعادة إرسال منشور متعثر تلقائياً ({pid})", flush=True)
                time.sleep(2)
        except Exception:
            pass

    director_state["retried_post_ids"] = list(retried)[-200:]
    return healed


# ==============================================================================
# 6) لوحة التقرير التنفيذي التلقائي بالعربية + دورة الإدارة الشاملة
# ==============================================================================

def write_director_report_md(
    channels_map: Dict[str, Dict[str, Any]],
    director_state: Dict[str, Any],
    out_md: Path = DIRECTOR_REPORT_MD,
) -> None:
    out_md.parent.mkdir(parents=True, exist_ok=True)
    now_str = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# 📊 لوحة مدير القنوات والنمو الذاتي (V16.0 — Constitution-Locked Video Lifecycle Director)",
        f"- **آخر فحص وتحديث تلقائي:** `{now_str}`",
        "- **حماية الهوية:** كل عنوان مقترح يمر على بوابة الدستور واللغة؛ لا يغيّر المدير مجال القناة أو مبادئها.",
        "- **التطوير التحريري:** `70%` للركائز الأعلى أداءً + `30%` استكشاف داخل نفس التخصص.",
        "- **منهج إنقاذ الفيديوهات:** قياس نمو الفيديو نفسه على فواصل متعددة، وانتظار بيانات يوتيوب المتأخرة قبل التشخيص؛ لا تعديل عشوائي، ولا حذف أو إعادة رفع.",
        "- **منع تقليب البيانات:** حد أقصى تجربتا عنوان وغلاف واحد لكل فيديو، مع انتظار 14 يوماً بين تغييرات العنوان، ثم إعادة قياس ما بعد التعديل.",
        "- **حدود القياس:** انخفاض المشاهدات وحده لا يثبت سبباً خوارزمياً؛ تغيير الغلاف يحتاج CTR/انطباعات كافية، وبيانات الاحتفاظ تحتاج وقت معالجة يوتيوب.",
        "",
    ]
    for cid, ch in channels_map.items():
        cst = (director_state.get("channels") or {}).get(cid) or {}
        ov = cst.get("account_overview") or {}
        ret = cst.get("retention_diagnostics") or {}
        winners = cst.get("top_winners") or []
        p_stats = cst.get("pillar_stats") or {}

        lines.append(f"## 🎬 {ch['brand_name']} (`{ch['handle']}`)")
        lines.append(
            f"- **مشاهدات آخر 30 يوماً:** فيسبوك `{ov.get('fb_views_30d', 0)}` | "
            f"يوتيوب `{ov.get('yt_views_30d', 0)}` (دقائق مشاهدة: `{ov.get('yt_watch_min_30d', 0)}`) | "
            f"تيك توك `{ov.get('tt_views_30d', 0)}`"
        )
        h3 = ret.get("avg_hold_3s")
        h3_txt = f"{h3*100:.1f}%" if h3 is not None else "قيد التجميع"
        lines.append(
            f"- **تشخيص الاحتفاظ والأداء:** بقاء أول 3 ثوانٍ `{h3_txt}` | "
            f"متوسط نقاط الشورت الخاطف `{ret.get('fast_short_avg_vps', 0)}` مقابل العميق `{ret.get('deep_short_avg_vps', 0)}` | "
            f"نمط العنوان الأقوى: `{ret.get('winning_title_style', 'mystery_statement')}`"
        )
        growth = cst.get("video_growth_summary") or {}
        lines.append("### 📈 متابعة نمو كل فيديو يوتيوب")
        if growth:
            lines.append(
                f"- **سجل المتابعة:** `{growth.get('tracked_videos', 0)}` فيديو | "
                f"حالات تعثر مؤكدة: `{growth.get('plateau_videos', 0)}` | "
                f"تجارب عناوين تراكمية: `{growth.get('title_experiments_total', 0)}` | "
                f"تجارب أغلفة تراكمية: `{growth.get('thumbnail_experiments_total', 0)}` | "
                f"إضافات قائمة التشغيل: `{growth.get('playlist_additions_total', 0)}`"
            )
            lines.append(
                f"- **آخر دورة:** صفحة أرشيف `{growth.get('analytics_page', 0)}` | "
                f"فحوص مشاهدات عامة `{growth.get('live_views_checked', 0)}` | "
                f"استعلامات يومية ناضجة `{growth.get('daily_analytics_checked', 0)}` | "
                f"استعلامات احتفاظ تفصيلية `{growth.get('retention_checked', 0)}` | "
                f"آخر إجراء: `{growth.get('latest_action', 'none')}`"
            )
            cases = growth.get("cases") or []
            reason_ar = {
                "weak_click_packaging_signal": "إشارة نقر ضعيفة مع انطباعات كافية؛ الغلاف/العنوان مرشح للاختبار",
                "weak_viewer_retention_signal": "الاحتفاظ أقل من خط القناة؛ تحسين الافتتاح للحلقات القادمة",
                "limited_or_unmeasured_distribution": "التوزيع قليل أو بيانات الانطباعات غير متاحة؛ السبب غير محسوم",
                "view_growth_flat_cause_not_proven": "النمو ثابت لكن السبب غير مثبت؛ لا تعديل أعمى",
            }
            if cases:
                lines.append("- **أبرز حالات التوقف التي تستحق المراجعة:**")
                for case in cases[:3]:
                    title = str(case.get("title") or case.get("video_id") or "فيديو")[:100]
                    reason = reason_ar.get(str(case.get("diagnosis")), "نمو بطيء يحتاج بيانات إضافية")
                    delta = case.get("views_delta_since_sample")
                    delta_txt = f"`+{delta}` منذ آخر عينة" if delta is not None else "لا توجد مقارنة بعد"
                    ctr_value = case.get("ctr")
                    ctr_txt = f"CTR `{float(ctr_value) * 100:.1f}%`" if ctr_value is not None else "CTR غير متاح"
                    avg_pct = case.get("average_view_percentage")
                    retention_txt = f"متوسط المشاهدة `{float(avg_pct):.1f}%`" if avg_pct is not None else "الاحتفاظ التفصيلي قيد التجميع"
                    link = str(case.get("url") or "")
                    lines.append(
                        f"  - «{title}» — `{case.get('views', 0)}` مشاهدة، {delta_txt}؛ {reason}؛ {ctr_txt}؛ {retention_txt}. "
                        f"[فتح الفيديو]({link})"
                    )
            else:
                lines.append("- **حالة التوقف:** لم يُثبت تعثر مستمر ببيانات كافية في هذه الدورة؛ الفيديوهات الجديدة أو قليلة العينة تنتظر اكتمال القياس.")
            if growth.get("action_note"):
                lines.append(f"- **ملاحظة الإجراء:** `{growth.get('action_note')}`")
        else:
            lines.append("- **سجل نمو الفيديوهات:** يبدأ تلقائياً عند أول دورة ناجحة مع صلاحية يوتيوب.")
        if winners:
            lines.append("- **أنجح الفيديوهات الفعلية على القناة:**")
            for w in winners[:3]:
                lines.append(
                    f"  1. «{w['title']}» (`{w['platform']}`) — المشاهدات: `{w['views']}` | الإعادات: `{w['replays']}` | النقاط: `{w['vps']}`"
                )
        ranked_pillars = sorted(
            p_stats.values(), key=lambda x: float(x.get("avg_vps") or 0.0), reverse=True
        )
        active_pillars = [p for p in ranked_pillars if int(p.get("posts") or 0) > 0]
        if active_pillars:
            top_p = active_pillars[0]
            lines.append(
                f"- **الركيزة المتصدرة داخل تخصص القناة:** «{top_p['label']}» (متوسط النقاط: `{top_p['avg_vps']}` من `{top_p['posts']}` منشورات)"
            )
        lines.append("")

    out_md.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def run_director_housekeeping(
    channels_map: Dict[str, Dict[str, Any]],
    memory: Dict[str, Any],
    llm_json_fn: Optional[Callable[..., Dict[str, Any]]] = None,
    groq_key: str = "",
    growth_llm_json_fn: Optional[Callable[..., Dict[str, Any]]] = None,
    growth_llm_key: str = "",
) -> Dict[str, Any]:
    """
    دورة الإدارة الذكية الشاملة (تعمل بأمان فائق Fail-Open دون أن تعطل إنتاج الفيديوهات إطلاقاً).
    """
    from video_growth_manager import load_video_growth_state, run_video_growth_cycle, save_video_growth_state

    state = load_director_state()
    growth_state = load_video_growth_state(list(channels_map.keys()))
    growth_llm_json_fn = growth_llm_json_fn or llm_json_fn
    growth_llm_key = growth_llm_key or groq_key
    print("=== [AI CHANNEL DIRECTOR V16.0] بدء تحليل نمو كل فيديو يوتيوب والتطوير الذاتي المحكوم بالدستور ===", flush=True)
    for cid, ch in channels_map.items():
        try:
            healed = heal_failed_scheduled_posts(ch, state)
            ch_st = harvest_channel_telemetry(ch, memory, state)
            try:
                growth = run_video_growth_cycle(
                    channel=ch,
                    director_state=state,
                    growth_state=growth_state,
                    llm_json_fn=growth_llm_json_fn,
                    llm_key=growth_llm_key,
                    text_validator=validate_text_against_constitution,
                )
            except Exception as growth_err:
                growth = {}
                print(f"  [GROWTH-WARN] تخطي آمن لتحليل نمو الفيديوهات في {cid}: {growth_err}", flush=True)
            replies = manage_audience_comments(ch, state, llm_json_fn=llm_json_fn, groq_key=groq_key)
            ov = ch_st.get("account_overview") or {}
            ret = ch_st.get("retention_diagnostics") or {}
            print(
                f"  📊 [{cid}] ({ch['brand_name']}): FB_30d={ov.get('fb_views_30d', 0)} | "
                f"YT_30d={ov.get('yt_views_30d', 0)} | TT_30d={ov.get('tt_views_30d', 0)} | "
                f"tracked_posts={ret.get('evaluated_posts', 0)} | YT_videos={growth.get('tracked_videos', 0)} | "
                f"plateaus={growth.get('plateau_videos', 0)} | growth_action={growth.get('latest_action', 'none')} | "
                f"replies={replies} | healed={healed}",
                flush=True,
            )
        except Exception as exc:
            print(f"  [DIRECTOR-WARN] تخطي آمن لخطأ غير مؤثر في متابعة {cid}: {exc}", flush=True)

    try:
        save_video_growth_state(growth_state)
    except Exception as exc:
        print(f"  [GROWTH-WARN] تعذر حفظ سجل نمو الفيديوهات، لكن دورة النشر مستمرة: {exc}", flush=True)
    try:
        save_director_state(state)
        write_director_report_md(channels_map, state)
    except Exception as exc:
        print(f"  [DIRECTOR-WARN] تعذر حفظ ملف تقرير المدير: {exc}", flush=True)

    return state
