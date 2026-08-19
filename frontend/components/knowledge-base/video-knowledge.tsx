"use client";

import { Clock3, Library, Plus, StickyNote } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import {
  YouTubePlayer,
  type YouTubePlayerHandle,
} from "@/components/study-workspace/youtube-player";
import { api } from "@/lib/api";
import type { StudyNote, StudyProgress, StudyWorkspaceData } from "@/lib/types";

function time(value: number) {
  const minutes = Math.floor(value / 60),
    seconds = Math.floor(value % 60);
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

export function VideoKnowledge() {
  const [data, setData] = useState<StudyWorkspaceData | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [current, setCurrent] = useState(0);
  const [draft, setDraft] = useState("");
  const player = useRef<YouTubePlayerHandle>(null);
  const load = useCallback(async (resourceId?: string | null) => {
    const workspace = await api<StudyWorkspaceData>(
      `/study-workspace/${resourceId ? `?resource_id=${resourceId}` : ""}`,
    );
    setData(workspace);
    setSelectedId(workspace.current_resource_id);
  }, []);
  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);
  const selected =
    data?.resources.find((item) => item.id === selectedId) ?? null;

  async function select(id: string) {
    player.current?.flush();
    await load(id);
    setCurrent(0);
  }
  const watched = useCallback(
    async (
      start: number,
      end: number,
      position: number,
      total: number,
      speed: number,
    ) => {
      if (!selectedId) return;
      const progress = await api<StudyProgress>(
        `/study-resources/${selectedId}/progress/`,
        {
          method: "PATCH",
          body: JSON.stringify({
            current_position: Math.floor(position),
            duration_seconds: Math.floor(total),
            playback_speed: speed,
            interval_start: Math.floor(start),
            interval_end: Math.floor(end),
            client_event_id: crypto.randomUUID(),
          }),
        },
      );
      setData(
        (old) =>
          old && {
            ...old,
            resources: old.resources.map((item) =>
              item.id === selectedId ? { ...item, progress } : item,
            ),
          },
      );
    },
    [selectedId],
  );
  async function addNote() {
    if (!selected || !draft.trim()) return;
    const note = await api<StudyNote>(
      `/study-resources/${selected.id}/notes/`,
      {
        method: "POST",
        body: JSON.stringify({
          timestamp_seconds: Math.floor(current),
          content: draft,
        }),
      },
    );
    setData((old) => old && { ...old, notes: [note, ...old.notes] });
    setDraft("");
  }
  return (
    <div className="grid min-h-[680px] overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 xl:grid-cols-[240px_minmax(0,1fr)_320px]">
      <aside className="border-r border-slate-200 p-3 dark:border-slate-800">
        <p className="flex items-center gap-2 px-2 text-xs font-black">
          <Library size={15} /> Saved videos
        </p>
        <div className="mt-3 space-y-1">
          {data?.resources.map((item) => (
            <button
              key={item.id}
              onClick={() => void select(item.id)}
              className={`w-full rounded-xl p-2 text-left ${item.id === selectedId ? "bg-indigo-50 dark:bg-indigo-950/40" : "hover:bg-slate-50 dark:hover:bg-slate-800"}`}
            >
              <p className="line-clamp-2 text-xs font-bold">{item.title}</p>
              <p className="mt-1 text-[9px] text-slate-400">
                {item.channel_name || "YouTube"} ·{" "}
                {item.progress?.completion_percentage ?? "0"}%
              </p>
            </button>
          ))}
        </div>
        <Link
          href="/study"
          className="mt-4 flex items-center justify-center gap-1.5 rounded-xl border border-slate-200 py-2 text-[10px] font-bold text-indigo-600 dark:border-slate-700"
        >
          <Plus size={13} /> Add video in Study
        </Link>
      </aside>
      <main className="min-w-0 bg-slate-50 p-4 dark:bg-slate-950">
        {selected ? (
          <>
            <YouTubePlayer
              key={selected.id}
              ref={player}
              videoId={selected.youtube_video_id}
              resumeAt={selected.progress?.last_position_seconds ?? 0}
              onTick={setCurrent}
              onWatched={watched}
            />
            <h2 className="mt-4 text-lg font-black">{selected.title}</h2>
            <p className="mt-1 text-xs text-slate-500">
              {selected.channel_name} · Current position {time(current)}
            </p>
          </>
        ) : (
          <div className="grid h-full place-items-center text-center">
            <p className="text-sm text-slate-400">
              Add a YouTube lesson in the Study Workspace.
            </p>
          </div>
        )}
      </main>
      <aside className="border-l border-slate-200 p-4 dark:border-slate-800">
        <p className="flex items-center gap-2 text-xs font-black">
          <StickyNote size={15} /> Timestamped notes
        </p>
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Capture what you learned…"
          className="mt-3 min-h-24 w-full rounded-xl border border-slate-200 bg-transparent p-3 text-xs outline-none dark:border-slate-700"
        />
        <button
          onClick={() => void addNote()}
          disabled={!draft.trim() || !selected}
          className="mt-2 flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 py-2.5 text-xs font-bold text-white disabled:opacity-40"
        >
          <Clock3 size={14} /> Save at {time(current)}
        </button>
        <div className="mt-4 space-y-2">
          {data?.notes.map((note) => (
            <button
              key={note.id}
              onClick={() => player.current?.seekTo(note.timestamp_seconds)}
              className="w-full rounded-xl border border-slate-200 p-3 text-left dark:border-slate-700"
            >
              <span className="text-[9px] font-black text-indigo-600">
                ▶ {time(note.timestamp_seconds)}
              </span>
              <p className="mt-1 line-clamp-3 text-[10px] leading-4 text-slate-500">
                {note.content}
              </p>
            </button>
          ))}
        </div>
      </aside>
    </div>
  );
}
