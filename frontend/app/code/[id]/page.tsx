"use client";

import Editor, { type OnMount } from "@monaco-editor/react";
import JSZip from "jszip";
import { ArrowLeft, Braces, Check, ChevronDown, ChevronUp, CircleAlert, Clock3, Code2, Download, FileCode2, FilePlus2, FolderOpen, GripHorizontal, History, LayoutDashboard, LoaderCircle, Maximize2, Minimize2, PanelLeftClose, PanelLeftOpen, Play, Save, ShieldCheck, Square, TerminalSquare, Trash2, X } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";
import { CodeAppLayout } from "@/components/code/app-layout";
import { api } from "@/lib/api";
import { buildWebPreview } from "@/lib/code-preview";
import type { CodingCapabilities, CodingFile, CodingProjectDetail, ExecutionJob, User } from "@/lib/types";

type SaveState = "saved" | "saving" | "unsaved" | "error";
type Revision = { id: string; version: number; checksum: string; created_at: string };
const AUTOSAVE_DELAY_MS = 60_000;

function languageForEditor(language: string) {
  if (language === "react") return "typescript";
  if (language === "plaintext") return "plaintext";
  return language;
}

function inferLanguage(path: string) {
  const extension = path.split(".").pop()?.toLowerCase();
  const map: Record<string, string> = { py: "python", js: "javascript", jsx: "javascript", ts: "typescript", tsx: "react", java: "java", c: "c", cpp: "cpp", cc: "cpp", go: "go", rs: "rust", php: "php", rb: "ruby", kt: "kotlin", sql: "sql", html: "html", css: "css", json: "json", md: "markdown" };
  return map[extension ?? ""] ?? "plaintext";
}

