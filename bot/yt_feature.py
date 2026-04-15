from .shared import *
import asyncio
import uuid
import os
import glob

YT_TMP = "/tmp"

# ─── حجم Telegram البوت الأقصى ───────────────────────────────────
TG_MAX_BYTES = 49 * 1024 * 1024  # 49 MB

def format_duration(secs):
    if not secs:
        return ""
    try:
        secs = int(secs)
        h = secs // 3600
        m = (secs % 3600) // 60
        s = secs % 60
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"
    except Exception:
        return ""

# ─── البحث ───────────────────────────────────────────────────────
def _yt_search_sync(query: str, limit: int):
    import yt_dlp
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "geo_bypass": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        results = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
        entries = results.get("entries", []) or []
        out = []
        for e in entries:
            if not e:
                continue
            out.append({
                "id": e.get("id") or e.get("url", ""),
                "title": e.get("title", "بدون عنوان"),
                "duration": e.get("duration"),
                "channel": e.get("channel") or e.get("uploader", ""),
            })
        return out

async def yt_search(query: str, limit: int = 10):
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _yt_search_sync, query, limit)
    except Exception as e:
        logging.warning(f"yt_search error: {e}")
        return []

# ─── تحميل الفيديو ────────────────────────────────────────────────
def _download_video_sync(video_id: str):
    import yt_dlp
    uid_str = uuid.uuid4().hex
    out_tmpl = f"{YT_TMP}/ytvid_{uid_str}.%(ext)s"

    # جرب تصاعدياً من الأقل جودة للحصول على ملف بأقل حجم
    formats_to_try = [
        "worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]/worst",
        "bestvideo[height<=240][ext=mp4]+bestaudio/best[height<=240]/worst",
        "bestvideo[height<=360][ext=mp4]+bestaudio/best[height<=360]",
    ]

    base_opts = {
        "quiet": True,
        "no_warnings": True,
        "outtmpl": out_tmpl,
        "merge_output_format": "mp4",
        "geo_bypass": True,
        "ignoreerrors": False,
    }

    last_error = None
    for fmt in formats_to_try:
        # امسح أي ملف سابق بنفس الاسم
        for f in glob.glob(f"{YT_TMP}/ytvid_{uid_str}.*"):
            try:
                os.remove(f)
            except Exception:
                pass

        opts = {**base_opts, "format": fmt}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(
                    f"https://www.youtube.com/watch?v={video_id}",
                    download=True
                )
                title = info.get("title", "فيديو")
                duration = info.get("duration")

            for ext in ("mp4", "mkv", "webm", "avi", "mov"):
                path = f"{YT_TMP}/ytvid_{uid_str}.{ext}"
                if os.path.exists(path):
                    size = os.path.getsize(path)
                    if size > TG_MAX_BYTES:
                        os.remove(path)
                        last_error = f"file_too_large:{size}"
                        break
                    return path, title, duration

        except Exception as e:
            err_str = str(e)
            last_error = err_str
            # إذا كان الفيديو غير متاح لا فائدة من تجربة صيغ أخرى
            if "not available" in err_str or "Private video" in err_str or "This video has been removed" in err_str:
                break
            continue

    return None, last_error, None

async def download_yt_video(video_id: str):
    """يُعيد (path, title, duration) أو (None, error_msg, None)"""
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _download_video_sync, video_id)
    except Exception as e:
        logging.warning(f"download_yt_video outer error: {e}")
        return None, str(e), None

# ─── تحميل الصوت ─────────────────────────────────────────────────
def _download_audio_sync(video_id: str):
    import yt_dlp
    uid_str = uuid.uuid4().hex
    out_tmpl = f"{YT_TMP}/ytaud_{uid_str}.%(ext)s"

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio",
        "outtmpl": out_tmpl,
        "geo_bypass": True,
        "ignoreerrors": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}",
                download=True
            )
            title = info.get("title", "صوت")
            duration = info.get("duration")

        for ext in ("m4a", "webm", "ogg", "opus", "mp3"):
            path = f"{YT_TMP}/ytaud_{uid_str}.{ext}"
            if os.path.exists(path):
                size = os.path.getsize(path)
                if size > TG_MAX_BYTES:
                    os.remove(path)
                    return None, f"file_too_large:{size}", None
                return path, title, duration

        return None, "file_not_found", None

    except Exception as e:
        logging.warning(f"download_yt_audio error: {e}")
        return None, str(e), None

async def download_yt_audio(video_id: str):
    """يُعيد (path, title, duration) أو (None, error_msg, None)"""
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, _download_audio_sync, video_id)
    except Exception as e:
        logging.warning(f"download_yt_audio outer error: {e}")
        return None, str(e), None

# ─── تنظيف ملفات مؤقتة ───────────────────────────────────────────
def cleanup_tmp(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

# ─── رسالة الخطأ الواضحة ─────────────────────────────────────────
def yt_error_message(error_str: str, is_video: bool) -> str:
    mode = "الفيديو" if is_video else "الصوت"
    if not error_str:
        return f"❌ تعذر تحميل {mode}. حاول فيديو آخر."
    if "file_too_large" in error_str:
        mb = ""
        try:
            mb = f" ({int(error_str.split(':')[1]) // 1024 // 1024} MB)"
        except Exception:
            pass
        return (
            f"❌ *الملف كبير جداً{mb}*\n\n"
            f"حجم {mode} يتجاوز 50MB وهو الحد المسموح به في تيليجرام.\n"
            "جرب فيديو أقصر أو اختر الاستماع للصوت فقط 🎵"
        )
    if "not available" in error_str or "not available" in error_str.lower():
        return (
            f"❌ *{mode} غير متاح*\n\n"
            "هذا الفيديو محمي أو غير متاح في منطقتنا.\n"
            "اختر فيديو آخر من النتائج 🔙"
        )
    if "Private video" in error_str:
        return f"❌ *فيديو خاص*\n\nهذا الفيديو خاص ولا يمكن تحميله."
    if "copyright" in error_str.lower():
        return f"❌ *محمي بحقوق النشر*\n\nلا يمكن تحميل هذا {mode}."
    return (
        f"❌ *تعذر تحميل {mode}*\n\n"
        "حاول فيديو آخر من النتائج 🔙"
    )

# ─── النص الافتراضي عند ضغط الزر ────────────────────────────────
def default_yt_prompt():
    return (
        "🎬 *بحث يوتيوب*\n\n"
        "أرسل عنوان الفيديو أو الأغنية التي تريد البحث عنها:"
    )
