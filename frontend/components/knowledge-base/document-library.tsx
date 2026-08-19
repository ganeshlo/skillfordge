"use client";
/* eslint-disable @next/next/no-img-element */

import {
  Bot,
  Download,
  File,
  FileText,
  Highlighter,
  Image as ImageIcon,
  LoaderCircle,
  Star,
  Trash2,
  Upload,
} from "lucide-react";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { api, apiBlob, apiForm } from "@/lib/api";
import type {
  DocumentHighlight,
  KnowledgeDocument,
  KnowledgeFolder,
} from "@/lib/types";

function fileIcon(type: string) {
  if (type.startsWith("image/")) return ImageIcon;
  if (type === "application/pdf") return FileText;
  return File;
}

export function DocumentLibrary({
  folders,
  folderId,
  onCountsChanged,
}: {
  folders: KnowledgeFolder[];
  folderId: string | null;
  onCountsChanged: () => void;
}) {
  const [items, setItems] = useState<KnowledgeDocument[]>([]);
  const [selected, setSelected] = useState<KnowledgeDocument | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [extractedText, setExtractedText] = useState("");
  const [highlights, setHighlights] = useState<DocumentHighlight[]>([]);
  const [uploading, setUploading] = useState(false);
  const [aiOutput, setAiOutput] = useState("");
  const load = useCallback(
    async () =>
      setItems(await api<KnowledgeDocument[]>("/knowledge/documents/")),
    [],
  );
  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);
  useEffect(
    () => () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    },
    [previewUrl],
  );

  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setUploading(true);
    const form = new FormData(event.currentTarget);
    if (folderId) form.set("folder_id", folderId);
    try {
      const document = await apiForm<KnowledgeDocument>(
        "/knowledge/documents/",
        form,
      );
      setItems((old) => [document, ...old]);
      event.currentTarget.reset();
      onCountsChanged();
    } finally {
      setUploading(false);
    }
  }

  async function open(document: KnowledgeDocument) {
    setSelected(document);
    setAiOutput("");
    const [blob, marks, extracted] = await Promise.all([
      apiBlob(`/knowledge/documents/${document.id}/content/?preview=true`),
      api<DocumentHighlight[]>(
        `/knowledge/documents/${document.id}/highlights/`,
      ),
      api<{ text: string }>(`/knowledge/documents/${document.id}/text/`),
    ]);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(URL.createObjectURL(blob));
    setHighlights(marks);
    setExtractedText(extracted.text);
  }

  async function addHighlight(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const form = new FormData(event.currentTarget);
    const mark = await api<DocumentHighlight>(
      `/knowledge/documents/${selected.id}/highlights/`,
      {
        method: "POST",
        body: JSON.stringify({
          page_number: Number(form.get("page")) || 1,
          quote: form.get("quote"),
          annotation: form.get("annotation"),
        }),
      },
    );
    setHighlights((old) => [...old, mark]);
    event.currentTarget.reset();
  }

  async function aiAction(action: string) {
    if (!selected) return;
    setAiOutput("Generating…");
    try {
      const result = await api<{ content: string }>("/knowledge/ai-actions/", {
        method: "POST",
        body: JSON.stringify({
          source_type: "document",
          source_id: selected.id,
          action,
        }),
      });
      setAiOutput(result.content);
    } catch (reason) {
      setAiOutput(
        reason instanceof Error ? reason.message : "AI request failed.",
      );
    }
  }

  async function remove(document: KnowledgeDocument) {
    if (!confirm(`Delete “${document.title}”?`)) return;
    await api(`/knowledge/documents/${document.id}/`, { method: "DELETE" });
    setItems((old) => old.filter((item) => item.id !== document.id));
    if (selected?.id === document.id) setSelected(null);
    onCountsChanged();
  }

  const visible = folderId
    ? items.filter((item) => item.folder_id === folderId)
    : items;
  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_420px]">
      <section>
        <form
          onSubmit={upload}
          className="flex flex-col items-center rounded-2xl border-2 border-dashed border-indigo-200 bg-indigo-50/50 p-6 text-center dark:border-indigo-900 dark:bg-indigo-950/20"
        >
          <Upload className="text-indigo-500" />
          <p className="mt-2 text-sm font-black">Upload knowledge files</p>
          <p className="mt-1 text-xs text-slate-500">
            PDF, DOCX, TXT, Markdown, PPTX, PNG, JPG or WebP · max 25 MB ·{" "}
            {folders.length} folders
          </p>
          <input
            name="file"
            type="file"
            required
            accept=".pdf,.docx,.txt,.md,.markdown,.pptx,.png,.jpg,.jpeg,.webp"
            className="mt-4 max-w-full text-xs"
          />
          <button
            disabled={uploading}
            className="mt-4 flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-bold text-white disabled:opacity-50"
          >
            {uploading && <LoaderCircle size={14} className="animate-spin" />}{" "}
            Upload securely
          </button>
        </form>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {visible.map((document) => {
            const Icon = fileIcon(document.mime_type);
            return (
              <article
                key={document.id}
                className="group rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900"
              >
                <div className="flex items-start justify-between">
                  <span className="grid size-10 place-items-center rounded-xl bg-blue-50 text-blue-600 dark:bg-blue-950">
                    <Icon size={19} />
                  </span>
                  <div className="flex gap-1">
                    {document.is_favorite && (
                      <Star
                        size={14}
                        className="text-amber-500"
                        fill="currentColor"
                      />
                    )}
                    <button
                      onClick={() => void remove(document)}
                      className="text-slate-300 opacity-0 hover:text-rose-600 group-hover:opacity-100"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
                <button
                  onClick={() => void open(document)}
                  className="mt-4 block w-full text-left"
                >
                  <h3 className="truncate text-sm font-black">
                    {document.title}
                  </h3>
                  <p className="mt-1 truncate text-[10px] text-slate-400">
                    {document.original_filename}
                  </p>
                  <div className="mt-3 flex items-center justify-between text-[9px]">
                    <span
                      className={`rounded-full px-2 py-1 font-bold ${document.status === "ready" ? "bg-emerald-50 text-emerald-700" : document.status === "failed" ? "bg-rose-50 text-rose-700" : "bg-amber-50 text-amber-700"}`}
                    >
                      {document.status}
                    </span>
                    <span className="text-slate-400">
                      {(document.size_bytes / 1024).toFixed(0)} KB
                    </span>
                  </div>
                </button>
              </article>
            );
          })}
        </div>
      </section>
      <aside className="min-h-96 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
        {selected ? (
          <>
            <div className="flex items-start justify-between">
              <div className="min-w-0">
                <h3 className="truncate font-black">{selected.title}</h3>
                <p className="text-[10px] text-slate-400">
                  {selected.mime_type}
                </p>
              </div>
              <a
                href={previewUrl}
                download={selected.original_filename}
                className="grid size-9 place-items-center rounded-lg border border-slate-200 dark:border-slate-700"
              >
                <Download size={15} />
              </a>
            </div>
            {previewUrl &&
              (selected.mime_type.startsWith("image/") ? (
                <img
                  src={previewUrl}
                  alt={selected.title}
                  className="mt-4 max-h-80 w-full rounded-xl object-contain"
                />
              ) : selected.mime_type === "application/pdf" ||
                selected.mime_type.startsWith("text/") ? (
                <iframe
                  src={previewUrl}
                  title={selected.title}
                  className="mt-4 h-80 w-full rounded-xl border border-slate-200 dark:border-slate-700"
                />
              ) : (
                  <pre className="mt-4 max-h-80 overflow-auto whitespace-pre-wrap rounded-xl bg-slate-50 p-4 text-xs leading-5 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                    {extractedText ||
                      "Text extraction is still processing. Open this document again shortly."}
                  </pre>
              ))}
            <div className="mt-4 flex flex-wrap gap-2">
              {[
                "summary",
                "flashcards",
                "interview",
                "revision",
                "explain",
              ].map((action) => (
                <button
                  key={action}
                  onClick={() => void aiAction(action)}
                  className="rounded-lg bg-violet-50 px-2 py-1.5 text-[9px] font-bold capitalize text-violet-700 dark:bg-violet-950 dark:text-violet-300"
                >
                  <Bot size={11} className="mr-1 inline" />
                  {action}
                </button>
              ))}
            </div>
            {aiOutput && (
              <pre className="mt-3 max-h-52 overflow-auto whitespace-pre-wrap rounded-xl bg-violet-50 p-3 text-[10px] leading-5 dark:bg-violet-950/30">
                {aiOutput}
              </pre>
            )}
            <form
              onSubmit={addHighlight}
              className="mt-5 border-t border-slate-100 pt-4 dark:border-slate-800"
            >
              <p className="flex items-center gap-2 text-xs font-black">
                <Highlighter size={14} /> Save highlight
              </p>
              <div className="mt-2 grid grid-cols-[60px_1fr] gap-2">
                <input
                  name="page"
                  type="number"
                  min="1"
                  defaultValue="1"
                  className="rounded-lg border border-slate-200 bg-transparent p-2 text-xs dark:border-slate-700"
                />
                <input
                  name="quote"
                  required
                  placeholder="Highlighted text"
                  className="rounded-lg border border-slate-200 bg-transparent p-2 text-xs dark:border-slate-700"
                />
              </div>
              <input
                name="annotation"
                placeholder="Your annotation"
                className="mt-2 w-full rounded-lg border border-slate-200 bg-transparent p-2 text-xs dark:border-slate-700"
              />
              <button className="mt-2 rounded-lg bg-slate-900 px-3 py-2 text-[10px] font-bold text-white dark:bg-slate-700">
                Save highlight
              </button>
            </form>
            <div className="mt-3 space-y-2">
              {highlights.map((mark) => (
                <blockquote
                  key={mark.id}
                  className="rounded-lg border-l-4 border-amber-300 bg-amber-50 p-2 text-[10px] text-amber-950"
                >
                  <strong>Page {mark.page_number}</strong> · {mark.quote}
                  {mark.annotation && (
                    <p className="mt-1 text-slate-500">{mark.annotation}</p>
                  )}
                </blockquote>
              ))}
            </div>
          </>
        ) : (
          <div className="grid h-full min-h-80 place-items-center text-center">
            <div>
              <FileText className="mx-auto text-slate-300" size={38} />
              <p className="mt-3 text-xs text-slate-400">
                Select a document to preview,
                <br />
                highlight, download, or use AI.
              </p>
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}
