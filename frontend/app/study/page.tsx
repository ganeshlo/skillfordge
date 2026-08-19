"use client";
/* eslint-disable @next/next/no-img-element */

import {
  Bookmark,
  CheckCircle2,
  Clock3,
  Download,
  Expand,
  Flame,
  FileText,
  GripVertical,
  Library,
  LoaderCircle,
  Maximize2,
  Minimize2,
  Moon,
  Pause,
  Pencil,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Pin,
  Play,
  Plus,
  Search,
  Square,
  Star,
  Sparkles,
  StickyNote,
  Sun,
  Trash2,
  Upload,
  Video,
  X,
} from "lucide-react";
import { FormEvent, PointerEvent as ReactPointerEvent, useCallback, useEffect, useRef, useState } from "react";
import type { CSSProperties } from "react";

import { StudyAppLayout } from "@/components/study-workspace/app-layout";
import {
  YouTubePlayer,
  type YouTubePlayerHandle,
} from "@/components/study-workspace/youtube-player";
import { api, apiBlob } from "@/lib/api";
import type {
  StudyBookmark,
  StudyNote,
  StudyProgress,
  StudyResource,
  StudySession,
  StudyWorkspaceData,
  User,
} from "@/lib/types";

type PanelTab = "notes" | "bookmarks" | "activity" | "session";
type MaximizedPanel = "library" | "video" | "tools" | null;

function formatTime(value: number) {
  const seconds = Math.max(0, Math.floor(value));
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const rest = seconds % 60;
  return hours
    ? `${hours}:${String(minutes).padStart(2, "0")}:${String(rest).padStart(2, "0")}`
    : `${minutes}:${String(rest).padStart(2, "0")}`;
}

function parseTime(value: string) {
  const parts = value.trim().split(":").map(Number);
  if (!parts.length || parts.some((part) => !Number.isFinite(part) || part < 0)) return null;
  if (parts.length === 1) return Math.floor(parts[0]);
  if (parts.length === 2 && parts[1] < 60) return Math.floor(parts[0] * 60 + parts[1]);
  if (parts.length === 3 && parts[1] < 60 && parts[2] < 60) return Math.floor(parts[0] * 3600 + parts[1] * 60 + parts[2]);
  return null;
}

function NotePreview({ content }: { content: string }) {
  return <div className="mt-3 space-y-2 text-xs leading-5 text-slate-700 dark:text-slate-200">{content.split("\n").map((raw, index) => {
    const line = raw.trim();
    if (!line) return <div key={index} className="h-1" />;
    if (line.startsWith("### ")) return <h5 key={index} className="pt-1 text-sm font-black">{line.slice(4)}</h5>;
    if (line.startsWith("## ")) return <h4 key={index} className="pt-2 text-base font-black text-indigo-700 dark:text-indigo-300">{line.slice(3)}</h4>;
    if (line.startsWith("# ")) return <h3 key={index} className="text-lg font-black tracking-tight">{line.slice(2)}</h3>;
    if (line.startsWith("- ") || line.startsWith("* ")) return <p key={index} className="pl-4 before:-ml-4 before:mr-2 before:text-indigo-500 before:content-['•']">{line.slice(2)}</p>;
    return <p key={index}>{line}</p>;
  })}</div>;
}

