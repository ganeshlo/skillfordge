import {
  BookOpenText,
  FileStack,
  FolderOpen,
  Sparkles,
  Star,
  Code2,
} from "lucide-react";

import type { KnowledgeDashboard } from "@/lib/types";
import type { KnowledgeView } from "./workspace-nav";

export function KnowledgeOverview({
  data,
  onView,
}: {
  data: KnowledgeDashboard;
  onView: (view: KnowledgeView) => void;
}) {
  const metrics = [
    [BookOpenText, "Notes", data.counts.notes, "notes"],
    [FileStack, "Documents", data.counts.documents, "documents"],
    [Code2, "Snippets", data.counts.snippets, "snippets"],
    [Star, "Favorites", data.counts.favorites, "notes"],
  ] as const;
  return (
    <div>
      <section className="overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-600 via-blue-600 to-violet-600 p-7 text-white shadow-xl shadow-indigo-200/50 dark:shadow-none">
        <div className="flex items-center gap-3">
          <span className="grid size-12 place-items-center rounded-2xl bg-white/15">
            <Sparkles size={23} />
          </span>
          <div>
            <p className="text-xs font-bold text-indigo-100">
              Your private knowledge system
            </p>
            <h2 className="mt-1 text-2xl font-black">
              Turn everything you learn into reusable knowledge.
            </h2>
          </div>
        </div>
        <p className="mt-4 max-w-2xl text-sm leading-6 text-indigo-100">
          Capture Markdown notes, organize files, save code, revisit video
          timestamps, and ask grounded questions with source citations.
        </p>
      </section>
      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map(([Icon, label, count, target]) => (
          <button
            key={label}
            onClick={() => onView(target)}
            className="rounded-2xl border border-slate-200 bg-white p-5 text-left shadow-sm hover:-translate-y-0.5 dark:border-slate-800 dark:bg-slate-900"
          >
            <Icon size={19} className="text-indigo-600" />
            <p className="mt-4 text-3xl font-black">{count}</p>
            <p className="text-xs text-slate-500">{label}</p>
          </button>
        ))}
      </div>
      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <section className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <h3 className="flex items-center gap-2 text-sm font-black">
            <BookOpenText size={16} className="text-indigo-600" /> Recent notes
          </h3>
          <div className="mt-3 space-y-2">
            {data.recent_notes.slice(0, 5).map((note) => (
              <button
                key={note.id}
                onClick={() => onView("notes")}
                className="block w-full rounded-xl bg-slate-50 p-3 text-left dark:bg-slate-800"
              >
                <p className="text-xs font-bold">{note.title}</p>
                <p className="mt-1 truncate text-[10px] text-slate-400">
                  {note.content.replace(/[#*_`]/g, "")}
                </p>
              </button>
            ))}
            {!data.recent_notes.length && (
              <p className="py-8 text-center text-xs text-slate-400">
                No notes yet.
              </p>
            )}
          </div>
        </section>
        <section className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <h3 className="flex items-center gap-2 text-sm font-black">
            <FolderOpen size={16} className="text-indigo-600" /> Knowledge
            organization
          </h3>
          <div className="mt-3 grid grid-cols-2 gap-2">
            {data.folders.slice(0, 6).map((folder) => (
              <div
                key={folder.id}
                className="rounded-xl border border-slate-100 p-3 dark:border-slate-800"
              >
                <span
                  className="block size-2 rounded-full"
                  style={{ backgroundColor: folder.color }}
                />
                <p className="mt-2 truncate text-xs font-bold">{folder.name}</p>
                <p className="text-[9px] text-slate-400">
                  {folder.item_count} items
                </p>
              </div>
            ))}
            {!data.folders.length && (
              <p className="col-span-2 py-8 text-center text-xs text-slate-400">
                Create folders for subjects, topics, or projects.
              </p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
