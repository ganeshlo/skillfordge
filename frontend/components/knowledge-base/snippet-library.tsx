"use client";

import {
  Check,
  Code2,
  Copy,
  Plus,
  Search,
  Star,
  Trash2,
  X,
} from "lucide-react";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { CodeSnippet, KnowledgeFolder } from "@/lib/types";

const languages = [
  "python",
  "javascript",
  "typescript",
  "react",
  "html",
  "css",
  "sql",
  "java",
  "go",
  "rust",
  "bash",
  "other",
];

export function SnippetLibrary({
  folderId,
  onCountsChanged,
}: {
  folders: KnowledgeFolder[];
  folderId: string | null;
  onCountsChanged: () => void;
}) {
  const [items, setItems] = useState<CodeSnippet[]>([]);
  const [creating, setCreating] = useState(false);
  const [query, setQuery] = useState("");
  const [copied, setCopied] = useState("");
  const load = useCallback(
    async () => setItems(await api<CodeSnippet[]>("/knowledge/snippets/")),
    [],
  );
  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const item = await api<CodeSnippet>("/knowledge/snippets/", {
      method: "POST",
      body: JSON.stringify({
        title: form.get("title"),
        description: form.get("description"),
        language: form.get("language"),
        code: form.get("code"),
        folder_id: folderId,
      }),
    });
    setItems((old) => [item, ...old]);
    setCreating(false);
    onCountsChanged();
  }
  async function copy(item: CodeSnippet) {
    await navigator.clipboard.writeText(item.code);
    setCopied(item.id);
    window.setTimeout(() => setCopied(""), 1500);
  }
  async function remove(id: string) {
    await api(`/knowledge/snippets/${id}/`, { method: "DELETE" });
    setItems((old) => old.filter((item) => item.id !== id));
    onCountsChanged();
  }
  const visible = items.filter(
    (item) =>
      (!folderId || item.folder_id === folderId) &&
      `${item.title} ${item.description} ${item.language} ${item.code}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <label className="flex min-w-64 flex-1 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 dark:border-slate-800 dark:bg-slate-900">
          <Search size={15} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search code snippets"
            className="w-full bg-transparent py-3 text-xs outline-none"
          />
        </label>
        <button
          onClick={() => setCreating(true)}
          className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-xs font-bold text-white"
        >
          <Plus size={15} /> New snippet
        </button>
      </div>
      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {visible.map((item) => (
          <article
            key={item.id}
            className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900"
          >
            <header className="flex items-start justify-between p-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="grid size-8 place-items-center rounded-lg bg-slate-950 text-indigo-300">
                    <Code2 size={15} />
                  </span>
                  <div>
                    <h3 className="text-sm font-black">{item.title}</h3>
                    <p className="text-[9px] font-bold uppercase text-indigo-600">
                      {item.language}
                    </p>
                  </div>
                </div>
                <p className="mt-2 text-[10px] text-slate-500">
                  {item.description}
                </p>
              </div>
              {item.is_favorite && (
                <Star
                  size={14}
                  className="text-amber-500"
                  fill="currentColor"
                />
              )}
            </header>
            <pre className="max-h-56 overflow-auto bg-slate-950 p-4 text-xs leading-6 text-slate-200">
              <code>{item.code}</code>
            </pre>
            <footer className="flex justify-between p-3">
              <button
                onClick={() => void copy(item)}
                className="flex items-center gap-1.5 text-[10px] font-bold text-indigo-600"
              >
                {copied === item.id ? <Check size={13} /> : <Copy size={13} />}
                {copied === item.id ? "Copied" : "Copy"}
              </button>
              <button
                onClick={() => void remove(item.id)}
                className="text-slate-400 hover:text-rose-600"
              >
                <Trash2 size={14} />
              </button>
            </footer>
          </article>
        ))}
      </div>
      {creating && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4">
          <form
            onSubmit={create}
            className="w-full max-w-xl rounded-2xl bg-white p-5 shadow-2xl dark:bg-slate-900"
          >
            <div className="flex justify-between">
              <h2 className="font-black">Save code snippet</h2>
              <button type="button" onClick={() => setCreating(false)}>
                <X size={17} />
              </button>
            </div>
            <div className="mt-4 grid gap-3">
              <input
                name="title"
                required
                placeholder="Snippet title"
                className="rounded-xl border border-slate-200 bg-transparent p-3 text-sm dark:border-slate-700"
              />
              <input
                name="description"
                placeholder="When should you use it?"
                className="rounded-xl border border-slate-200 bg-transparent p-3 text-sm dark:border-slate-700"
              />
              <select
                name="language"
                className="rounded-xl border border-slate-200 bg-transparent p-3 text-sm dark:border-slate-700"
              >
                {languages.map((language) => (
                  <option key={language}>{language}</option>
                ))}
              </select>
              <textarea
                name="code"
                required
                rows={12}
                placeholder="Paste reusable code…"
                className="rounded-xl border border-slate-200 bg-slate-950 p-3 font-mono text-xs text-white"
              />
            </div>
            <button className="mt-4 w-full rounded-xl bg-indigo-600 py-3 text-sm font-bold text-white">
              Save snippet
            </button>
          </form>
        </div>
      )}
    </>
  );
}
