"""使用 yt-dlp 取得 YouTube 中繼資料與英文字幕。"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL

from .srt import parse_srt
from .vtt import parse_vtt


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


def _prefer_subtitle_file(candidates: list[Path], ext: str) -> Path | None:
    """從候選檔中挑選較佳的英文字幕檔。"""
    if not candidates:
        return None
    preferred = [
        p
        for p in candidates
        if p.name.lower().endswith(f".en.{ext}") or f".en.{ext}" in p.name.lower()
    ]
    # 避開 en-orig 以外、優先純 .en.
    pure_en = [p for p in preferred if ".en-orig." not in p.name.lower()]
    if pure_en:
        return pure_en[0]
    if preferred:
        return preferred[0]
    return candidates[0]


def fetch_video_with_subs(url: str) -> dict[str, Any]:
    """
    依 URL 取得影片資訊與英文字幕，並解析成分段。

    優先下載 VTT（保留 YouTube 自動字幕逐字時間），其次 SRT。
    不下載影片本體。
    """
    with tempfile.TemporaryDirectory(prefix="ylf_subs_") as tmp:
        outtmpl = str(Path(tmp) / "%(id)s")
        ydl_opts: dict[str, Any] = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en", "en-US", "en-GB"],
            # 優先 VTT，才能利用 karaoke 逐字時間重建不重疊分段
            "subtitlesformat": "vtt",
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

        vtt_candidates = sorted(Path(tmp).glob(f"{video_id}*.vtt"))
        srt_candidates = sorted(Path(tmp).glob(f"{video_id}*.srt"))
        vtt_path = _prefer_subtitle_file(vtt_candidates, "vtt")
        srt_path = _prefer_subtitle_file(srt_candidates, "srt")

        segments: list[dict[str, Any]] = []
        if vtt_path and vtt_path.exists():
            vtt_content = vtt_path.read_text(encoding="utf-8", errors="replace")
            segments = parse_vtt(vtt_content)
        elif srt_path and srt_path.exists():
            srt_content = srt_path.read_text(encoding="utf-8", errors="replace")
            segments = parse_srt(srt_content)
        else:
            manual = info.get("subtitles") or {}
            auto = info.get("automatic_captions") or {}
            if not _pick_english_sub_key(manual) and not _pick_english_sub_key(auto):
                raise YoutubeImportError("此影片沒有可用的英文字幕")
            raise YoutubeImportError("已偵測到英文字幕但無法下載字幕檔")

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
