# -*- coding: utf-8 -*-
"""
ناشر الإمبراطورية V13.0 — محرك الانتشار السريع وكسر حاجز الـ 200 مشاهدة (1 فيلم كامل + 4 شورتس يومياً)
- يرفع الصورة المصغرة المخصصة بحقل Zernio الرسمي (`"thumbnail"`) لرفع CTR على يوتيوب وفيسبوك من أول لحظة!
- ينشر 4 مقاطع شورتس يومياً لكل قناة (2 شورتس خاطفة <55 ثانية + 2 شورتس درامية عميقة) موزعة زمنياً كل 3 ساعات على مدار اليوم!
- يعالج سبب الـ 0 مشاهدة على تيك توك بحذف أي روابط يوتيوب خارجية أو كلمة `#shorts` من وصف تيك توك واستبدالها بسؤال جدلي (١ أو ٢) + هاشتاجات FYP أصلية!
- يفصل نشر كل منصة بشكل مستقل (Fault Isolation) حتى لا يؤثر حد النشر اليومي المؤقت لأي منصة على باقي المنصات!
"""

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


def _strip_hashtags(txt: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"#\S+", "", txt)).strip(" -—|")


def _apply_timing(payload: Dict[str, Any], delay_hours: float) -> Dict[str, Any]:
    if delay_hours <= 0.05:
        payload["publishNow"] = True
    else:
        sched_epoch = time.time() + delay_hours * 3600.0
        payload["scheduledFor"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(sched_epoch))
    return payload


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

    shorts_files = [
        ("short_3", "short_3_title", "cta_spoken_3", short3_mp4, short3_cover, 0.0),   # الموجة 1 فوراً: الشورت الخاطف 38ث
        ("short_1", "short_1_title", "cta_spoken_1", short1_mp4, short1_cover, 3.0),   # الموجة 2 (+3 ساعات): الشورت الدرامي العميق الأول
        ("short_4", "short_4_title", "cta_spoken_4", short4_mp4, short4_cover, 6.0),   # الموجة 3 (+6 ساعات): الشورت الخاطف الثاني 50ث
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
    }

    # 1) نشر الحلقة الكاملة على يوتيوب + فيسبوك مع الصورة المصغرة المخصصة ("thumbnail")
    if yt_acc:
        payload_yt_long = {
            "title": ep_title,
            "content": full_yt_description,
            "tags": tags_list,
            "publishNow": True,
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
        }
        r_yt = requests.post(f"{ZERNIO_BASE}/posts", headers=_headers(main_key), json=payload_yt_long, timeout=180)
        if r_yt.status_code < 400:
            yt_data = r_yt.json()
            results["long_video"]["youtube"] = yt_data
            post_id = yt_data.get("post", yt_data).get("_id") or yt_data.get("post", yt_data).get("id")
            yt_watch = _extract_youtube_url(yt_data)
            if not yt_watch and post_id:
                yt_watch = wait_for_youtube_url(main_key, post_id, max_wait_sec=140)
            results["youtube_watch_url"] = yt_watch
        else:
            print(f"[{ch['id']}][WARN] تعذر رفع الفيلم الطويل على يوتيوب مؤقتاً ({r_yt.status_code}): {r_yt.text[:240]}", flush=True)
            results["long_video"]["youtube_error"] = r_yt.text[:300]

    if fb_acc:
        payload_fb_long = {
            "title": ep_title,
            "content": full_yt_description,
            "publishNow": True,
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
        }
        r_fb = requests.post(f"{ZERNIO_BASE}/posts", headers=_headers(main_key), json=payload_fb_long, timeout=180)
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

    # 2) نشر وجدولة الـ 4 مقاطع شورتس على مدار اليوم (بفصل مستقل لكل منصة لضمان عدم تعطل أي منصة)
    for item in uploaded_shorts:
        s_id = item["id"]
        delay_h = float(item["delay_hours"])
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
            # وصف تيك توك نظيف 100% بدون أي رابط يوتيوب خارجي أو كلمة #shorts لتفادي كتم الوصول (0 Views)
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
        short_res: Dict[str, Any] = {"delay_hours": delay_h}
        s_media_item: Dict[str, Any] = {"type": "video", "url": item["main_url"]}
        if item.get("cover_url"):
            s_media_item["thumbnail"] = item["cover_url"]

        if yt_acc:
            yt_s_payload = _apply_timing(
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
                delay_h,
            )
            ry = requests.post(f"{ZERNIO_BASE}/posts", headers=_headers(main_key), json=yt_s_payload, timeout=180)
            if ry.status_code < 400:
                short_res["youtube"] = ry.json()
            else:
                print(f"[{ch['id']}][WARN] يوتيوب {s_id} ({ry.status_code}): {ry.text[:200]}", flush=True)
                short_res["youtube_error"] = ry.text[:260]

        if fb_acc:
            fb_s_payload = _apply_timing(
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
                delay_h,
            )
            rf = requests.post(f"{ZERNIO_BASE}/posts", headers=_headers(main_key), json=fb_s_payload, timeout=180)
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

            tt_payload = _apply_timing(
                {
                    "content": tt_caption[:2000],
                    "mediaItems": [{"type": "video", "url": item["tt_url"]}],
                    "platforms": [{
                        "platform": "tiktok",
                        "accountId": tt_acc,
                        "platformSpecificData": tt_spec_data,
                    }],
                },
                delay_h,
            )
            rtt = requests.post(f"{ZERNIO_BASE}/posts", headers=_headers(tt_key), json=tt_payload, timeout=180)
            if rtt.status_code < 400:
                short_res["tiktok"] = rtt.json()
            else:
                print(f"[{ch['id']}][WARN] تيك توك {s_id} ({rtt.status_code}): {rtt.text[:200]}", flush=True)
                short_res["tiktok_error"] = rtt.text[:260]

        results[s_id] = short_res
        time.sleep(2)

    return results
