"""本機 JSON 儲存：影片清單與分段資料。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# 專案根目錄下的 data/
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
INDEX_PATH = DATA_DIR / "videos.json"


def ensure_data_dir() -> None:
    """確保資料目錄存在。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not INDEX_PATH.exists():
        INDEX_PATH.write_text("[]", encoding="utf-8")


def _read_index() -> list[dict[str, Any]]:
    """讀取影片索引。"""
    ensure_data_dir()
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def _write_index(items: list[dict[str, Any]]) -> None:
    """寫入影片索引。"""
    ensure_data_dir()
    INDEX_PATH.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _detail_path(video_id: str) -> Path:
    """取得單一影片詳情檔路徑。"""
    return DATA_DIR / f"{video_id}.json"


def list_videos() -> list[dict[str, Any]]:
    """列出所有已匯入影片的摘要。"""
    return _read_index()


def get_video(video_id: str) -> dict[str, Any] | None:
    """讀取單一影片詳情（含分段）。"""
    path = _detail_path(video_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_video(video: dict[str, Any]) -> dict[str, Any]:
    """
    儲存或更新影片詳情，並同步索引摘要。

    video 需含 id、title、channel、duration、thumbnail、segments。
    """
    ensure_data_dir()
    video_id = video["id"]
    _detail_path(video_id).write_text(
        json.dumps(video, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = {
        "id": video_id,
        "title": video.get("title", ""),
        "channel": video.get("channel", ""),
        "duration": video.get("duration", 0),
        "thumbnail": video.get("thumbnail", ""),
        "segment_count": len(video.get("segments", [])),
    }
    index = _read_index()
    index = [item for item in index if item.get("id") != video_id]
    index.insert(0, summary)
    _write_index(index)
    return video
