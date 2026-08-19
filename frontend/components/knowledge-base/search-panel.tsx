"use client";

import { Bot, FileSearch, LoaderCircle, Search, Sparkles } from "lucide-react";
import { FormEvent, useState } from "react";

import { api } from "@/lib/api";
import type { KnowledgeSearchResult } from "@/lib/types";
import { MarkdownPreview } from "./markdown-preview";

export function SearchPanel({
  semanticAvailable,
}: {
  semanticAvailable: boolean;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<KnowledgeSearchResult[]>([]);
  const [mode, setMode] = useState("");
  const [answer, setAnswer] = useState("");
  const [citations, setCitations] = useState<KnowledgeSearchResult[]>([]);
  const [busy, setBusy] = useState<"search" | "ask" | "">("");

  async function search(event: FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    setBusy("search");
    setAnswer("");
    try {
      const response = await api<{
        mode: string;
        results: KnowledgeSearchResult[];
      }>("/knowledge/search/", {
        method: "POST",
        body: JSON.stringify({ query }),
      });
      setResults(response.results);
      setMode(response.mode);
    } finally {
      setBusy("");
    }
  }
  async function ask() {
    if (!query.trim()) return;
    setBusy("ask");
    setAnswer("");
    try {
      const response = await api<{
        answer: string;
        citations: KnowledgeSearchResult[];
      }>("/knowledge/ask/", {
        method: "POST",
        body: JSON.stringify({ question: query }),
      });
      setAnswer(response.answer);
      setCitations(response.citations);
    } catch (reason) {
      setAnswer(
        reason instanceof Error
          ? reason.message
          : "Knowledge AI request failed.",
      );
      setCitations([]);
    } finally {
      setBusy("");
    }
  }
  return (
    <div className="mx-auto max-w-5xl">
      <section className="overflow-hidden rounded-3xl bg-slate-950 p-6 text-white shadow-xl sm:p-8">
        <div className="flex items-center gap-3">
          <span className="grid size-11 place-items-center rounded-2xl bg-violet-500/20 text-violet-300">
            <Bot size={22} />
          </span>
          <div>
            <h2 className="text-xl font-black">Ask your knowledge</h2>
            <p className="text-xs text-slate-400">
              Grounded only in your private notes and documents
            </p>
          </div>
        </div>
        <form
          onSubmit={search}
          className="mt-6 flex flex-col gap-2 sm:flex-row"
        >
          <label className="flex flex-1 items-center gap-2 rounded-xl bg-white/10 px-4">
            <Search size={17} className="text-slate-400" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="What did I learn about JWT authentication?"
              className="w-full bg-transparent py-4 text-sm outline-none placeholder:text-slate-500"
            />
          </label>
          <button
            disabled={Boolean(busy)}
            className="rounded-xl bg-white px-5 py-3 text-xs font-black text-slate-950 disabled:opacity-50"
          >
            {busy === "search" ? "Searching…" : "Search"}
          </button>
          <button
            type="button"
            onClick={() => void ask()}
            disabled={Boolean(busy)}
            className="flex items-center justify-center gap-2 rounded-xl bg-violet-600 px-5 py-3 text-xs font-black disabled:opacity-50"
          >
            {busy === "ask" ? (
              <LoaderCircle size={14} className="animate-spin" />
            ) : (
              <Sparkles size={14} />
            )}{" "}
            Ask AI
          </button>
        </form>
        <p className="mt-3 text-[10px] text-slate-500">
          {semanticAvailable
            ? "Hybrid keyword + pgvector semantic retrieval is available."
            : "Keyword search is available. Configure the AI key to enable embeddings and grounded answers."}
        </p>
      </section>
      {answer && (
        <section className="mt-5 rounded-2xl border border-violet-200 bg-white p-5 shadow-sm dark:border-violet-900 dark:bg-slate-900">
          <p className="flex items-center gap-2 text-xs font-black text-violet-700 dark:text-violet-300">
            <Sparkles size={15} /> Grounded answer
          </p>
          <div className="mt-3">
            <MarkdownPreview content={answer} />
          </div>
          {citations.length > 0 && (
            <div className="mt-5 border-t border-slate-100 pt-4 dark:border-slate-800">
              <p className="text-[10px] font-black uppercase tracking-wider text-slate-400">
                Sources
              </p>
              <div className="mt-2 grid gap-2 sm:grid-cols-2">
                {citations.map((item, index) => (
                  <article
                    key={item.id}
                    className="rounded-xl bg-slate-50 p-3 text-xs dark:bg-slate-800"
                  >
                    <strong>
                      [S{index + 1}] {item.title}
                    </strong>
                    <p className="mt-1 line-clamp-2 text-[10px] text-slate-500">
                      {item.excerpt}
                    </p>
                  </article>
                ))}
              </div>
            </div>
          )}
        </section>
      )}
      <div className="mt-5 flex items-center justify-between">
        <h3 className="text-sm font-black">Search results</h3>
        {mode && (
          <span className="rounded-full bg-indigo-50 px-2 py-1 text-[9px] font-bold uppercase text-indigo-700">
            {mode}
          </span>
        )}
      </div>
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        {results.map((item) => (
          <article
            key={item.id}
            className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="flex items-start gap-3">
              <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950">
                <FileSearch size={16} />
              </span>
              <div className="min-w-0">
                <p className="text-[9px] font-black uppercase tracking-wider text-indigo-600">
                  {item.source_type}
                </p>
                <h4 className="truncate text-sm font-black">{item.title}</h4>
              </div>
            </div>
            <p className="mt-3 line-clamp-4 text-xs leading-5 text-slate-500">
              {item.excerpt}
            </p>
          </article>
        ))}
      </div>
    </div>
  );
}
