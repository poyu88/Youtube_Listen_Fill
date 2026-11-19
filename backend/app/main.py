"""FastAPI 應用入口：影片匯入與查詢 API。"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .store import get_video, list_videos, save_video
from .youtube import YoutubeImportError, fetch_video_with_subs

app = FastAPI(title="YouTube Listen Fill API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ImportRequest(BaseModel):
    """匯入 YouTube 影片的請求本體。"""

    url: str = Field(..., min_length=1, description="YouTube 影片 URL")


@app.get("/api/health")
def health() -> dict[str, str]:
    """健康檢查。"""
    return {"status": "ok"}


@app.get("/api/videos")
def api_list_videos() -> list[dict[str, Any]]:
    """取得已匯入影片列表。"""
    return list_videos()


@app.get("/api/videos/{video_id}")
def api_get_video(video_id: str) -> dict[str, Any]:
    """取得單一影片詳情與分段。"""
    video = get_video(video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="找不到此影片")
    return video


@app.post("/api/videos/import")
def api_import_video(body: ImportRequest) -> dict[str, Any]:
    """從 YouTube URL 匯入中繼資料與英文字幕分段。"""
    try:
        video = fetch_video_with_subs(body.url.strip())
    except YoutubeImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"匯入失敗：{exc}") from exc

    return save_video(video)
