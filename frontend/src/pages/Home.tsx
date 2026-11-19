import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { fetchVideos, importVideo } from "../api";
import type { VideoSummary } from "../types";
import { formatDuration } from "../utils";

/**
 * 影片庫首頁：貼上 YouTube URL 匯入，並顯示卡片列表。
 */
export default function Home() {
  const [url, setUrl] = useState("");
  const [videos, setVideos] = useState<VideoSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadVideos = useCallback(async () => {
    try {
      const list = await fetchVideos();
      setVideos(list);
    } catch (err) {
      setError(err instanceof Error ? err.message : "無法載入影片列表");
    }
  }, []);

  useEffect(() => {
    void loadVideos();
  }, [loadVideos]);

  async function handleImport(event: FormEvent) {
    event.preventDefault();
    const trimmed = url.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);
    try {
      await importVideo(trimmed);
      setUrl("");
      await loadVideos();
    } catch (err) {
      setError(err instanceof Error ? err.message : "匯入失敗");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page home-page">
      <header className="page-header">
        <h1>YouTube 聽打練習</h1>
        <p className="subtitle">貼上影片連結，練習英文聽力與拼寫</p>
      </header>

      <form className="import-form" onSubmit={handleImport}>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://www.youtube.com/watch?v=..."
          disabled={loading}
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? "匯入中…" : "匯入"}
        </button>
      </form>

      {error && <p className="error-banner">{error}</p>}

      <section className="video-grid">
        {videos.length === 0 && !loading && (
          <p className="empty-hint">尚無影片，請先匯入一支有英文字幕的 YouTube 影片。</p>
        )}
        {videos.map((video) => (
          <Link key={video.id} to={`/practice/${video.id}`} className="video-card">
            <div className="video-card-thumb">
              {video.thumbnail ? (
                <img src={video.thumbnail} alt="" loading="lazy" />
              ) : (
                <div className="thumb-placeholder" />
              )}
              <span className="duration-badge">{formatDuration(video.duration)}</span>
            </div>
            <div className="video-card-body">
              <h2>{video.title}</h2>
              <p>{video.channel}</p>
              <p className="meta">{video.segment_count} 個分段</p>
            </div>
          </Link>
        ))}
      </section>
    </div>
  );
}
