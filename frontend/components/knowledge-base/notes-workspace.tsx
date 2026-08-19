"use client";

import { FilePlus2, Search, Star } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { KnowledgeFolder, KnowledgeNote, KnowledgeTag } from "@/lib/types";
import { NoteEditor } from "./note-editor";

export function NotesWorkspace({
  folders,
  tags,
  folderId,
  onCountsChanged,
}: {
  folders: KnowledgeFolder[];
  tags: KnowledgeTag[];
  folderId: string | null;
  onCountsChanged: () => void;
}) {
  const [notes, setNotes] = useState<KnowledgeNote[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const load = useCallback(async () => {
    const params = new URLSearchParams();
    if (folderId) params.set("folder_id", folderId);
    if (query) params.set("q", query);
    const items = await api<KnowledgeNote[]>(`/knowledge/notes/?${params}`);
    setNotes(items);
    setSelectedId((current) =>
      items.some((item) => item.id === current)
        ? current
        : (items[0]?.id ?? null),
    );
  }, [folderId, query]);
  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function create() {
    const note = await api<KnowledgeNote>("/knowledge/notes/", {
      method: "POST",
      body: JSON.stringify({
        title: "Untitled note",
        content: "# New note\n\n",
        folder_id: folderId,
      }),
    });
    setNotes((old) => [note, ...old]);
    setSelectedId(note.id);
    onCountsChanged();
  }
  const selected = notes.find((item) => item.id === selectedId) ?? null;
  return (
    <div className="flex min-h-[680px] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <aside
        className={`${selected ? "hidden md:block" : "block"} w-full shrink-0 border-r border-slate-200 dark:border-slate-800 md:w-72`}
      >
        <div className="flex items-center gap-2 border-b border-slate-100 p-3 dark:border-slate-800">
          <label className="flex flex-1 items-center gap-2 rounded-lg bg-slate-100 px-3 dark:bg-slate-800">
            <Search size={14} />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search notes"
              className="w-full bg-transparent py-2 text-xs outline-none"
            />
          </label>
          <button
            onClick={() => void create()}
            className="grid size-9 place-items-center rounded-lg bg-indigo-600 text-white"
            aria-label="New note"
          >
            <FilePlus2 size={16} />
          </button>
        </div>
        <div className="max-h-[620px] overflow-y-auto p-2">
          {notes.map((note) => (
            <button
              key={note.id}
              onClick={() => setSelectedId(note.id)}
              className={`mb-1 w-full rounded-xl p-3 text-left ${selectedId === note.id ? "bg-indigo-50 dark:bg-indigo-950/40" : "hover:bg-slate-50 dark:hover:bg-slate-800"}`}
            >
              <div className="flex gap-2">
                <p className="min-w-0 flex-1 truncate text-xs font-black">
                  {note.title}
                </p>
                {note.is_favorite && (
                  <Star
                    size={12}
                    className="text-amber-500"
                    fill="currentColor"
                  />
                )}
              </div>
              <p className="mt-1 line-clamp-2 text-[10px] leading-4 text-slate-500">
                {note.content.replace(/[#*_`]/g, "") || "Empty note"}
              </p>
              <p className="mt-2 text-[9px] text-slate-400">
                v{note.current_version} ·{" "}
                {new Date(note.updated_at).toLocaleDateString()}
              </p>
            </button>
          ))}
          {!notes.length && (
            <p className="p-8 text-center text-xs text-slate-400">
              Create your first knowledge note.
            </p>
          )}
        </div>
      </aside>
      {selected ? (
        <NoteEditor
          key={selected.id}
          note={selected}
          folders={folders}
          availableTags={tags}
          onSaved={(saved) =>
            setNotes((old) =>
              old.map((item) => (item.id === saved.id ? saved : item)),
            )
          }
          onDeleted={(id) => {
            setNotes((old) => old.filter((item) => item.id !== id));
            setSelectedId(null);
            onCountsChanged();
          }}
        />
      ) : (
        <div className="hidden flex-1 place-items-center text-center md:grid">
          <div>
            <FilePlus2 className="mx-auto text-indigo-300" size={40} />
            <p className="mt-3 text-sm font-bold">Select or create a note</p>
          </div>
        </div>
      )}
    </div>
  );
}
