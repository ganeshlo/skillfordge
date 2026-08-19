"use client";

import { FormEvent, useState } from "react";
import { Braces, LoaderCircle, X } from "lucide-react";
import { api } from "@/lib/api";
import type { CodingProjectDetail } from "@/lib/types";

const languages = ["python", "javascript", "typescript", "react", "html", "java", "go", "rust", "cpp", "sql"];

export function CreateProjectDialog({ open, onClose, onCreated }: { open: boolean; onClose: () => void; onCreated: (project: CodingProjectDetail) => void }) {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  if (!open) return null;
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setLoading(true); setError("");
    const form = new FormData(event.currentTarget);
    try { const project = await api<CodingProjectDetail>("/coding/projects/", { method: "POST", body: JSON.stringify({ name: form.get("name"), description: form.get("description"), primary_language: form.get("language"), include_starter: true }) }); onCreated(project); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not create project"); }
    finally { setLoading(false); }
  }
  return <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/45 p-4 backdrop-blur-sm" role="dialog" aria-modal="true"><div className="w-full max-w-lg overflow-hidden rounded-3xl bg-white shadow-2xl"><header className="flex items-start justify-between border-b border-slate-100 p-6"><div className="flex gap-3"><span className="grid size-11 place-items-center rounded-xl bg-violet-50 text-violet-600"><Braces size={21} /></span><div><h2 className="font-black">Create coding project</h2><p className="mt-1 text-xs text-slate-500">A starter file is created for your language.</p></div></div><button onClick={onClose} aria-label="Close" className="grid size-9 place-items-center rounded-lg text-slate-400 hover:bg-slate-100"><X size={18} /></button></header><form onSubmit={submit}><div className="grid gap-4 p-6"><div className="grid-field"><label htmlFor="project-name">Project name</label><input id="project-name" name="name" required maxLength={160} autoFocus placeholder="Algorithm practice" /></div><div className="grid-field"><label htmlFor="project-description">Description</label><textarea id="project-description" name="description" rows={3} placeholder="What are you building or practicing?" /></div><div className="grid-field"><label htmlFor="project-language">Primary language</label><select id="project-language" name="language" defaultValue="python">{languages.map(language => <option key={language} value={language}>{language[0].toUpperCase() + language.slice(1)}</option>)}</select></div>{error && <p className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}</div><footer className="flex justify-end gap-2 border-t border-slate-100 bg-slate-50 px-6 py-4"><button type="button" onClick={onClose} className="px-4 py-2.5 text-sm font-bold text-slate-500">Cancel</button><button disabled={loading} className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2.5 text-sm font-bold text-white shadow-lg shadow-violet-200 disabled:opacity-50">{loading && <LoaderCircle className="animate-spin" size={16} />} Create project</button></footer></form></div></div>;
}

