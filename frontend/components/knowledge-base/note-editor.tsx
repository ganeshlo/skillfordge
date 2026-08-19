"use client";

import {
  Bold,
  Bot,
  CheckSquare,
  Clock3,
  Code2,
  Eye,
  Heading2,
  Italic,
  List,
  LoaderCircle,
  Pencil,
  Save,
  Star,
  Trash2,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { api } from "@/lib/api";
import type {
  KnowledgeFolder,
  KnowledgeNote,
  KnowledgeNoteVersion,
  KnowledgeTag,
} from "@/lib/types";
import { MarkdownPreview } from "./markdown-preview";

export function NoteEditor({
  note,
  folders,
  availableTags,
  onSaved,
  onDeleted,
}: {
  note: KnowledgeNote;
  folders: KnowledgeFolder[];
  availableTags: KnowledgeTag[];
  onSaved: (note: KnowledgeNote) => void;
  onDeleted: (id: string) => void;
}) {
  const [title, setTitle] = useState(note.title);
  const [content, setContent] = useState(note.content);
  const [favorite, setFavorite] = useState(note.is_favorite);
  const [folderId, setFolderId] = useState(note.folder_id ?? "");
  const [tagIds, setTagIds] = useState(note.tags.map((tag) => tag.id));
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [preview, setPreview] = useState(false);
  const [versions, setVersions] = useState<KnowledgeNoteVersion[] | null>(null);
  const [aiResult, setAiResult] = useState("");
  const [aiBusy, setAiBusy] = useState("");
  const textarea = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!dirty) return;
    const timer = window.setTimeout(async () => {
      setSaving(true);
      try {
        const saved = await api<KnowledgeNote>(`/knowledge/notes/${note.id}/`, {
          method: "PATCH",
          body: JSON.stringify({
            title,
            content,
            is_favorite: favorite,
            folder_id: folderId || null,
            tag_ids: tagIds,
          }),
        });
        onSaved(saved);
        setDirty(false);
      } finally {
        setSaving(false);
      }
    }, 1200);
    return () => window.clearTimeout(timer);
  }, [content, dirty, favorite, folderId, note.id, onSaved, tagIds, title]);

  function modify(prefix: string, suffix = prefix) {
    const element = textarea.current;
    if (!element) return;
    const start = element.selectionStart,
      end = element.selectionEnd;
    setContent(
      content.slice(0, start) +
        prefix +
        content.slice(start, end) +
        suffix +
        content.slice(end),
    );
    setDirty(true);
    requestAnimationFrame(() => {
      element.focus();
      element.setSelectionRange(start + prefix.length, end + prefix.length);
    });
  }

  async function aiAction(action: string) {
    setAiBusy(action);
    setAiResult("");
    try {
      const result = await api<{ content: string }>("/knowledge/ai-actions/", {
        method: "POST",
        body: JSON.stringify({
          source_type: "note",
          source_id: note.id,
          action,
        }),
      });
      setAiResult(result.content);
    } catch (reason) {
      setAiResult(
        reason instanceof Error ? reason.message : "AI request failed.",
      );
    } finally {
      setAiBusy("");
    }
  }

  async function remove() {
    if (!confirm("Delete this note? Version history will also be removed."))
      return;
    await api(`/knowledge/notes/${note.id}/`, { method: "DELETE" });
    onDeleted(note.id);
  }

  return (
    <section className="flex min-h-[680px] min-w-0 flex-1 flex-col bg-white dark:bg-slate-900">
      <header className="flex flex-wrap items-center gap-2 border-b border-slate-200 px-4 py-3 dark:border-slate-800">
        <input
          value={title}
          onChange={(event) => {
            setTitle(event.target.value);
            setDirty(true);
          }}
          className="min-w-48 flex-1 bg-transparent text-lg font-black outline-none"
          aria-label="Note title"
        />
        <select
          value={folderId}
          onChange={(event) => {
            setFolderId(event.target.value);
            setDirty(true);
          }}
          className="rounded-lg border border-slate-200 bg-transparent px-2 py-1.5 text-xs dark:border-slate-700"
        >
          <option value="">No folder</option>
          {folders.map((folder) => (
            <option key={folder.id} value={folder.id}>
              {folder.name}
            </option>
          ))}
        </select>
        <span className="flex items-center gap-1 text-[10px] text-slate-400">
          {saving ? (
            <LoaderCircle size={12} className="animate-spin" />
          ) : (
            <Save size={12} />
          )}
          {saving ? "Saving" : dirty ? "Autosave pending" : "Saved"}
        </span>
        <button
          onClick={() => {
            setFavorite(!favorite);
            setDirty(true);
          }}
          aria-label="Favorite note"
          className={favorite ? "text-amber-500" : "text-slate-400"}
        >
          <Star size={17} fill={favorite ? "currentColor" : "none"} />
        </button>
        <button
          onClick={() => setPreview(!preview)}
          className="grid size-8 place-items-center rounded-lg border border-slate-200 dark:border-slate-700"
          aria-label={preview ? "Edit note" : "Preview note"}
        >
          {preview ? <Pencil size={15} /> : <Eye size={15} />}
        </button>
        <button
          onClick={() => void remove()}
          className="text-slate-400 hover:text-rose-600"
          aria-label="Delete note"
        >
          <Trash2 size={16} />
        </button>
      </header>
      {!preview && (
        <>
          <div className="flex flex-wrap gap-1 border-b border-slate-100 px-4 py-2 dark:border-slate-800">
            {[
              [Heading2, "Heading", "## ", ""],
              [Bold, "Bold", "**", "**"],
              [Italic, "Italic", "_", "_"],
              [List, "List", "- ", ""],
              [CheckSquare, "Checklist", "- [ ] ", ""],
              [Code2, "Code", "```\n", "\n```"],
            ].map(([Icon, label, prefix, suffix]) => {
              const Tool = Icon as typeof Bold;
              return (
                <button
                  key={String(label)}
                  onClick={() => modify(String(prefix), String(suffix))}
                  title={String(label)}
                  className="grid size-8 place-items-center rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  <Tool size={15} />
                </button>
              );
            })}
            <span className="mx-2 w-px bg-slate-200 dark:bg-slate-700" />
            {["summary", "flashcards", "interview", "revision", "explain"].map(
              (action) => (
                <button
                  key={action}
                  onClick={() => void aiAction(action)}
                  disabled={Boolean(aiBusy)}
                  className="rounded-lg bg-violet-50 px-2.5 py-1.5 text-[10px] font-bold capitalize text-violet-700 disabled:opacity-40 dark:bg-violet-950/40 dark:text-violet-300"
                >
                  {aiBusy === action ? "Working…" : action}
                </button>
              ),
            )}
          </div>
          {availableTags.length > 0 && (
            <div className="flex flex-wrap gap-1.5 border-b border-slate-100 px-4 py-2 dark:border-slate-800">
              {availableTags.map((tag) => (
                <button
                  key={tag.id}
                  onClick={() => {
                    setTagIds((old) =>
                      old.includes(tag.id)
                        ? old.filter((id) => id !== tag.id)
                        : [...old, tag.id],
                    );
                    setDirty(true);
                  }}
                  className={`rounded-full px-2 py-1 text-[9px] font-bold ${tagIds.includes(tag.id) ? "text-white" : "bg-slate-100 text-slate-500 dark:bg-slate-800"}`}
                  style={
                    tagIds.includes(tag.id)
                      ? { backgroundColor: tag.color }
                      : undefined
                  }
                >
                  #{tag.name}
                </button>
              ))}
            </div>
          )}
        </>
      )}
      <div className="min-h-0 flex-1 overflow-y-auto p-5">
        {preview ? (
          <MarkdownPreview content={content} />
        ) : (
          <textarea
            ref={textarea}
            value={content}
            onChange={(event) => {
              setContent(event.target.value);
              setDirty(true);
            }}
            placeholder="Write in Markdown…"
            className="min-h-[520px] w-full resize-none bg-transparent font-mono text-sm leading-7 outline-none"
          />
        )}
        {aiResult && (
          <div className="mt-5 rounded-2xl border border-violet-200 bg-violet-50 p-4 dark:border-violet-900 dark:bg-violet-950/30">
            <div className="flex items-center justify-between">
              <p className="flex items-center gap-2 text-xs font-black text-violet-700 dark:text-violet-300">
                <Bot size={15} /> AI result
              </p>
              <button
                onClick={() => {
                  setContent(`${content}\n\n${aiResult}`);
                  setDirty(true);
                  setAiResult("");
                }}
                className="rounded-lg bg-violet-600 px-3 py-1.5 text-[10px] font-bold text-white"
              >
                Add to note
              </button>
            </div>
            <div className="mt-3">
              <MarkdownPreview content={aiResult} />
            </div>
          </div>
        )}
      </div>
      <footer className="border-t border-slate-100 px-4 py-2 dark:border-slate-800">
        <button
          onClick={async () =>
            setVersions(
              await api<KnowledgeNoteVersion[]>(
                `/knowledge/notes/${note.id}/versions/`,
              ),
            )
          }
          className="flex items-center gap-1.5 text-[10px] font-bold text-slate-500"
        >
          <Clock3 size={13} /> Version {note.current_version}
        </button>
        {versions && (
          <div className="mt-2 flex gap-2 overflow-x-auto pb-1">
            {versions.map((version) => (
              <button
                key={version.id}
                onClick={() => {
                  setTitle(version.title);
                  setContent(version.content);
                  setDirty(true);
                }}
                className="shrink-0 rounded-lg border border-slate-200 px-2 py-1 text-[9px] dark:border-slate-700"
              >
                Restore v{version.version}
              </button>
            ))}
          </div>
        )}
      </footer>
    </section>
  );
}