export default function StudyPage() {
  const [user, setUser] = useState<User | null>(null);
  const [data, setData] = useState<StudyWorkspaceData | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [adding, setAdding] = useState(false);
  const [search, setSearch] = useState("");
  const [noteSearch, setNoteSearch] = useState("");
  const [tab, setTab] = useState<PanelTab>("notes");
  const [currentTime, setCurrentTime] = useState(0);
  const [dark, setDark] = useState(() =>
    typeof document !== "undefined" && document.documentElement.classList.contains("dark")
  );
  const [focused, setFocused] = useState(false);
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const [leftWidth, setLeftWidth] = useState(280);
  const [rightWidth, setRightWidth] = useState(380);
  const [maximizedPanel, setMaximizedPanel] = useState<MaximizedPanel>(null);
  const [draft, setDraft] = useState("");
  const [sessionGoal, setSessionGoal] = useState("");
  const [aiOpen, setAiOpen] = useState(false);
  const [aiMode, setAiMode] = useState<"full" | "range">("full");
  const [rangeStart, setRangeStart] = useState("0:00");
  const [rangeEnd, setRangeEnd] = useState("5:00");
  const [transcriptText, setTranscriptText] = useState("");
  const [transcriptFormat, setTranscriptFormat] = useState<"auto" | "plain" | "srt" | "vtt">("auto");
  const [aiBusy, setAiBusy] = useState(false);
  const [transcriptBusy, setTranscriptBusy] = useState(false);
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null);
  const [clock, setClock] = useState(Date.now());
  const playerRef = useRef<YouTubePlayerHandle>(null);
  const gridRef = useRef<HTMLDivElement>(null);
  const leftWidthBeforeMax = useRef(280);
  const rightWidthBeforeMax = useRef(380);
  const collapsedBeforeVideoMax = useRef({ left: false, right: false });
  const noteTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  const load = useCallback(async (resourceId?: string | null) => {
    const workspace = await api<StudyWorkspaceData>(
      `/study-workspace/${resourceId ? `?resource_id=${resourceId}` : ""}`,
    );
    setData(workspace);
    setSelectedId(workspace.current_resource_id);
    setDraft(workspace.current_resource_id
      ? localStorage.getItem(`study-note-draft:${workspace.current_resource_id}`) ?? ""
      : "");
    return workspace;
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void Promise.all([api<User>("/me/"), load()])
        .then(([me]) => setUser(me))
        .catch((reason: Error) => setError(reason.message))
        .finally(() => setLoading(false));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  useEffect(() => {
    const timer = window.setInterval(() => setClock(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (selectedId) localStorage.setItem(`study-note-draft:${selectedId}`, draft);
  }, [draft, selectedId]);

  useEffect(() => {
    const item = data?.active_session;
    if (!item || item.status === "ended") return;
    const heartbeat = window.setInterval(() => {
      void api<StudySession>(`/study-sessions/${item.id}/heartbeat/`, {
        method: "PATCH",
        body: JSON.stringify({}),
      }).then((session) => setData((old) => old && ({ ...old, active_session: session })));
    }, 15000);
    return () => window.clearInterval(heartbeat);
  }, [data?.active_session]);

  useEffect(() => {
    const session = data?.active_session;
    if (!session || session.status !== "active") return;
    let idleTimer: ReturnType<typeof setTimeout>;
    const reset = () => {
      clearTimeout(idleTimer);
      idleTimer = setTimeout(() => {
        void sessionAction("pause", { idle: true });
      }, 5 * 60 * 1000);
    };
    const events = ["mousemove", "keydown", "pointerdown", "touchstart"];
    events.forEach((event) => window.addEventListener(event, reset, { passive: true }));
    reset();
    return () => {
      clearTimeout(idleTimer);
      events.forEach((event) => window.removeEventListener(event, reset));
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data?.active_session?.id, data?.active_session?.status]);

  useEffect(() => () => {
    Object.values(noteTimers.current).forEach(clearTimeout);
  }, []);

  const selected = data?.resources.find((item) => item.id === selectedId) ?? null;

  async function selectVideo(id: string) {
    if (id === selectedId) return;
    playerRef.current?.flush();
    setLoading(true);
    setError("");
    try {
      await load(id);
      setCurrentTime(0);
      setAiOpen(false);
      setRangeStart("0:00");
      setRangeEnd("5:00");
      setTab("notes");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load video.");
    } finally {
      setLoading(false);
    }
  }

  async function addVideo(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setError("");
    try {
      const created = await api<StudyResource>("/study-resources/", {
        method: "POST",
        body: JSON.stringify({
          title: form.get("title"),
          external_url: form.get("url"),
          channel_name: form.get("channel"),
        }),
      });
      event.currentTarget.reset();
      setAdding(false);
      await load(created.id);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not add video.");
    }
  }

  async function deleteVideo(item: StudyResource) {
    if (!window.confirm(`Remove “${item.title}” and its private notes and progress?`)) return;
    await api(`/study-resources/${item.id}/`, { method: "DELETE" });
    await load(item.id === selectedId ? null : selectedId);
  }

  const onTick = useCallback((position: number) => {
    setCurrentTime(position);
  }, []);

  const onWatched = useCallback(async (
    start: number,
    end: number,
    position: number,
    total: number,
    speed: number,
  ) => {
    if (!selectedId) return;
    try {
      const progress = await api<StudyProgress>(`/study-resources/${selectedId}/progress/`, {
        method: "PATCH",
        keepalive: true,
        body: JSON.stringify({
          current_position: Math.floor(position),
          duration_seconds: Math.floor(total),
          playback_speed: speed,
          interval_start: Math.floor(start),
          interval_end: Math.floor(end),
          client_event_id: crypto.randomUUID(),
        }),
      });
      setData((old) => old && ({
        ...old,
        resources: old.resources.map((item) => item.id === selectedId
          ? { ...item, duration_seconds: Math.floor(total), progress }
          : item),
      }));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Progress could not be saved.");
    }
  }, [selectedId]);

  async function createNote() {
    if (!selected || !draft.trim()) return;
    const note = await api<StudyNote>(`/study-resources/${selected.id}/notes/`, {
      method: "POST",
      body: JSON.stringify({ timestamp_seconds: Math.floor(currentTime), content: draft }),
    });
    setData((old) => old && ({
      ...old,
      notes: [note, ...old.notes],
      today_activity: { ...old.today_activity, notes_created: old.today_activity.notes_created + 1 },
    }));
    setDraft("");
    localStorage.removeItem(`study-note-draft:${selected.id}`);
  }

  function updateNoteLocal(note: StudyNote, changes: Partial<StudyNote>) {
    const updated = { ...note, ...changes };
    setData((old) => old && ({
      ...old,
      notes: old.notes.map((item) => item.id === note.id ? updated : item),
    }));
    clearTimeout(noteTimers.current[note.id]);
    noteTimers.current[note.id] = setTimeout(() => {
      void api<StudyNote>(`/study-notes/${note.id}/`, {
        method: "PATCH",
        body: JSON.stringify(changes),
      }).catch((reason: Error) => setError(reason.message));
    }, 900);
  }

  async function deleteNote(id: string) {
    await api(`/study-notes/${id}/`, { method: "DELETE" });
    setData((old) => old && ({ ...old, notes: old.notes.filter((item) => item.id !== id) }));
  }

  async function importTranscript() {
    if (!selected || !transcriptText.trim()) return;
    setTranscriptBusy(true); setError("");
    try {
      const transcript = await api<{ language: string; has_timestamps: boolean }>(`/study-resources/${selected.id}/transcript/`, {
        method: "PUT",
        body: JSON.stringify({ content: transcriptText, content_format: transcriptFormat, language: "en" }),
      });
      setData((old) => old && ({
        ...old,
        resources: old.resources.map((item) => item.id === selected.id ? {
          ...item, transcript: { available: true, has_timestamps: transcript.has_timestamps, language: transcript.language },
        } : item),
      }));
      setTranscriptText("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not import transcript.");
    } finally { setTranscriptBusy(false); }
  }

  async function generateAiNote() {
    if (!selected) return;
    const start = aiMode === "range" ? parseTime(rangeStart) : 0;
    const end = aiMode === "range" ? parseTime(rangeEnd) : null;
    if (start === null || (aiMode === "range" && (end === null || end <= start))) {
      setError("Use a valid timestamp range such as 2:30 to 7:00."); return;
    }
    setAiBusy(true); setError("");
    try {
      const note = await api<StudyNote>(`/study-resources/${selected.id}/ai-notes/`, {
        method: "POST",
        body: JSON.stringify({ mode: aiMode, start_seconds: start, end_seconds: end }),
      });
      setData((old) => old && ({
        ...old, notes: [note, ...old.notes],
        today_activity: { ...old.today_activity, notes_created: old.today_activity.notes_created + 1 },
      }));
      setAiOpen(false);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "AI notes could not be generated.");
    } finally { setAiBusy(false); }
  }

  async function downloadNote(note: StudyNote) {
    try {
      const blob = await apiBlob(`/study-notes/${note.id}/pdf/`);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${selected?.title || "learnos-notes"}.pdf`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "PDF could not be downloaded.");
    }
  }

  async function createBookmark() {
    if (!selected) return;
    const item = await api<StudyBookmark>(`/study-resources/${selected.id}/bookmarks/`, {
      method: "POST",
      body: JSON.stringify({
        timestamp_seconds: Math.floor(currentTime),
        label: `Bookmark at ${formatTime(currentTime)}`,
        bookmark_type: "important",
      }),
    });
    setData((old) => old && ({
      ...old,
      bookmarks: [...old.bookmarks, item],
      today_activity: { ...old.today_activity, bookmarks_created: old.today_activity.bookmarks_created + 1 },
    }));
    setTab("bookmarks");
  }

  async function updateBookmark(item: StudyBookmark, changes: Partial<StudyBookmark>) {
    const saved = await api<StudyBookmark>(`/study-bookmarks/${item.id}/`, {
      method: "PATCH",
      body: JSON.stringify(changes),
    });
    setData((old) => old && ({
      ...old,
      bookmarks: old.bookmarks.map((bookmark) => bookmark.id === saved.id ? saved : bookmark),
    }));
  }

  async function deleteBookmark(id: string) {
    await api(`/study-bookmarks/${id}/`, { method: "DELETE" });
    setData((old) => old && ({ ...old, bookmarks: old.bookmarks.filter((item) => item.id !== id) }));
  }

  async function startSession() {
    const session = await api<StudySession>("/study-sessions/start/", {
      method: "POST",
      body: JSON.stringify({ resource_id: selectedId, session_goal: sessionGoal }),
    });
    setData((old) => old && ({ ...old, active_session: session }));
  }

  async function sessionAction(action: "pause" | "resume" | "heartbeat" | "end", body = {}) {
    const session = data?.active_session;
    if (!session) return;
    const saved = await api<StudySession>(`/study-sessions/${session.id}/${action}/`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
    if (action === "end") {
      await load(selectedId);
      return;
    }
    setData((old) => old && ({
      ...old,
      active_session: saved,
    }));
  }

  async function toggleTheme() {
    const value = !dark;
    setDark(value);
    const theme = value ? "dark" : "light";
    localStorage.setItem("learnos-theme", theme);
    document.documentElement.classList.toggle("dark", value);
    document.documentElement.style.colorScheme = theme;
    window.dispatchEvent(new CustomEvent("learnos-theme-change", { detail: theme }));
    try { await api("/me/", { method: "PATCH", body: JSON.stringify({ theme }) }); } catch { /* local theme remains available */ }
  }

  function startResize(side: "left" | "right", event: ReactPointerEvent<HTMLDivElement>) {
    event.preventDefault();
    const bounds = gridRef.current?.getBoundingClientRect();
    if (!bounds) return;
    const move = (pointer: PointerEvent) => {
      if (side === "left") {
        setLeftWidth(Math.min(440, Math.max(220, pointer.clientX - bounds.left)));
      } else {
        setRightWidth(Math.min(560, Math.max(300, bounds.right - pointer.clientX)));
      }
    };
    const stop = () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", stop);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", stop);
  }

  function maximizeVideo() {
    collapsedBeforeVideoMax.current = { left: leftCollapsed, right: rightCollapsed };
    setMaximizedPanel("video");
    setFocused(false);
    setLeftCollapsed(true);
    setRightCollapsed(true);
  }

  function restorePanels() {
    if (maximizedPanel === "library") setLeftWidth(leftWidthBeforeMax.current);
    if (maximizedPanel === "tools") setRightWidth(rightWidthBeforeMax.current);
    if (maximizedPanel === "video") {
      setLeftCollapsed(collapsedBeforeVideoMax.current.left);
      setRightCollapsed(collapsedBeforeVideoMax.current.right);
    }
    setMaximizedPanel(null);
    setFocused(false);
  }

  function maximizeSidePanel(panel: "library" | "tools") {
    if (maximizedPanel === "library" && panel !== "library") {
      setLeftWidth(leftWidthBeforeMax.current);
    }
    if (maximizedPanel === "tools" && panel !== "tools") {
      setRightWidth(rightWidthBeforeMax.current);
    }
    if (maximizedPanel === "video") {
      setLeftCollapsed(collapsedBeforeVideoMax.current.left);
      setRightCollapsed(collapsedBeforeVideoMax.current.right);
    }
    setFocused(false);
    setMaximizedPanel(panel);
    if (panel === "library") {
      leftWidthBeforeMax.current = leftWidth;
      setLeftCollapsed(false);
      setLeftWidth(440);
    } else {
      rightWidthBeforeMax.current = rightWidth;
      setRightCollapsed(false);
      setRightWidth(560);
    }
  }

  const gridStyle = {
    "--study-left": `${leftCollapsed ? 52 : leftWidth}px`,
    "--study-right": `${rightCollapsed ? 52 : rightWidth}px`,
  } as CSSProperties;

  const filteredVideos = data?.resources.filter((item) =>
    `${item.title} ${item.channel_name}`.toLowerCase().includes(search.toLowerCase()),
  ) ?? [];
  const filteredNotes = data?.notes.filter((item) =>
    item.content.toLowerCase().includes(noteSearch.toLowerCase()),
  ) ?? [];
  const session = data?.active_session;
  const sessionSeconds = session
    ? session.active_seconds + (session.status === "active"
      ? Math.max(0, Math.floor((clock - new Date(session.last_transition_at).getTime()) / 1000))
      : 0)
    : 0;

  return (
    <StudyAppLayout user={user} focused={focused}>
      <div className={dark ? "dark min-h-screen bg-slate-950 text-slate-100" : "min-h-screen bg-slate-100 text-slate-900"}>
        <div className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-4 dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center gap-3">
            <span className="grid size-9 place-items-center rounded-xl bg-indigo-600 text-white"><Video size={18} /></span>
            <div><h1 className="text-sm font-black">Study Workspace</h1><p className="text-[10px] text-slate-500">Private, focused learning</p></div>
          </div>
          <div className="flex items-center gap-2">
            {session && <span className="hidden rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700 sm:block">{session.status === "active" ? "● Studying" : "Paused"} · {formatTime(sessionSeconds)}</span>}
            <button onClick={() => void toggleTheme()} className="rounded-lg border border-slate-200 p-2 dark:border-slate-700" aria-label="Toggle dark mode">{dark ? <Sun size={16} /> : <Moon size={16} />}</button>
            <button onClick={() => maximizedPanel === "video" ? restorePanels() : maximizeVideo()} className="rounded-lg border border-slate-200 p-2 dark:border-slate-700" aria-label={maximizedPanel === "video" ? "Restore all panels" : "Open distraction-free video mode"}>{maximizedPanel === "video" ? <Minimize2 size={16} /> : <Expand size={16} />}</button>
          </div>
        </div>

        {error && <div role="alert" className="mx-4 mt-3 flex items-center justify-between rounded-xl bg-rose-50 px-4 py-2 text-xs font-semibold text-rose-700"><span>{error}</span><button onClick={() => setError("")}><X size={15} /></button></div>}

        <div ref={gridRef} style={gridStyle} className="study-workspace-grid min-h-[calc(100vh-3.5rem)]">
          <aside className="relative border-r border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            {leftCollapsed ? <button onClick={() => setLeftCollapsed(false)} className="mx-auto grid size-9 place-items-center rounded-xl text-indigo-600 hover:bg-indigo-50" aria-label="Expand video library"><PanelLeftOpen size={18} /></button> : <>
            <div className="flex items-center justify-between"><div><p className="text-xs font-black uppercase tracking-wider text-slate-500">Video library</p><p className="mt-1 text-xs text-slate-400">{data?.resources.length ?? 0} saved videos</p></div><div className="flex items-center gap-1"><button onClick={() => maximizedPanel === "library" ? restorePanels() : maximizeSidePanel("library")} className="grid size-8 place-items-center rounded-lg text-slate-400 hover:bg-slate-100" aria-label={maximizedPanel === "library" ? "Restore all panels" : "Maximize video library"} title={maximizedPanel === "library" ? "Restore" : "Maximize"}>{maximizedPanel === "library" ? <Minimize2 size={15} /> : <Maximize2 size={15} />}</button>{maximizedPanel !== "library" && <button onClick={() => setLeftCollapsed(true)} className="grid size-8 place-items-center rounded-lg text-slate-400 hover:bg-slate-100" aria-label="Minimize video library"><PanelLeftClose size={17} /></button>}<button onClick={() => setAdding(true)} className="grid size-9 place-items-center rounded-xl bg-indigo-600 text-white" aria-label="Add video"><Plus size={17} /></button></div></div>
            <label className="mt-4 flex items-center gap-2 rounded-xl border border-slate-200 px-3 dark:border-slate-700"><Search size={15} className="text-slate-400" /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search videos" className="w-full bg-transparent py-2.5 text-xs outline-none" /></label>
            <div className="mt-4 max-h-[calc(100vh-10rem)] space-y-2 overflow-y-auto pr-1">
              {filteredVideos.map((item) => <button key={item.id} onClick={() => void selectVideo(item.id)} className={`group w-full rounded-xl border p-2 text-left ${item.id === selectedId ? "border-indigo-400 bg-indigo-50 dark:bg-indigo-950/40" : "border-transparent hover:bg-slate-50 dark:hover:bg-slate-800"}`}>
                <div className="relative overflow-hidden rounded-lg bg-slate-200"><img src={`https://i.ytimg.com/vi/${item.youtube_video_id}/mqdefault.jpg`} alt="" className="aspect-video w-full object-cover" /><span className="absolute bottom-1 right-1 rounded bg-black/80 px-1.5 py-0.5 text-[9px] text-white">{formatTime(item.duration_seconds)}</span></div>
                <div className="mt-2 flex gap-2"><div className="min-w-0 flex-1"><p className="truncate text-xs font-bold">{item.title}</p><p className="truncate text-[10px] text-slate-500">{item.channel_name || "YouTube"}</p></div><span onClick={(event) => { event.stopPropagation(); void deleteVideo(item); }} className="invisible grid size-6 place-items-center rounded text-slate-400 hover:bg-rose-50 hover:text-rose-600 group-hover:visible"><Trash2 size={13} /></span></div>
                <div className="mt-2 h-1 overflow-hidden rounded-full bg-slate-200"><div className="h-full bg-indigo-600" style={{ width: `${item.progress?.completion_percentage ?? 0}%` }} /></div>
              </button>)}
              {!filteredVideos.length && !loading && <div className="rounded-xl border border-dashed border-slate-300 p-6 text-center text-xs text-slate-500">No saved videos yet.</div>}
            </div>
            </>}
            {!leftCollapsed && maximizedPanel === null && <div onPointerDown={(event) => startResize("left", event)} className="absolute -right-1 top-0 z-20 hidden h-full w-2 cursor-col-resize items-center justify-center hover:bg-indigo-100/60 xl:flex" title="Drag to resize video library"><GripVertical size={12} className="text-slate-300" /></div>}
          </aside>

          <main className="relative min-w-0 p-4 sm:p-6">
            <div className="mb-2 flex justify-end"><button onClick={() => maximizedPanel === "video" ? restorePanels() : maximizeVideo()} className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-[10px] font-bold text-slate-500 hover:border-indigo-300 dark:border-slate-700 dark:bg-slate-900" aria-label={maximizedPanel === "video" ? "Restore panels" : "Maximize video area"}>{maximizedPanel === "video" ? <Minimize2 size={13} /> : <Maximize2 size={13} />}{maximizedPanel === "video" ? "Restore" : "Maximize"}</button></div>
            {loading && !data ? <div className="grid min-h-96 place-items-center"><LoaderCircle className="animate-spin text-indigo-600" /></div> : selected ? <div className="mx-auto max-w-5xl">
              <YouTubePlayer key={selected.id} ref={playerRef} videoId={selected.youtube_video_id} resumeAt={selected.progress?.last_position_seconds ?? 0} onTick={onTick} onWatched={onWatched} />
              <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-lg font-black">{selected.title}</h2><p className="mt-1 text-xs text-slate-500">{selected.channel_name || "YouTube"} · resumed at {formatTime(selected.progress?.last_position_seconds ?? 0)}</p></div><button onClick={() => void createBookmark()} className="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-xs font-bold hover:border-indigo-300 dark:border-slate-700"><Bookmark size={15} /> Bookmark {formatTime(currentTime)}</button></div>
                <div className="mt-4 flex items-center gap-3"><div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700"><div className="h-full rounded-full bg-gradient-to-r from-indigo-600 to-blue-600" style={{ width: `${selected.progress?.completion_percentage ?? 0}%` }} /></div><span className="text-xs font-bold">{selected.progress?.completion_percentage ?? "0.00"}% unique</span></div>
              </div>
            </div> : <div className="grid min-h-[65vh] place-items-center"><div className="max-w-sm text-center"><span className="mx-auto grid size-16 place-items-center rounded-2xl bg-indigo-100 text-indigo-600"><Library size={28} /></span><h2 className="mt-5 text-2xl font-black">Build your video library</h2><p className="mt-2 text-sm leading-6 text-slate-500">Add a YouTube lesson to watch, take timestamped notes, and track real learning progress.</p><button onClick={() => setAdding(true)} className="mt-5 rounded-xl bg-indigo-600 px-5 py-3 text-sm font-bold text-white">Add your first video</button></div></div>}
          </main>

          <aside className="relative border-l border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
            {rightCollapsed ? <button onClick={() => setRightCollapsed(false)} className="mx-auto mt-4 grid size-9 place-items-center rounded-xl text-indigo-600 hover:bg-indigo-50" aria-label="Expand study tools"><PanelRightOpen size={18} /></button> : <>
            <div className="flex items-center border-b border-slate-200 dark:border-slate-800"><div className="grid flex-1 grid-cols-4">{([['notes', StickyNote, 'Notes'], ['bookmarks', Bookmark, 'Marks'], ['activity', Flame, 'Today'], ['session', Clock3, 'Session']] as const).map(([value, Icon, label]) => <button key={value} onClick={() => setTab(value)} className={`flex flex-col items-center gap-1 border-b-2 px-1 py-3 text-[10px] font-bold ${tab === value ? "border-indigo-600 text-indigo-600" : "border-transparent text-slate-500"}`}><Icon size={16} />{label}</button>)}</div><button onClick={() => maximizedPanel === "tools" ? restorePanels() : maximizeSidePanel("tools")} className="grid size-8 place-items-center rounded-lg text-slate-400 hover:bg-slate-100" aria-label={maximizedPanel === "tools" ? "Restore all panels" : "Maximize study tools"} title={maximizedPanel === "tools" ? "Restore" : "Maximize"}>{maximizedPanel === "tools" ? <Minimize2 size={15} /> : <Maximize2 size={15} />}</button>{maximizedPanel !== "tools" && <button onClick={() => setRightCollapsed(true)} className="mr-2 grid size-8 place-items-center rounded-lg text-slate-400 hover:bg-slate-100" aria-label="Minimize study tools"><PanelRightClose size={17} /></button>}</div>
            <div className="max-h-[calc(100vh-7rem)] overflow-y-auto p-4">
              {tab === "notes" && <div>
                <div className="flex items-center justify-between gap-2"><div><h3 className="text-sm font-black">Timestamped notes</h3><p className="mt-0.5 text-[10px] text-slate-400">Personal and AI-generated learning notes</p></div><button onClick={() => setAiOpen((value) => !value)} disabled={!selected} className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-violet-600 to-indigo-600 px-3 py-2 text-[10px] font-black text-white disabled:opacity-40"><Sparkles size={13} /> AI notes</button></div>
                {aiOpen && selected && <section className="mt-4 rounded-2xl border border-violet-200 bg-gradient-to-br from-violet-50 to-indigo-50 p-4 dark:border-violet-900 dark:from-violet-950/40 dark:to-indigo-950/30">
                  <div className="flex items-start gap-3"><span className="grid size-9 shrink-0 place-items-center rounded-xl bg-violet-600 text-white"><Sparkles size={17} /></span><div className="min-w-0"><h4 className="text-xs font-black">AI note generator</h4><p className="mt-1 text-[10px] leading-4 text-slate-500 dark:text-slate-400">Generate structured Markdown notes from the currently open video. AI notes remain editable.</p><a href={selected.external_url} target="_blank" rel="noreferrer" className="mt-1 block truncate text-[9px] font-bold text-violet-600 dark:text-violet-300" title={selected.external_url}>Using: {selected.title}</a></div></div>
                  {!selected.transcript.available ? <div className="mt-4">
                    <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-[10px] leading-4 text-amber-800 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-300"><strong>Transcript needed.</strong> YouTube does not let LearnOS download arbitrary captions. Paste plain text for full notes, or SRT/VTT for timestamp-range notes.</div>
                    <div className="mt-3 flex gap-2"><select value={transcriptFormat} onChange={(event) => setTranscriptFormat(event.target.value as typeof transcriptFormat)} className="rounded-lg border border-violet-200 bg-white px-2 py-2 text-[10px] dark:border-violet-800 dark:bg-slate-900"><option value="auto">Auto-detect</option><option value="plain">Plain text</option><option value="srt">SRT captions</option><option value="vtt">WebVTT captions</option></select></div>
                    <textarea value={transcriptText} onChange={(event) => setTranscriptText(event.target.value)} placeholder="Paste the video transcript, SRT, or VTT captions here…" className="mt-2 min-h-32 w-full resize-y rounded-xl border border-violet-200 bg-white p-3 text-xs outline-none focus:border-violet-500 dark:border-violet-800 dark:bg-slate-900" />
                    <button onClick={() => void importTranscript()} disabled={transcriptBusy || !transcriptText.trim()} className="mt-2 flex w-full items-center justify-center gap-2 rounded-xl border border-violet-300 bg-white py-2.5 text-xs font-bold text-violet-700 disabled:opacity-40 dark:border-violet-800 dark:bg-slate-900 dark:text-violet-300">{transcriptBusy ? <LoaderCircle size={14} className="animate-spin" /> : <Upload size={14} />} Import transcript</button>
                  </div> : <div className="mt-4">
                    <div className="flex items-center justify-between rounded-xl bg-white/80 px-3 py-2 text-[10px] dark:bg-slate-900/70"><span className="flex items-center gap-1.5 font-bold text-emerald-700 dark:text-emerald-400"><FileText size={13} /> Transcript ready</span><span className="text-slate-400">{selected.transcript.has_timestamps ? "Timestamped" : "Plain text"}</span></div>
                    <div className="mt-3 grid grid-cols-2 gap-2"><button onClick={() => setAiMode("full")} className={`rounded-xl border px-3 py-2 text-[10px] font-black ${aiMode === "full" ? "border-violet-500 bg-violet-600 text-white" : "border-violet-200 bg-white text-slate-600 dark:border-violet-800 dark:bg-slate-900 dark:text-slate-300"}`}>Full video</button><button onClick={() => setAiMode("range")} disabled={!selected.transcript.has_timestamps} className={`rounded-xl border px-3 py-2 text-[10px] font-black disabled:cursor-not-allowed disabled:opacity-40 ${aiMode === "range" ? "border-violet-500 bg-violet-600 text-white" : "border-violet-200 bg-white text-slate-600 dark:border-violet-800 dark:bg-slate-900 dark:text-slate-300"}`}>Timestamp range</button></div>
                    {aiMode === "range" && <div className="mt-3"><div className="grid grid-cols-2 gap-2"><label className="text-[10px] font-bold">From<input value={rangeStart} onChange={(event) => setRangeStart(event.target.value)} placeholder="0:00" className="mt-1 w-full rounded-lg border border-violet-200 bg-white p-2 text-xs font-normal outline-none dark:border-violet-800 dark:bg-slate-900" /></label><label className="text-[10px] font-bold">To<input value={rangeEnd} onChange={(event) => setRangeEnd(event.target.value)} placeholder="5:00" className="mt-1 w-full rounded-lg border border-violet-200 bg-white p-2 text-xs font-normal outline-none dark:border-violet-800 dark:bg-slate-900" /></label></div><button onClick={() => { const start = Math.floor(currentTime); const end = selected.duration_seconds ? Math.min(selected.duration_seconds, start + 300) : start + 300; setRangeStart(formatTime(start)); setRangeEnd(formatTime(end)); }} className="mt-2 text-[10px] font-bold text-violet-700 dark:text-violet-300">Use current time + 5 minutes</button></div>}
                    {!data?.ai_notes_available && <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-2 text-[10px] leading-4 text-amber-800 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-300"><strong>AI service is not connected.</strong> The open video is selected correctly, but an administrator must connect an OpenAI API key or a local AI provider before notes can be generated.</p>}
                    <button onClick={() => void generateAiNote()} disabled={aiBusy || !data?.ai_notes_available} className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 py-3 text-xs font-black text-white shadow-lg shadow-violet-200/50 disabled:opacity-50 dark:shadow-none">{aiBusy ? <LoaderCircle size={15} className="animate-spin" /> : <Sparkles size={15} />} {aiBusy ? "Creating clean notes…" : "Generate notes"}</button>
                    <p className="mt-2 text-center text-[9px] leading-4 text-slate-400">AI can make mistakes. Review generated notes against the video.</p>
                  </div>}
                </section>}
                <textarea value={draft} onChange={(event) => setDraft(event.target.value)} disabled={!selected} placeholder={selected ? "Write what you learned…" : "Select a video first"} className="mt-3 min-h-28 w-full resize-y rounded-xl border border-slate-200 bg-transparent p-3 text-sm outline-none focus:border-indigo-400 dark:border-slate-700" />
                <div className="mt-2 flex items-center justify-between"><span className="text-[10px] text-slate-400">Draft autosaved · {formatTime(currentTime)}</span><button onClick={() => void createNote()} disabled={!draft.trim() || !selected} className="rounded-lg bg-indigo-600 px-3 py-2 text-xs font-bold text-white disabled:opacity-40">Add note</button></div>
                <label className="mt-5 flex items-center gap-2 rounded-xl bg-slate-100 px-3 dark:bg-slate-800"><Search size={14} /><input value={noteSearch} onChange={(event) => setNoteSearch(event.target.value)} placeholder="Search notes" className="w-full bg-transparent py-2.5 text-xs outline-none" /></label>
                <div className="mt-3 space-y-3">{filteredNotes.map((note) => <article key={note.id} className={`rounded-xl border p-3 ${note.is_important ? "border-amber-300 bg-amber-50/50 dark:bg-amber-950/20" : "border-slate-200 dark:border-slate-700"}`}>
                  <div className="flex items-center justify-between gap-2"><div className="flex min-w-0 items-center gap-1.5"><button onClick={() => playerRef.current?.seekTo(note.timestamp_seconds)} className="shrink-0 rounded-md bg-indigo-50 px-2 py-1 text-[10px] font-bold text-indigo-700 dark:bg-indigo-950">▶ {formatTime(note.timestamp_seconds)}{note.range_end_seconds !== null ? `–${formatTime(note.range_end_seconds)}` : ""}</button>{note.source === "ai" && <span className="rounded-full bg-violet-100 px-2 py-0.5 text-[8px] font-black uppercase text-violet-700 dark:bg-violet-950 dark:text-violet-300">AI</span>}</div><div className="flex shrink-0 gap-1"><button title="Pin note" onClick={() => updateNoteLocal(note, { is_pinned: !note.is_pinned })} className={note.is_pinned ? "text-indigo-600" : "text-slate-400"}><Pin size={14} /></button><button title="Mark important" onClick={() => updateNoteLocal(note, { is_important: !note.is_important })} className={note.is_important ? "text-amber-500" : "text-slate-400"}><Star size={14} /></button><button title={editingNoteId === note.id ? "Finish editing" : "Edit note"} onClick={() => setEditingNoteId(editingNoteId === note.id ? null : note.id)} className="text-slate-400 hover:text-indigo-600"><Pencil size={14} /></button><button title="Download PDF" onClick={() => void downloadNote(note)} className="text-slate-400 hover:text-indigo-600"><Download size={14} /></button><button title="Delete note" onClick={() => void deleteNote(note.id)} className="text-slate-400 hover:text-rose-600"><Trash2 size={14} /></button></div></div>
                  {editingNoteId === note.id ? <><textarea value={note.content} onChange={(event) => updateNoteLocal(note, { content: event.target.value })} className="mt-3 min-h-40 w-full resize-y rounded-lg bg-slate-50 p-2 text-xs leading-5 outline-none dark:bg-slate-800" /><p className="text-[9px] text-slate-400">Autosaves after editing</p></> : <NotePreview content={note.content} />}
                </article>)}</div>
              </div>}

              {tab === "bookmarks" && <div><div className="flex items-center justify-between"><h3 className="text-sm font-black">Bookmarks</h3><button onClick={() => void createBookmark()} disabled={!selected} className="rounded-lg bg-indigo-600 px-3 py-2 text-xs font-bold text-white disabled:opacity-40"><Plus size={13} className="inline" /> Add</button></div><div className="mt-4 space-y-3">{data?.bookmarks.map((item) => <article key={item.id} className="rounded-xl border border-slate-200 p-3 dark:border-slate-700"><div className="flex items-center justify-between"><button onClick={() => playerRef.current?.seekTo(item.timestamp_seconds)} className="text-xs font-black text-indigo-600">▶ {formatTime(item.timestamp_seconds)}</button><button onClick={() => void deleteBookmark(item.id)} className="text-slate-400 hover:text-rose-600"><Trash2 size={14} /></button></div><input value={item.label} onChange={(event) => setData((old) => old && ({ ...old, bookmarks: old.bookmarks.map((entry) => entry.id === item.id ? { ...entry, label: event.target.value } : entry) }))} onBlur={(event) => void updateBookmark(item, { label: event.target.value })} className="mt-2 w-full bg-transparent text-xs font-semibold outline-none" /><select value={item.bookmark_type} onChange={(event) => void updateBookmark(item, { bookmark_type: event.target.value })} className="mt-2 rounded-lg border border-slate-200 bg-transparent p-1.5 text-[10px] dark:border-slate-700"><option value="important">Important</option><option value="difficult">Difficult</option><option value="review_later">Review later</option><option value="example">Example</option><option value="interview_point">Interview point</option></select></article>)}{!data?.bookmarks.length && <p className="py-12 text-center text-xs text-slate-400">Bookmark important moments as you study.</p>}</div></div>}

              {tab === "activity" && <div><h3 className="text-sm font-black">Today&apos;s activity</h3><p className="mt-1 text-xs text-slate-500">Only your active learning is counted.</p><div className="mt-4 grid grid-cols-2 gap-3">{[
                [Clock3, "Active study", formatTime(data?.today_activity.active_study_seconds ?? 0)],
                [Play, "Playback", formatTime(data?.today_activity.video_playback_seconds ?? 0)],
                [CheckCircle2, "Unique watched", formatTime(data?.today_activity.unique_watched_seconds ?? 0)],
                [Video, "Videos studied", data?.today_activity.videos_studied ?? 0],
                [Flame, "Completed", data?.today_activity.videos_completed ?? 0],
                [StickyNote, "Notes", data?.today_activity.notes_created ?? 0],
                [Bookmark, "Bookmarks", data?.today_activity.bookmarks_created ?? 0],
              ].map(([Icon, label, value]) => { const ActivityIcon = Icon as typeof Clock3; return <div key={String(label)} className="rounded-xl border border-slate-200 p-3 dark:border-slate-700"><ActivityIcon size={16} className="text-indigo-600" /><p className="mt-3 text-lg font-black">{String(value)}</p><p className="text-[10px] text-slate-500">{String(label)}</p></div>; })}</div></div>}

              {tab === "session" && <div><h3 className="text-sm font-black">Study session</h3>{session ? <div className="mt-5"><div className="rounded-2xl bg-gradient-to-br from-indigo-600 to-blue-600 p-5 text-white"><p className="text-[10px] font-bold uppercase tracking-wider text-indigo-100">{session.status}</p><p className="mt-2 text-4xl font-black tabular-nums">{formatTime(sessionSeconds)}</p><p className="mt-2 text-xs text-indigo-100">{session.session_goal || "Focused learning session"}</p></div><div className="mt-4 grid grid-cols-2 gap-2">{session.status === "active" ? <button onClick={() => void sessionAction("pause")} className="flex items-center justify-center gap-2 rounded-xl border border-slate-200 py-3 text-xs font-bold dark:border-slate-700"><Pause size={15} /> Pause</button> : <button onClick={() => void sessionAction("resume")} className="flex items-center justify-center gap-2 rounded-xl bg-emerald-600 py-3 text-xs font-bold text-white"><Play size={15} /> Resume</button>}<button onClick={() => void sessionAction("end")} className="flex items-center justify-center gap-2 rounded-xl bg-slate-900 py-3 text-xs font-bold text-white dark:bg-slate-700"><Square size={14} /> End</button></div><div className="mt-4 grid grid-cols-2 gap-3 text-center"><div className="rounded-xl bg-slate-100 p-3 dark:bg-slate-800"><p className="font-black">{formatTime(session.paused_seconds)}</p><p className="text-[10px] text-slate-500">Paused</p></div><div className="rounded-xl bg-slate-100 p-3 dark:bg-slate-800"><p className="font-black">{formatTime(session.idle_seconds)}</p><p className="text-[10px] text-slate-500">Idle</p></div></div></div> : <div className="mt-5"><label className="text-xs font-bold">What will you accomplish?</label><textarea value={sessionGoal} onChange={(event) => setSessionGoal(event.target.value)} placeholder="Example: Understand React state updates" className="mt-2 min-h-24 w-full rounded-xl border border-slate-200 bg-transparent p-3 text-sm outline-none dark:border-slate-700" /><button onClick={() => void startSession()} className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 py-3 text-sm font-bold text-white"><Play size={16} /> Start focused session</button><p className="mt-3 text-center text-[10px] leading-4 text-slate-400">Inactive sessions pause automatically after 5 minutes. Activity is saved every 15 seconds.</p></div>}</div>}
            </div>
            </>}
            {!rightCollapsed && maximizedPanel === null && <div onPointerDown={(event) => startResize("right", event)} className="absolute -left-1 top-0 z-20 hidden h-full w-2 cursor-col-resize items-center justify-center hover:bg-indigo-100/60 xl:flex" title="Drag to resize study tools"><GripVertical size={12} className="text-slate-300" /></div>}
          </aside>
        </div>

        {adding && <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/60 p-4"><form onSubmit={addVideo} className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900"><div className="flex items-center justify-between"><div><h2 className="text-lg font-black">Add YouTube video</h2><p className="mt-1 text-xs text-slate-500">The video stays on YouTube and plays through its official player.</p></div><button type="button" onClick={() => setAdding(false)}><X size={18} /></button></div><div className="mt-5 space-y-4"><label className="grid gap-1.5 text-xs font-bold">Video title <span className="font-normal text-slate-400">(optional)</span><input name="title" maxLength={240} className="rounded-xl border border-slate-200 bg-transparent p-3 font-normal dark:border-slate-700" placeholder="What are you learning?" /></label><label className="grid gap-1.5 text-xs font-bold">YouTube link<input name="url" type="url" required className="rounded-xl border border-slate-200 bg-transparent p-3 font-normal dark:border-slate-700" placeholder="https://www.youtube.com/watch?v=..." /></label><label className="grid gap-1.5 text-xs font-bold">Channel <span className="font-normal text-slate-400">(optional)</span><input name="channel" maxLength={180} className="rounded-xl border border-slate-200 bg-transparent p-3 font-normal dark:border-slate-700" /></label></div><button className="mt-6 w-full rounded-xl bg-indigo-600 py-3 text-sm font-bold text-white">Add to my library</button></form></div>}
      </div>
    </StudyAppLayout>
  );
}
