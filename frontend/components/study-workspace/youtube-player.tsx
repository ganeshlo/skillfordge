"use client";

import { forwardRef, useEffect, useId, useImperativeHandle, useRef } from "react";

type Player = {
  destroy(): void;
  getCurrentTime(): number;
  getDuration(): number;
  getPlaybackRate(): number;
  seekTo(seconds: number, allowSeekAhead: boolean): void;
};
type YTApi = {
  Player: new (id: string, options: Record<string, unknown>) => Player;
  PlayerState: { PLAYING: number; PAUSED: number; ENDED: number };
};
declare global {
  interface Window {
    YT?: YTApi;
    onYouTubeIframeAPIReady?: () => void;
  }
}

export type YouTubePlayerHandle = {
  seekTo(seconds: number): void;
  currentTime(): number;
  flush(): void;
};

let loader: Promise<YTApi> | null = null;
function apiReady() {
  if (window.YT) return Promise.resolve(window.YT);
  if (!loader) {
    loader = new Promise((resolve) => {
      window.onYouTubeIframeAPIReady = () => window.YT && resolve(window.YT);
      if (!document.querySelector('script[src="https://www.youtube.com/iframe_api"]')) {
        const script = document.createElement("script");
        script.src = "https://www.youtube.com/iframe_api";
        document.head.appendChild(script);
      }
    });
  }
  return loader;
}

export const YouTubePlayer = forwardRef<
  YouTubePlayerHandle,
  {
    videoId: string;
    resumeAt: number;
    onTick: (time: number, duration: number) => void;
    onWatched: (
      start: number,
      end: number,
      position: number,
      duration: number,
      speed: number,
    ) => void;
  }
>(function YouTubePlayer({ videoId, resumeAt, onTick, onWatched }, ref) {
  const id = `yt-${useId().replaceAll(":", "")}`;
  const player = useRef<Player | null>(null);
  const playing = useRef(false);
  const segmentStart = useRef<number | null>(null);
  const lastObserved = useRef(0);

  const flush = () => {
    if (!player.current || segmentStart.current === null) return;
    const position = Math.floor(lastObserved.current || player.current.getCurrentTime());
    const start = Math.floor(segmentStart.current);
    if (position > start) {
      onWatched(
        start,
        position,
        Math.floor(player.current.getCurrentTime()),
        Math.floor(player.current.getDuration()),
        player.current.getPlaybackRate(),
      );
    }
    segmentStart.current = playing.current ? player.current.getCurrentTime() : null;
    lastObserved.current = player.current.getCurrentTime();
  };

  useImperativeHandle(ref, () => ({
    seekTo(seconds) {
      flush();
      player.current?.seekTo(seconds, true);
      segmentStart.current = seconds;
      lastObserved.current = seconds;
    },
    currentTime: () => player.current?.getCurrentTime() ?? 0,
    flush,
  }));

  useEffect(() => {
    let stopped = false;
    void apiReady().then((YT) => {
      if (stopped) return;
      player.current = new YT.Player(id, {
        videoId,
        playerVars: { start: Math.floor(resumeAt), rel: 0, playsinline: 1 },
        events: {
          onReady: () => {
            lastObserved.current = resumeAt;
            if (player.current) onTick(resumeAt, player.current.getDuration());
          },
          onStateChange: (event: { data: number }) => {
            if (event.data === YT.PlayerState.PLAYING) {
              const current = player.current?.getCurrentTime() ?? 0;
              playing.current = true;
              segmentStart.current = current;
              lastObserved.current = current;
            } else if (
              event.data === YT.PlayerState.PAUSED ||
              event.data === YT.PlayerState.ENDED
            ) {
              flush();
              playing.current = false;
              segmentStart.current = null;
            }
          },
        },
      });
    });

    const tick = window.setInterval(() => {
      if (!player.current) return;
      const current = player.current.getCurrentTime();
      const duration = player.current.getDuration();
      if (playing.current) {
        const expectedMaximum = Math.max(3, player.current.getPlaybackRate() * 2.5);
        const delta = current - lastObserved.current;
        if (delta < -0.5 || delta > expectedMaximum) {
          flush();
          segmentStart.current = current;
        }
      }
      lastObserved.current = current;
      onTick(current, duration);
    }, 1000);
    const save = window.setInterval(() => playing.current && flush(), 12000);
    const saveBeforeLeaving = () => flush();
    window.addEventListener("pagehide", saveBeforeLeaving);
    document.addEventListener("visibilitychange", saveBeforeLeaving);

    return () => {
      stopped = true;
      flush();
      window.clearInterval(tick);
      window.clearInterval(save);
      window.removeEventListener("pagehide", saveBeforeLeaving);
      document.removeEventListener("visibilitychange", saveBeforeLeaving);
      player.current?.destroy();
      player.current = null;
    };
    // Player lifetime should change only when the selected video changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, videoId]);

  return (
    <div className="aspect-video overflow-hidden rounded-2xl bg-black shadow-2xl">
      <div id={id} className="h-full w-full" />
    </div>
  );
});
