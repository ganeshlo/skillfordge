import {
  BookOpenText,
  Bot,
  Code2,
  FileStack,
  LayoutGrid,
  Plus,
  Video,
} from "lucide-react";

import type { KnowledgeFolder } from "@/lib/types";

export type KnowledgeView =
  "overview" | "notes" | "documents" | "snippets" | "videos" | "search";

const views = [
  ["overview", LayoutGrid, "Overview"],
  ["notes", BookOpenText, "Notes"],
  ["documents", FileStack, "Documents"],
  ["snippets", Code2, "Code snippets"],
  ["videos", Video, "Video notes"],
  ["search", Bot, "AI search"],
] as const;

export function WorkspaceNav({
  view,
  folders,
  selectedFolder,
  onView,
  onFolder,
  onNewFolder,
}: {
  view: KnowledgeView;
  folders: KnowledgeFolder[];
  selectedFolder: string | null;
  onView: (view: KnowledgeView) => void;
  onFolder: (id: string | null) => void;
  onNewFolder: () => void;
}) {
  return (
    <aside className="border-r border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900 lg:min-h-[calc(100vh-4rem)] lg:w-56 lg:p-4">
      <nav className="grid grid-cols-3 gap-1 lg:grid-cols-1">
        {views.map(([value, Icon, label]) => (
          <button
            key={value}
            onClick={() => onView(value)}
            className={`flex items-center gap-2 rounded-xl px-3 py-2.5 text-xs font-bold ${view === value ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300" : "text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-800"}`}
          >
            <Icon size={16} />
            <span className="truncate">{label}</span>
          </button>
        ))}
      </nav>
      <div className="mt-6 hidden lg:block">
        <div className="flex items-center justify-between px-2">
          <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">
            Folders
          </p>
          <button
            onClick={onNewFolder}
            className="grid size-7 place-items-center rounded-lg text-indigo-600 hover:bg-indigo-50"
            aria-label="New folder"
          >
            <Plus size={14} />
          </button>
        </div>
        <button
          onClick={() => onFolder(null)}
          className={`mt-2 w-full rounded-lg px-3 py-2 text-left text-xs font-semibold ${selectedFolder === null ? "bg-slate-100 dark:bg-slate-800" : "text-slate-500"}`}
        >
          All knowledge
        </button>
        <div className="mt-1 space-y-1">
          {folders.map((folder) => (
            <button
              key={folder.id}
              onClick={() => onFolder(folder.id)}
              className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-xs ${selectedFolder === folder.id ? "bg-slate-100 font-bold dark:bg-slate-800" : "text-slate-500"}`}
            >
              <span
                className="size-2 rounded-full"
                style={{ backgroundColor: folder.color }}
              />
              <span className="min-w-0 flex-1 truncate">{folder.name}</span>
              <span className="text-[9px] text-slate-400">
                {folder.item_count}
              </span>
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}
