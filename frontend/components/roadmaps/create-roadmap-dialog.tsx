"use client";

import { FormEvent, useState } from "react";
import { LoaderCircle, Map, X } from "lucide-react";
import { api } from "@/lib/api";
import type { RoadmapSummary } from "@/lib/types";

export function CreateRoadmapDialog({ open, onClose, onCreated }: { open: boolean; onClose: () => void; onCreated: (roadmap: RoadmapSummary) => void }) {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  if (!open) return null;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setLoading(true);
    const form = new FormData(event.currentTarget);
    try {
      const roadmap = await api<RoadmapSummary>("/roadmaps/", { method: "POST", body: JSON.stringify({
        title: form.get("title"), career_goal: form.get("career_goal"), description: form.get("description"),
        visibility: form.get("visibility"), status: "active", target_deadline: form.get("target_deadline") || null,
        estimated_minutes: Number(form.get("estimated_hours") || 0) * 60,
      }) });
      onCreated(roadmap);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not create roadmap"); }
    finally { setLoading(false); }
  }

  return <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 p-4 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="create-roadmap-title"><div className="w-full max-w-xl overflow-hidden rounded-3xl bg-white shadow-2xl"><header className="flex items-start justify-between border-b border-slate-100 p-6"><div className="flex gap-3"><span className="grid size-11 place-items-center rounded-xl bg-indigo-50 text-indigo-600"><Map size={21} /></span><div><h2 id="create-roadmap-title" className="text-lg font-black tracking-tight">Create a learning roadmap</h2><p className="mt-1 text-xs text-slate-500">Start with the destination. Add phases and topics next.</p></div></div><button onClick={onClose} className="grid size-9 place-items-center rounded-lg text-slate-400 hover:bg-slate-100" aria-label="Close"><X size={18} /></button></header><form onSubmit={submit}><div className="grid gap-4 p-6"><div className="grid-field"><label htmlFor="roadmap-title">Roadmap title</label><input id="roadmap-title" name="title" required maxLength={180} placeholder="Full-Stack Engineer" autoFocus /></div><div className="grid-field"><label htmlFor="career-goal">Career or learning goal</label><input id="career-goal" name="career_goal" maxLength={160} placeholder="Become job-ready for a backend role" /></div><div className="grid-field"><label htmlFor="description">Description</label><textarea id="description" name="description" rows={3} placeholder="What this roadmap should help you accomplish" /></div><div className="grid gap-4 sm:grid-cols-3"><div className="grid-field"><label htmlFor="visibility">Visibility</label><select id="visibility" name="visibility"><option value="private">Private</option><option value="public">Public</option></select></div><div className="grid-field"><label htmlFor="deadline">Target date</label><input id="deadline" name="target_deadline" type="date" /></div><div className="grid-field"><label htmlFor="hours">Estimate (hours)</label><input id="hours" name="estimated_hours" type="number" min="0" max="10000" defaultValue="40" /></div></div>{error && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}</div><footer className="flex justify-end gap-2 border-t border-slate-100 bg-slate-50 px-6 py-4"><button type="button" onClick={onClose} className="rounded-xl px-4 py-2.5 text-sm font-bold text-slate-500">Cancel</button><button disabled={loading} className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-bold text-white shadow-lg shadow-indigo-200 disabled:opacity-60">{loading && <LoaderCircle className="animate-spin" size={16} />} Create roadmap</button></footer></form></div></div>;
}

