import type { VideoDetail, VideoSummary } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });

  if (!response.ok) {
    let detail = `請求失敗（${response.status}）`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

/** 取得已匯入影片列表。 */
export function fetchVideos(): Promise<VideoSummary[]> {
  return request<VideoSummary[]>("/api/videos");
}

/** 取得單一影片詳情。 */
export function fetchVideo(id: string): Promise<VideoDetail> {
  return request<VideoDetail>(`/api/videos/${id}`);
}

/** 從 YouTube URL 匯入影片。 */
export function importVideo(url: string): Promise<VideoDetail> {
  return request<VideoDetail>("/api/videos/import", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}
