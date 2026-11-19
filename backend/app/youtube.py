"""使用 yt-dlp 取得 YouTube 中繼資料與英文字幕。"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL

from .srt import parse_srt


class YoutubeImportError(Exception):
    """YouTube 匯入失敗時拋出的錯誤。"""


def _pick_english_sub_key(subtitles: dict[str, Any]) -> str | None:
    """從字幕字典中挑選英文字幕鍵（優先 en，其次 en-*）。"""
    if not subtitles:
        return None
    if "en" in subtitles:
        return "en"
    for key in subtitles:
        if key.lower().startswith("en"):
            return key
    return None


def fetch_video_with_subs(url: str) -> dict[str, Any]:
    """
    依 URL 取得影片資訊與英文字幕，並解析成分段。

    優先使用人工字幕，其次自動字幕。不下載影片本體。
    """
    with tempfile.TemporaryDirectory(prefix="ylf_subs_") as tmp:
        outtmpl = str(Path(tmp) / "%(id)s")
        ydl_opts: dict[str, Any] = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en", "en-US", "en-GB"],
            "subtitlesformat": "srt",
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
        except Exception as exc:  # noqa: BLE001 — 轉成業務錯誤
            raise YoutubeImportError(f"無法取得影片資訊：{exc}") from exc

        if not info:
            raise YoutubeImportError("無法解析此 YouTube URL")

        video_id = info.get("id")
        if not video_id:
            raise YoutubeImportError("缺少影片 ID")

        # yt-dlp 可能寫出 .en.srt / .en-US.srt 等
        srt_path: Path | None = None
        candidates = sorted(Path(tmp).glob(f"{video_id}*.srt"))
        if candidates:
            # 優先檔名含純 .en.
            preferred = [p for p in candidates if ".en." in p.name.lower()]
            srt_path = preferred[0] if preferred else candidates[0]

        srt_content = ""
        if srt_path and srt_path.exists():
            srt_content = srt_path.read_text(encoding="utf-8", errors="replace")
        else:
            # 後備：從 info 中確認是否有英文軌
            manual = info.get("subtitles") or {}
            auto = info.get("automatic_captions") or {}
            if not _pick_english_sub_key(manual) and not _pick_english_sub_key(auto):
                raise YoutubeImportError("此影片沒有可用的英文字幕")
            raise YoutubeImportError("已偵測到英文字幕但無法下載 SRT 檔")

        segments = parse_srt(srt_content)
        if not segments:
            raise YoutubeImportError("英文字幕解析後沒有可用分段")

        thumbnails = info.get("thumbnails") or []
        thumbnail = info.get("thumbnail") or (
            thumbnails[-1].get("url") if thumbnails else ""
        )

        return {
            "id": video_id,
            "title": info.get("title") or "",
            "channel": info.get("channel") or info.get("uploader") or "",
            "duration": int(info.get("duration") or 0),
            "thumbnail": thumbnail or "",
            "url": info.get("webpage_url") or url,
            "segments": segments,
        }