function executionIdempotencyKey() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") return crypto.randomUUID();
  return `execution-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export default function CodeEditorPage() {
  const { id } = useParams<{ id: string }>();
  const [user, setUser] = useState<User | null>(null);
  const [project, setProject] = useState<CodingProjectDetail | null>(null);
  const [capabilities, setCapabilities] = useState<CodingCapabilities | null>(null);
  const [activeFileId, setActiveFileId] = useState<string | null>(null);
  const [openFileIds, setOpenFileIds] = useState<string[]>([]);
  const [saveStates, setSaveStates] = useState<Record<string, SaveState>>({});
  const [newFilePath, setNewFilePath] = useState("");
  const [addingFile, setAddingFile] = useState(false);
  const [error, setError] = useState("");
  const [theme, setTheme] = useState<"vs-dark" | "light">("vs-dark");
  const [revisions, setRevisions] = useState<Revision[] | null>(null);
  const [execution, setExecution] = useState<ExecutionJob | null>(null);
  const [runStage, setRunStage] = useState("");
  const [stdin, setStdin] = useState("");
  const [previewDocument, setPreviewDocument] = useState<string | null>(null);
  const [explorerOpen, setExplorerOpen] = useState(true);
  const [explorerWidth, setExplorerWidth] = useState(224);
  const [terminalOpen, setTerminalOpen] = useState(true);
  const [terminalHeight, setTerminalHeight] = useState(180);
  const [terminalMaximized, setTerminalMaximized] = useState(false);
  const [panelView, setPanelView] = useState<"terminal" | "history">("terminal");
  const timers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});
  const latestContent = useRef<Record<string, string>>({});
  const saveSequence = useRef<Record<string, number>>({});
  const executionTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const workspaceRef = useRef<HTMLDivElement | null>(null);
  const editorActions = useRef({
    run: () => {}, save: () => {}, create: () => {}, remove: () => {}, history: () => {},
    download: () => {}, toggleExplorer: () => {}, toggleTerminal: () => {},
  });

  const load = useCallback(async () => {
    try {
      const [me, item, featureSet, recentExecutions] = await Promise.all([
        api<User>("/me/"), api<CodingProjectDetail>(`/coding/projects/${id}/`), api<CodingCapabilities>("/coding/capabilities/"), api<ExecutionJob[]>("/coding/executions/"),
      ]);
      setUser(me); setProject(item); setCapabilities(featureSet); setError("");
      item.files.forEach(file => { latestContent.current[file.id] = file.content; });
      setExecution(current => current ?? recentExecutions.find(job => job.project_id === item.id) ?? null);
      if (item.files.length) { setActiveFileId(current => current ?? item.files[0].id); setOpenFileIds(current => current.length ? current : [item.files[0].id]); }
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load coding workspace"); }
  }, [id]);

  useEffect(() => {
    const task = window.setTimeout(() => void load(), 0);
    const activeTimers = timers.current;
    return () => { clearTimeout(task); Object.values(activeTimers).forEach(clearTimeout); if (executionTimer.current) clearTimeout(executionTimer.current); };
  }, [load]);

  const activeFile = useMemo(() => project?.files.find(file => file.id === activeFileId) ?? null, [activeFileId, project]);
  const openFiles = useMemo(() => project?.files.filter(file => openFileIds.includes(file.id)) ?? [], [openFileIds, project]);

  async function persistFile(file: CodingFile) {
    const submittedContent = file.content;
    const requestSequence = (saveSequence.current[file.id] ?? 0) + 1;
    saveSequence.current[file.id] = requestSequence;
    setSaveStates(current => ({ ...current, [file.id]: "saving" }));
    try {
      const updated = await api<CodingFile>(`/coding/files/${file.id}/`, { method: "PATCH", body: JSON.stringify({ content: submittedContent }) });
      if (saveSequence.current[file.id] !== requestSequence) return;
      const hasNewerEdits = latestContent.current[file.id] !== submittedContent;
      setProject(current => current ? {
        ...current,
        files: current.files.map(item => item.id === updated.id ? { ...updated, content: hasNewerEdits ? item.content : updated.content } : item),
      } : current);
      setSaveStates(current => ({ ...current, [file.id]: hasNewerEdits ? "unsaved" : "saved" }));
    } catch (reason) {
      if (saveSequence.current[file.id] !== requestSequence) return;
      setSaveStates(current => ({ ...current, [file.id]: "error" }));
      setError(reason instanceof Error ? reason.message : "Autosave failed");
    }
  }

  function updateContent(value: string | undefined) {
    if (!activeFile || value === undefined || value === activeFile.content) return;
    const updated = { ...activeFile, content: value };
    setPreviewDocument(null);
    latestContent.current[updated.id] = value;
    setProject(current => current ? { ...current, files: current.files.map(file => file.id === updated.id ? updated : file) } : current);
    setSaveStates(current => ({ ...current, [updated.id]: "unsaved" }));
    clearTimeout(timers.current[updated.id]);
    timers.current[updated.id] = setTimeout(() => void persistFile(updated), AUTOSAVE_DELAY_MS);
  }

  function openFile(file: CodingFile) {
    setActiveFileId(file.id);
    setOpenFileIds(current => current.includes(file.id) ? current : [...current, file.id]);
    setRevisions(null);
  }

  function closeTab(fileId: string) {
    setOpenFileIds(current => {
      const next = current.filter(idValue => idValue !== fileId);
      if (activeFileId === fileId) setActiveFileId(next.at(-1) ?? null);
      return next;
    });
  }

  async function createFile(event: FormEvent) {
    event.preventDefault(); if (!project || !newFilePath.trim()) return;
    try {
      const file = await api<CodingFile>(`/coding/projects/${project.id}/files/`, { method: "POST", body: JSON.stringify({ path: newFilePath.trim(), content: "", language: inferLanguage(newFilePath) }) });
      latestContent.current[file.id] = file.content;
      setProject({ ...project, files: [...project.files, file].sort((a, b) => a.path.localeCompare(b.path)), file_count: project.file_count + 1 });
      setNewFilePath(""); setAddingFile(false); openFile(file);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not create file"); }
  }

  async function deleteFile(file: CodingFile) {
    if (!window.confirm(`Delete ${file.path}? Its version history will also be removed.`)) return;
    try { await api(`/coding/files/${file.id}/`, { method: "DELETE" }); delete latestContent.current[file.id]; delete saveSequence.current[file.id]; setProject(current => current ? { ...current, files: current.files.filter(item => item.id !== file.id), file_count: current.file_count - 1 } : current); closeTab(file.id); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not delete file"); }
  }

  async function showHistory() {
    if (!activeFile) return;
    try { setRevisions(await api<Revision[]>(`/coding/files/${activeFile.id}/revisions/`)); setPanelView("history"); setTerminalOpen(true); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load version history"); }
  }

  async function downloadProject() {
    if (!project) return;
    const zip = new JSZip();
    project.files.forEach(file => zip.file(file.path, file.content));
    const blob = await zip.generateAsync({ type: "blob" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a"); anchor.href = url; anchor.download = `${project.name.toLowerCase().replace(/[^a-z0-9]+/g, "-")}.zip`; anchor.click(); URL.revokeObjectURL(url);
  }

  async function pollExecution(jobId: string) {
    try {
      const job = await api<ExecutionJob>(`/coding/executions/${jobId}/`);
      setExecution(job);
      setRunStage(job.status === "queued" || job.status === "dispatching" ? "Waiting for an isolated worker…" : job.status === "running" ? "Running in the isolated container…" : "");
      if (["queued", "dispatching", "running"].includes(job.status)) {
        executionTimer.current = setTimeout(() => void pollExecution(jobId), 800);
      }
    } catch (reason) { setRunStage(""); setError(reason instanceof Error ? reason.message : "Could not read execution result"); }
  }

  async function runCode() {
    if (!activeFile || !project) { setError("Select a file before running code."); return; }
    setPanelView("terminal"); setTerminalOpen(true);
    if (["html", "css", "react"].includes(activeFile.language)) {
      setError("");
      try {
        if (saveStates[activeFile.id] !== "saved") await persistFile(activeFile);
        setPreviewDocument(buildWebPreview(project.files, activeFile));
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : "The browser preview could not be built.");
      }
      return;
    }
    const executableLanguages = ["python", "javascript", "typescript", "java", "c", "cpp", "go", "rust", "php", "ruby", "kotlin", "sql"];
    if (!executableLanguages.includes(activeFile.language)) {
      setError(`${activeFile.language} files can be edited and saved, but are not executable.`);
      return;
    }
    if (!capabilities?.execution) {
      setExecution(null);
      setError(capabilities?.execution_message ?? "The isolated execution runner is not configured.");
      return;
    }
    setError("");
    setRunStage("Saving the latest source…");
    try {
      if (saveStates[activeFile.id] !== "saved") await persistFile(activeFile);
      setRunStage("Submitting to the isolated runner…");
      const job = await api<ExecutionJob>("/coding/executions/", {
        method: "POST",
        headers: { "Idempotency-Key": executionIdempotencyKey() },
        body: JSON.stringify({ file_id: activeFile.id, stdin }),
      });
      setExecution(job);
      setRunStage("Execution queued…");
      executionTimer.current = setTimeout(() => void pollExecution(job.id), 500);
    } catch (reason) { setRunStage(""); setError(reason instanceof Error ? reason.message : "Execution could not start"); }
  }

  async function stopExecution() {
    if (!execution || !["queued", "dispatching", "running"].includes(execution.status)) return;
    try { const job = await api<ExecutionJob>(`/coding/executions/${execution.id}/cancel/`, { method: "POST", body: "{}" }); setExecution(job); setRunStage(""); if (executionTimer.current) clearTimeout(executionTimer.current); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Execution could not be cancelled"); }
  }

  function resizeExplorer(event: ReactPointerEvent<HTMLDivElement>) {
    event.preventDefault();
    const startX = event.clientX;
    const startWidth = explorerWidth;
    const move = (pointerEvent: PointerEvent) => setExplorerWidth(Math.min(480, Math.max(168, startWidth + pointerEvent.clientX - startX)));
    const stop = () => { window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", stop); };
    window.addEventListener("pointermove", move); window.addEventListener("pointerup", stop);
  }

  function resizeTerminal(event: ReactPointerEvent<HTMLDivElement>) {
    event.preventDefault();
    setTerminalMaximized(false);
    const startY = event.clientY;
    const startHeight = terminalHeight;
    const move = (pointerEvent: PointerEvent) => {
      const maximum = Math.max(180, (workspaceRef.current?.getBoundingClientRect().height ?? 600) * 0.75);
      setTerminalHeight(Math.min(maximum, Math.max(96, startHeight + startY - pointerEvent.clientY)));
    };
    const stop = () => { window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", stop); };
    window.addEventListener("pointermove", move); window.addEventListener("pointerup", stop);
  }

  const handleEditorMount: OnMount = (editor, monaco) => {
    const addAction = (id: string, label: string, order: number, run: () => void, keybindings?: number[]) => editor.addAction({
      id: `learnos.${id}`, label, contextMenuGroupId: "learnos.actions", contextMenuOrder: order, keybindings, run,
    });
    addAction("run", "Run / Preview", 1, () => editorActions.current.run(), [monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter]);
    addAction("save", "Save file", 2, () => editorActions.current.save(), [monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS]);
    addAction("new-file", "New file", 3, () => editorActions.current.create(), [monaco.KeyMod.CtrlCmd | monaco.KeyMod.Alt | monaco.KeyCode.KeyN]);
    addAction("history", "Show version history", 4, () => editorActions.current.history());
    addAction("download", "Download project", 5, () => editorActions.current.download());
    addAction("toggle-explorer", "Toggle Explorer", 6, () => editorActions.current.toggleExplorer(), [monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.KeyE]);
    addAction("toggle-terminal", "Toggle Terminal", 7, () => editorActions.current.toggleTerminal(), [monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyJ]);
    addAction("delete-file", "Delete current file", 8, () => editorActions.current.remove());
  };

  if (!project) return <CodeAppLayout user={user} immersive><div className="grid flex-1 place-items-center bg-slate-950 text-center text-white">{error ? <div><CircleAlert className="mx-auto text-rose-400" /><h1 className="mt-3 font-black">Workspace unavailable</h1><p className="mt-2 text-sm text-slate-400">{error}</p><Link href="/code" className="mt-4 inline-flex rounded-lg bg-violet-600 px-4 py-2 text-sm font-bold">Back to projects</Link></div> : <LoaderCircle className="animate-spin text-violet-400" />}</div></CodeAppLayout>;

  const state = activeFile ? saveStates[activeFile.id] ?? "saved" : "saved";
  const running = Boolean(execution && ["queued", "dispatching", "running"].includes(execution.status));
  const previewLanguage = Boolean(activeFile && ["html", "css", "react"].includes(activeFile.language));
  const executableLanguage = Boolean(activeFile && ["python", "javascript", "typescript", "java", "c", "cpp", "go", "rust", "php", "ruby", "kotlin", "sql"].includes(activeFile.language));
  const supportedForRun = previewLanguage || executableLanguage;
  const canRun = previewLanguage || Boolean(capabilities?.execution && executableLanguage);
  editorActions.current = {
    run: () => void runCode(),
    save: () => { if (activeFile) void persistFile(activeFile); },
    create: () => { setExplorerOpen(true); setAddingFile(true); },
    remove: () => { if (activeFile) void deleteFile(activeFile); },
    history: () => void showHistory(),
    download: () => void downloadProject(),
    toggleExplorer: () => setExplorerOpen(current => !current),
    toggleTerminal: () => setTerminalOpen(current => !current),
  };
  return <CodeAppLayout user={user} immersive><div className="flex min-h-0 flex-1 flex-col bg-[#0d1117] text-slate-200">
    <header className="flex h-12 shrink-0 items-center gap-2 border-b border-slate-800 bg-[#11161d] px-3"><Link href="/code" className="grid size-8 place-items-center rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white" aria-label="Back to projects"><ArrowLeft size={17} /></Link><Link href="/dashboard" className="grid size-8 place-items-center rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white" aria-label="Open dashboard" title="Dashboard"><LayoutDashboard size={16} /></Link><button onClick={() => setExplorerOpen(current => !current)} className="grid size-8 place-items-center rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white" title={explorerOpen ? "Hide Explorer (⌘⇧E)" : "Show Explorer (⌘⇧E)"}>{explorerOpen ? <PanelLeftClose size={16} /> : <PanelLeftOpen size={16} />}</button><Braces size={17} className="text-violet-400" /><strong className="max-w-48 truncate text-xs">{project.name}</strong><span className="hidden text-[10px] text-slate-500 sm:inline">/ {activeFile?.path ?? "No file selected"}</span><div className="ml-auto flex items-center gap-1"><button onClick={() => setTerminalOpen(current => !current)} className="grid size-8 place-items-center rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white" title="Toggle Terminal (⌘J)"><TerminalSquare size={16} /></button><span className={`mr-2 hidden items-center gap-1 text-[9px] sm:flex ${state === "error" ? "text-rose-400" : state === "saved" ? "text-emerald-400" : "text-amber-400"}`}>{state === "saving" ? <LoaderCircle className="animate-spin" size={11} /> : state === "saved" ? <Check size={11} /> : <CircleAlert size={11} />}{state}</span><button onClick={() => activeFile && void persistFile(activeFile)} disabled={!activeFile || state === "saving"} className="grid size-8 place-items-center rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white" title="Save now (⌘S)"><Save size={16} /></button><button onClick={() => void downloadProject()} className="grid size-8 place-items-center rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white" title="Download project"><Download size={16} /></button>{running ? <button onClick={() => void stopExecution()} className="ml-1 inline-flex items-center gap-1.5 rounded-lg bg-rose-600 px-3 py-2 text-[10px] font-bold text-white"><Square size={11} fill="currentColor" /> Stop</button> : <button onClick={() => void runCode()} disabled={!supportedForRun} title={canRun ? previewLanguage ? "Open sandboxed browser preview" : "Run in isolated sandbox (⌘↵)" : capabilities?.execution_message ?? "Checking runner availability"} className={`ml-1 inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-[10px] font-bold text-white disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400 ${canRun ? "bg-emerald-600 hover:bg-emerald-500" : "bg-amber-600 hover:bg-amber-500"}`}><Play size={13} fill="currentColor" /> {previewLanguage ? "Preview" : "Run"}</button>}</div></header>
    {error && <div className="flex shrink-0 items-center justify-between bg-rose-950/60 px-4 py-2 text-xs text-rose-300"><span>{error}</span><button onClick={() => setError("")}><X size={14} /></button></div>}
    <div ref={workspaceRef} className="flex min-h-0 flex-1">{explorerOpen && <aside style={{ width: explorerWidth }} className="relative hidden shrink-0 flex-col border-r border-slate-800 bg-[#11161d] sm:flex"><div className="flex h-10 items-center justify-between px-3"><span className="text-[10px] font-black uppercase tracking-wider text-slate-400">Explorer</span><div className="flex items-center gap-1"><button onClick={() => setExplorerWidth(current => current >= 340 ? 224 : 360)} className="grid size-6 place-items-center text-slate-500 hover:text-white" title={explorerWidth >= 340 ? "Restore Explorer width" : "Maximize Explorer"}>{explorerWidth >= 340 ? <Minimize2 size={13} /> : <Maximize2 size={13} />}</button><button onClick={() => setAddingFile(true)} className="grid size-6 place-items-center text-slate-400 hover:text-white" title="New file"><FilePlus2 size={15} /></button><button onClick={() => setExplorerOpen(false)} className="grid size-6 place-items-center text-slate-500 hover:text-white" title="Hide Explorer"><X size={13} /></button></div></div><div className="flex items-center gap-1.5 px-3 pb-2 text-[10px] font-bold uppercase text-slate-300"><ChevronDown size={13} /><FolderOpen size={13} className="text-violet-400" /><span className="truncate">{project.name}</span></div><div className="min-h-0 flex-1 overflow-y-auto px-1">{project.files.map(file => <div key={file.id} className={`group flex items-center rounded-md ${file.id === activeFileId ? "bg-slate-800 text-white" : "text-slate-400 hover:bg-slate-800/60"}`}><button onClick={() => openFile(file)} className="flex min-w-0 flex-1 items-center gap-2 px-3 py-1.5 text-left text-[11px]"><FileCode2 size={13} className="shrink-0 text-blue-400" /><span className="truncate">{file.path}</span>{saveStates[file.id] === "unsaved" && <span className="ml-auto size-1.5 rounded-full bg-amber-400" />}</button><button onClick={() => void deleteFile(file)} className="mr-1 hidden p-1 text-slate-500 hover:text-rose-400 group-hover:block" aria-label={`Delete ${file.path}`}><Trash2 size={12} /></button></div>)}{addingFile && <form onSubmit={createFile} className="p-2"><input value={newFilePath} onChange={event => setNewFilePath(event.target.value)} autoFocus placeholder="src/file.py" className="w-full rounded border border-violet-500 bg-slate-950 px-2 py-1.5 text-[10px] text-white outline-none" /><div className="mt-1 flex gap-1"><button className="rounded bg-violet-600 px-2 py-1 text-[9px] font-bold">Create</button><button type="button" onClick={() => setAddingFile(false)} className="px-2 text-[9px] text-slate-500">Cancel</button></div></form>}</div><div className="border-t border-slate-800 p-3 text-[9px] text-slate-500"><div className="flex items-center gap-1.5"><ShieldCheck size={12} className="text-emerald-500" /> Owner-scoped files</div><div className="mt-1 flex items-center gap-1.5"><Clock3 size={12} /> {project.files.length} files · autosave</div></div><div onPointerDown={resizeExplorer} className="absolute inset-y-0 -right-1 z-10 w-2 cursor-col-resize touch-none hover:bg-violet-500/50" title="Drag to resize Explorer" /></aside>}
      <section className="flex min-w-0 flex-1 flex-col"><div className="flex h-9 shrink-0 overflow-x-auto border-b border-slate-800 bg-[#0f141b]">{openFiles.map(file => <div key={file.id} className={`flex min-w-32 max-w-52 items-center border-r border-slate-800 px-2 text-[10px] ${file.id === activeFileId ? "border-t border-t-violet-500 bg-[#0d1117] text-white" : "text-slate-500"}`}><button onClick={() => openFile(file)} className="flex min-w-0 flex-1 items-center gap-1.5"><FileCode2 size={12} className="shrink-0 text-blue-400" /><span className="truncate">{file.path.split("/").at(-1)}</span>{saveStates[file.id] === "unsaved" && <span className="size-1.5 rounded-full bg-amber-400" />}</button><button onClick={() => closeTab(file.id)} className="ml-2 text-slate-500 hover:text-white"><X size={12} /></button></div>)}</div>
        <div className="relative min-h-0 flex-1">{previewDocument ? <><button onClick={() => setPreviewDocument(null)} className="absolute right-3 top-3 z-10 rounded-lg bg-slate-950 px-3 py-2 text-[10px] font-bold text-white shadow-lg">Back to editor</button><iframe title="Project preview" sandbox="allow-scripts" srcDoc={previewDocument} className="h-full w-full border-0 bg-white" /></> : activeFile ? <Editor height="100%" language={languageForEditor(activeFile.language)} value={activeFile.content} theme={theme} onMount={handleEditorMount} onChange={updateContent} options={{ fontSize: 13, fontFamily: "SFMono-Regular, Consolas, monospace", minimap: { enabled: true }, automaticLayout: true, scrollBeyondLastLine: false, tabSize: 2, wordWrap: "on", padding: { top: 14 }, bracketPairColorization: { enabled: true } }} loading={<div className="grid h-full place-items-center"><LoaderCircle className="animate-spin text-violet-400" /></div>} /> : <div className="grid h-full place-items-center text-center text-slate-500"><div><Code2 className="mx-auto" size={36} /><p className="mt-3 text-xs">Create or select a file to begin.</p></div></div>}</div>
        {terminalOpen && <div style={{ height: terminalMaximized ? "72%" : terminalHeight }} className="relative shrink-0 border-t border-slate-800 bg-[#0a0e13]"><div onPointerDown={resizeTerminal} className="absolute -top-1.5 inset-x-0 z-10 flex h-3 cursor-row-resize touch-none items-center justify-center text-slate-700 hover:bg-violet-500/30 hover:text-violet-300" title="Drag to resize Terminal"><GripHorizontal size={18} /></div><div className="flex h-9 items-center border-b border-slate-800 px-3"><button onClick={() => setPanelView("terminal")} className={`inline-flex h-full items-center gap-2 border-b px-1 text-[9px] font-black uppercase tracking-wider ${panelView === "terminal" ? "border-emerald-500 text-slate-200" : "border-transparent text-slate-500 hover:text-white"}`}><TerminalSquare size={13} className="text-emerald-500" /> Terminal</button><button onClick={() => void showHistory()} disabled={!activeFile} className={`ml-3 inline-flex h-full items-center gap-1 border-b px-1 text-[9px] font-black uppercase tracking-wider ${panelView === "history" ? "border-violet-500 text-slate-200" : "border-transparent text-slate-500 hover:text-white"}`}><History size={11} /> Versions</button>{panelView === "terminal" && <span className={`ml-3 text-[9px] font-bold ${execution?.status === "succeeded" ? "text-emerald-400" : execution?.status === "failed" || execution?.status === "timed_out" ? "text-rose-400" : "text-amber-400"}`}>{execution?.status}</span>}<input value={stdin} onChange={event => setStdin(event.target.value)} disabled={running} placeholder="Standard input before Run (optional)" className="ml-auto hidden w-52 rounded border border-slate-800 bg-slate-950 px-2 py-1 text-[9px] text-slate-300 outline-none focus:border-violet-500 md:block" /><button onClick={() => setTheme(current => current === "vs-dark" ? "light" : "vs-dark")} className="ml-3 text-[9px] text-slate-500 hover:text-white">Theme: {theme === "vs-dark" ? "Dark" : "Light"}</button><button onClick={() => setTerminalMaximized(current => !current)} className="ml-2 grid size-6 place-items-center text-slate-500 hover:text-white" title={terminalMaximized ? "Restore Terminal" : "Maximize Terminal"}>{terminalMaximized ? <Minimize2 size={13} /> : <Maximize2 size={13} />}</button><button onClick={() => setTerminalOpen(false)} className="grid size-6 place-items-center text-slate-500 hover:text-white" title="Minimize Terminal"><ChevronDown size={15} /></button></div><div className="h-[calc(100%-2.25rem)] overflow-auto whitespace-pre-wrap p-3 font-mono text-[10px] leading-5 text-slate-400">{panelView === "history" ? revisions ? revisions.length ? revisions.map(revision => <div key={revision.id}>v{revision.version} · {new Date(revision.created_at).toLocaleString()} · {revision.checksum.slice(0, 12)}</div>) : "No revisions recorded." : <span className="inline-flex items-center gap-2"><LoaderCircle size={12} className="animate-spin" />Loading versions…</span> : runStage ? <span className="inline-flex items-center gap-2 text-amber-400"><LoaderCircle size={12} className="animate-spin" />{runStage}</span> : execution ? <>{execution.stdout && <span className="text-slate-200">{execution.stdout}</span>}{execution.stderr && <span className="text-rose-300">{execution.stderr}</span>}{running && <span className="text-amber-400">Running in isolated sandbox…</span>}{!running && <div className="mt-2 text-slate-600">Exit {execution.exit_code ?? "—"} · {execution.runtime_ms ?? "—"} ms · {execution.memory_bytes ? `${Math.round(execution.memory_bytes / 1024)} KB` : "memory —"}</div>}</> : <><span className="text-amber-400">{capabilities?.execution ? "Ready:" : "Execution unavailable:"}</span> {capabilities?.execution_message ?? "Checking isolated runner capability…"}<br /><span className="text-slate-600">Run output appears here. This is an isolated execution terminal, not a host-system shell.</span></>}</div></div>}
        {!terminalOpen && <button onClick={() => setTerminalOpen(true)} className="flex h-8 shrink-0 items-center gap-2 border-t border-slate-800 bg-[#0a0e13] px-3 text-[9px] font-black uppercase tracking-wider text-slate-500 hover:text-white"><ChevronUp size={14} /> Terminal</button>}
      </section></div>
  </div></CodeAppLayout>;
}
