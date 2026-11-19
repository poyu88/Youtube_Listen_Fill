import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchVideo } from "../api";
import BlankFill from "../components/BlankFill";
import PlaybackControls from "../components/PlaybackControls";
import SegmentList from "../components/SegmentList";
import YouTubePlayer, { type YouTubePlayerHandle } from "../components/YouTubePlayer";
import type { PlayMode, VideoDetail } from "../types";

/**
 * 練習頁：播放器、分段列表、速度／模式控制與挖空練習。
 */
export default function Practice() {
  const { videoId = "" } = useParams();
  const [video, setVideo] = useState<VideoDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [speed, setSpeed] = useState(1);
  const [mode, setMode] = useState<PlayMode>("once");

  const playerRef = useRef<YouTubePlayerHandle | null>(null);
  const modeRef = useRef(mode);
  const currentIndexRef = useRef(currentIndex);
  const videoRef = useRef(video);
  const loopTimerRef = useRef<number | null>(null);
  const watchingRef = useRef(false);

  useEffect(() => {
    modeRef.current = mode;
  }, [mode]);

  useEffect(() => {
    currentIndexRef.current = currentIndex;
  }, [currentIndex]);

  useEffect(() => {
    videoRef.current = video;
  }, [video]);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    setVideo(null);

    void fetchVideo(videoId)
      .then((data) => {
        if (!cancelled) {
          setVideo(data);
          setCurrentIndex(0);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "載入失敗");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [videoId]);

  const clearLoopTimer = useCallback(() => {
    if (loopTimerRef.current != null) {
      window.clearTimeout(loopTimerRef.current);
      loopTimerRef.current = null;
    }
  }, []);

  const playSegment = useCallback(
    (index: number) => {
      const data = videoRef.current;
      const player = playerRef.current;
      if (!data || !player) return;
      const segment = data.segments[index];
      if (!segment) return;

      clearLoopTimer();
      watchingRef.current = true;
      setCurrentIndex(index);
      currentIndexRef.current = index;
      player.seekAndPlay(segment.start);
    },
    [clearLoopTimer],
  );

  const handlePlayerReady = useCallback(
    (handle: YouTubePlayerHandle) => {
      playerRef.current = handle;
      handle.setPlaybackRate(speed);
      playSegment(currentIndexRef.current);
    },
    [playSegment, speed],
  );

  const handleTimeUpdate = useCallback(
    (time: number) => {
      if (!watchingRef.current) return;
      const data = videoRef.current;
      if (!data) return;
      const segment = data.segments[currentIndexRef.current];
      if (!segment) return;

      if (time >= segment.end - 0.05) {
        watchingRef.current = false;
        playerRef.current?.pause();

        if (modeRef.current === "loop") {
          clearLoopTimer();
          loopTimerRef.current = window.setTimeout(() => {
            playSegment(currentIndexRef.current);
          }, 2000);
        }
      }
    },
    [clearLoopTimer, playSegment],
  );

  useEffect(() => {
    playerRef.current?.setPlaybackRate(speed);
  }, [speed]);

  useEffect(() => () => clearLoopTimer(), [clearLoopTimer]);

  function goPrev() {
    if (currentIndex <= 0) return;
    playSegment(currentIndex - 1);
  }

  function goNext() {
    if (!video || currentIndex >= video.segments.length - 1) return;
    playSegment(currentIndex + 1);
  }

  if (error) {
    return (
      <div className="page">
        <Link to="/" className="back-link">
          ← 返回
        </Link>
        <p className="error-banner">{error}</p>
      </div>
    );
  }

  if (!video) {
    return (
      <div className="page">
        <p>載入中…</p>
      </div>
    );
  }

  const current = video.segments[currentIndex];

  return (
    <div className="page practice-page">
      <header className="practice-header">
        <Link to="/" className="back-link">
          ← 返回
        </Link>
        <h1>{video.title}</h1>
      </header>

      <div className="practice-layout">
        <section className="player-panel">
          <button
            type="button"
            className="nav-arrow"
            onClick={goPrev}
            disabled={currentIndex <= 0}
            aria-label="上一句"
          >
            ◀
          </button>
          <div className="player-frame">
            <YouTubePlayer
              videoId={video.id}
              onReady={handlePlayerReady}
              onTimeUpdate={handleTimeUpdate}
            />
          </div>
          <button
            type="button"
            className="nav-arrow"
            onClick={goNext}
            disabled={currentIndex >= video.segments.length - 1}
            aria-label="下一句"
          >
            ▶
          </button>
        </section>

        <aside className="sidebar-panel">
          <SegmentList
            segments={video.segments}
            currentIndex={currentIndex}
            onSelect={playSegment}
          />
          <PlaybackControls
            speed={speed}
            mode={mode}
            onSpeedChange={setSpeed}
            onModeChange={(next) => {
              clearLoopTimer();
              setMode(next);
            }}
          />
        </aside>

        <section className="practice-bottom">
          {current && (
            <BlankFill
              key={current.index}
              tokens={current.tokens}
              segmentKey={current.index}
            />
          )}
        </section>
      </div>
    </div>
  );
}
