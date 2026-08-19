"use client";

import {
  FolderPlus,
  LoaderCircle,
  Moon,
  Settings2,
  Sun,
  Tag,
  X,
} from "lucide-react";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { KnowledgeAppLayout } from "@/components/knowledge-base/app-layout";
import { DocumentLibrary } from "@/components/knowledge-base/document-library";
import { NotesWorkspace } from "@/components/knowledge-base/notes-workspace";
import { KnowledgeOverview } from "@/components/knowledge-base/overview";
import { SearchPanel } from "@/components/knowledge-base/search-panel";
import { SnippetLibrary } from "@/components/knowledge-base/snippet-library";
import { VideoKnowledge } from "@/components/knowledge-base/video-knowledge";
import {
  type KnowledgeView,
  WorkspaceNav,
} from "@/components/knowledge-base/workspace-nav";
import { api } from "@/lib/api";
import type {
  KnowledgeDashboard,
  KnowledgeFolder,
  KnowledgeTag,
  User,
} from "@/lib/types";

export default function KnowledgePage() {
  const [user, setUser] = useState<User | null>(null);
  const [data, setData] = useState<KnowledgeDashboard | null>(null);
  const [view, setView] = useState<KnowledgeView>("overview");
  const [folderId, setFolderId] = useState<string | null>(null);
  const [organize, setOrganize] = useState(false);
  const [dark, setDark] = useState(false);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    try {
      const [me, dashboard] = await Promise.all([
        api<User>("/me/"),
        api<KnowledgeDashboard>("/knowledge/"),
      ]);
      setUser(me);
      setData(dashboard);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Knowledge base could not load.",
      );
    }
  }, []);
  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function createFolder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const folder = await api<KnowledgeFolder>("/knowledge/folders/", {
      method: "POST",
      body: JSON.stringify({
        name: form.get("name"),
        color: form.get("color"),
        parent_id: form.get("parent") || null,
      }),
    });
    setData((old) => old && { ...old, folders: [...old.folders, folder] });
    event.currentTarget.reset();
  }
  async function createTag(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const tag = await api<KnowledgeTag>("/knowledge/tags/", {
      method: "POST",
      body: JSON.stringify({
        name: form.get("name"),
        color: form.get("color"),
      }),
    });
    setData((old) => old && { ...old, tags: [...old.tags, tag] });
    event.currentTarget.reset();
  }
  function chooseFolder(id: string | null) {
    setFolderId(id);
    if (view === "overview" || view === "search" || view === "videos")
      setView("notes");
  }
  return (
    <KnowledgeAppLayout user={user}>
      <div
        className={
          dark
            ? "dark min-h-[calc(100vh-4rem)] bg-slate-950 text-slate-100"
            : "min-h-[calc(100vh-4rem)] bg-slate-50 text-slate-900"
        }
      >
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white px-5 py-4 dark:border-slate-800 dark:bg-slate-900">
          <div>
            <p className="text-[10px] font-black uppercase tracking-[.18em] text-indigo-600">
              LearnOS Knowledge
            </p>
            <h1 className="mt-1 text-2xl font-black tracking-tight">
              Knowledge Base
            </h1>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setOrganize(true)}
              className="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-xs font-bold dark:border-slate-700"
            >
              <Settings2 size={15} /> Organize
            </button>
            <button
              onClick={() => setDark(!dark)}
              className="grid size-9 place-items-center rounded-xl border border-slate-200 dark:border-slate-700"
              aria-label="Toggle dark mode"
            >
              {dark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
          </div>
        </header>
        {error && (
          <div className="m-4 rounded-xl bg-rose-50 p-3 text-xs font-bold text-rose-700">
            {error}
          </div>
        )}
        {!data ? (
          <div className="grid min-h-96 place-items-center">
            <LoaderCircle className="animate-spin text-indigo-600" />
          </div>
        ) : (
          <div className="lg:flex">
            <WorkspaceNav
              view={view}
              folders={data.folders}
              selectedFolder={folderId}
              onView={setView}
              onFolder={chooseFolder}
              onNewFolder={() => setOrganize(true)}
            />
            <main className="min-w-0 flex-1 p-4 sm:p-6">
              {view === "overview" && (
                <KnowledgeOverview data={data} onView={setView} />
              )}
              {view === "notes" && (
                <NotesWorkspace
                  folders={data.folders}
                  tags={data.tags}
                  folderId={folderId}
                  onCountsChanged={() => void load()}
                />
              )}
              {view === "documents" && (
                <DocumentLibrary
                  folders={data.folders}
                  folderId={folderId}
                  onCountsChanged={() => void load()}
                />
              )}
              {view === "snippets" && (
                <SnippetLibrary
                  folders={data.folders}
                  folderId={folderId}
                  onCountsChanged={() => void load()}
                />
              )}
              {view === "videos" && <VideoKnowledge />}
              {view === "search" && (
                <SearchPanel
                  semanticAvailable={data.semantic_search_available}
                />
              )}
            </main>
          </div>
        )}
        {organize && data && (
          <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4">
            <div className="w-full max-w-xl rounded-2xl bg-white p-5 shadow-2xl dark:bg-slate-900">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="font-black">Organize knowledge</h2>
                  <p className="text-xs text-slate-500">
                    Folders can represent subjects, topics, or projects.
                  </p>
                </div>
                <button onClick={() => setOrganize(false)}>
                  <X size={18} />
                </button>
              </div>
              <div className="mt-5 grid gap-5 sm:grid-cols-2">
                <form
                  onSubmit={createFolder}
                  className="rounded-xl border border-slate-200 p-4 dark:border-slate-700"
                >
                  <p className="flex items-center gap-2 text-xs font-black">
                    <FolderPlus size={15} /> New folder
                  </p>
                  <input
                    name="name"
                    required
                    placeholder="React learning"
                    className="mt-3 w-full rounded-lg border border-slate-200 bg-transparent p-2.5 text-xs dark:border-slate-700"
                  />
                  <select
                    name="parent"
                    className="mt-2 w-full rounded-lg border border-slate-200 bg-transparent p-2.5 text-xs dark:border-slate-700"
                  >
                    <option value="">Top level</option>
                    {data.folders.map((folder) => (
                      <option key={folder.id} value={folder.id}>
                        {folder.name}
                      </option>
                    ))}
                  </select>
                  <input
                    name="color"
                    type="color"
                    defaultValue="#4F46E5"
                    className="mt-2 h-9 w-full"
                  />
                  <button className="mt-2 w-full rounded-lg bg-indigo-600 py-2 text-xs font-bold text-white">
                    Create folder
                  </button>
                </form>
                <form
                  onSubmit={createTag}
                  className="rounded-xl border border-slate-200 p-4 dark:border-slate-700"
                >
                  <p className="flex items-center gap-2 text-xs font-black">
                    <Tag size={15} /> New tag
                  </p>
                  <input
                    name="name"
                    required
                    placeholder="authentication"
                    className="mt-3 w-full rounded-lg border border-slate-200 bg-transparent p-2.5 text-xs dark:border-slate-700"
                  />
                  <input
                    name="color"
                    type="color"
                    defaultValue="#7C3AED"
                    className="mt-2 h-9 w-full"
                  />
                  <button className="mt-2 w-full rounded-lg bg-violet-600 py-2 text-xs font-bold text-white">
                    Create tag
                  </button>
                  <div className="mt-3 flex flex-wrap gap-1">
                    {data.tags.map((tag) => (
                      <span
                        key={tag.id}
                        className="rounded-full px-2 py-1 text-[9px] font-bold text-white"
                        style={{ backgroundColor: tag.color }}
                      >
                        #{tag.name}
                      </span>
                    ))}
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </KnowledgeAppLayout>
  );
}
