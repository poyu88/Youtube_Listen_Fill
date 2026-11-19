import { useEffect, useId, useRef } from "react";

let apiPromise: Promise<void> | null = null;

/** 確保 YouTube IFrame API 腳本已載入。 */
function loadYouTubeApi(): Promise<void> {
  if (window.YT?.Player) return Promise.resolve();
  if (apiPromise) return apiPromise;

  apiPromise = new Promise((resolve) => {
    const existing = document.querySelector('script[src="https://www.youtube.com/iframe_api"]');
    if (!existing) {
      const tag = document.createElement("script");
      tag.src = "https://www.youtube.com/iframe_api";
      document.head.appendChild(tag);
    }
    const previous = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => {
      previous?.();
      resolve();
    };
    if (window.YT?.Player) resolve();
  });

  return apiPromise;
}

export interface YouTubePlayerHandle {
  seekAndPlay: (start: number) => void;
  pause: () => void;
  getCurrentTime: () => number;
  setPlaybackRate: (rate: number) => void;
}

interface YouTubePlayerProps {
  videoId: string;
  onReady?: (handle: YouTubePlayerHandle) => void;
  onTimeUpdate?: (time: number) => void;
}

/**
 * YouTube 內嵌播放器封裝，提供 seek／暫停／速率控制。
 */
export default function YouTubePlayer({ videoId, onReady, onTimeUpdate }: YouTubePlayerProps) {
  const reactId = useId().replace(/:/g, "");
  const elementId = `yt-player-${reactId}`;
  const playerRef = useRef<YTPlayer | null>(null);
  const pollRef = useRef<number | null>(null);
  const onReadyRef = useRef(onReady);
  const onTimeUpdateRef = useRef(onTimeUpdate);

  useEffect(() => {
    onReadyRef.current = onReady;
    onTimeUpdateRef.current = onTimeUpdate;
  }, [onReady, onTimeUpdate]);

  useEffect(() => {
    let cancelled = false;

    const stopPoll = () => {
      if (pollRef.current != null) {
        window.clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };

    const startPoll = () => {
      stopPoll();
      pollRef.current = window.setInterval(() => {
        const player = playerRef.current;
        if (!player) return;
        onTimeUpdateRef.current?.(player.getCurrentTime());
      }, 100);
    };

    void loadYouTubeApi().then(() => {
      if (cancelled || !window.YT) return;

      playerRef.current = new window.YT.Player(elementId, {
        videoId,
        playerVars: {
          rel: 0,
          modestbranding: 1,
          playsinline: 1,
        },
        events: {
          onReady: () => {
            const player = playerRef.current;
            if (!player) return;
            const handle: YouTubePlayerHandle = {
              seekAndPlay: (start: number) => {
                player.seekTo(start, true);
                player.playVideo();
              },
              pause: () => player.pauseVideo(),
              getCurrentTime: () => player.getCurrentTime(),
              setPlaybackRate: (rate: number) => player.setPlaybackRate(rate),
            };
            onReadyRef.current?.(handle);
            startPoll();
          },
          onStateChange: (event) => {
            if (event.data === window.YT?.PlayerState.PLAYING) {
              startPoll();
            }
          },
        },
      });
    });

    return () => {
      cancelled = true;
      stopPoll();
      playerRef.current?.destroy();
      playerRef.current = null;
    };
  }, [elementId, videoId]);

  return <div id={elementId} className="yt-iframe" />;
}
