"use client";

import { ArrowRight, Clock3, Compass, Map, Plus, Search, Shield, Target } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { CreateRoadmapDialog } from "@/components/roadmaps/create-roadmap-dialog";
import { RoadmapAppLayout } from "@/components/roadmaps/app-layout";
import { api } from "@/lib/api";
import type { RoadmapSummary, User } from "@/lib/types";

function formatHours(minutes: number) { return minutes ? `${Math.round(minutes / 60)}h` : "Not estimated"; }

export default function RoadmapsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [roadmaps, setRoadmaps] = useState<RoadmapSummary[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    try { const [me, items] = await Promise.all([api<User>("/me/"), api<RoadmapSummary[]>("/roadmaps/")]); setUser(me); setRoadmaps(items); setError(""); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load roadmaps"); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { const task = window.setTimeout(() => void load(), 0); return () => clearTimeout(task); }, [load]);
  const filtered = useMemo(() => roadmaps.filter(item => `${item.title} ${item.career_goal}`.toLowerCase().includes(query.toLowerCase())), [query, roadmaps]);

  return <RoadmapAppLayout user={user}><div className="mx-auto max-w-7xl p-5 pb-12 sm:p-8"><div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end"><div><div className="flex items-center gap-2 text-xs font-black uppercase tracking-[.15em] text-indigo-600"><span className="h-px w-5 bg-indigo-500" /> My learning</div><h1 className="mt-3 text-3xl font-black tracking-[-.045em] text-slate-950 sm:text-4xl">Learning roadmaps</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">Break an ambitious goal into ordered phases, focused topics, useful resources, and visible evidence of progress.</p></div><button onClick={() => setCreating(true)} className="inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-indigo-200"><Plus size={17} /> Create roadmap</button></div>
    <section className="mt-8 grid gap-4 sm:grid-cols-3"><div className="rounded-2xl border border-slate-200 bg-white p-5"><span className="text-xs font-bold text-slate-500">Active roadmaps</span><strong className="mt-2 block text-3xl font-black">{roadmaps.filter(item => item.status === "active").length}</strong></div><div className="rounded-2xl border border-slate-200 bg-white p-5"><span className="text-xs font-bold text-slate-500">Topics completed</span><strong className="mt-2 block text-3xl font-black">{roadmaps.reduce((sum, item) => sum + item.completed_topic_count, 0)}</strong></div><div className="rounded-2xl border border-slate-200 bg-white p-5"><span className="text-xs font-bold text-slate-500">Total learning topics</span><strong className="mt-2 block text-3xl font-black">{roadmaps.reduce((sum, item) => sum + item.topic_count, 0)}</strong></div></section>
    <div className="mt-6 flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-3 sm:flex-row sm:items-center"><div className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={17} /><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search your roadmaps" className="w-full rounded-xl border-0 bg-slate-50 py-2.5 pl-10 pr-3 text-sm outline-none ring-indigo-100 focus:ring-2" /></div><div className="flex gap-2"><span className="rounded-lg bg-indigo-50 px-3 py-2 text-xs font-bold text-indigo-700">All roadmaps</span><span className="rounded-lg px-3 py-2 text-xs font-bold text-slate-400">Owned & shared</span></div></div>
    {error && <p className="mt-5 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
    {loading ? <div className="mt-6 grid animate-pulse gap-4 md:grid-cols-2 xl:grid-cols-3">{[1,2,3].map(item => <div key={item} className="h-64 rounded-2xl bg-white ring-1 ring-slate-200" />)}</div> : filtered.length ? <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{filtered.map(roadmap => <Link href={`/roadmaps/${roadmap.id}`} key={roadmap.id} className="group overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-xl hover:shadow-indigo-100/50"><div className="h-1.5 bg-gradient-to-r from-indigo-500 via-blue-500 to-violet-500" /><div className="p-5"><div className="flex items-start justify-between gap-3"><span className="grid size-11 place-items-center rounded-xl bg-indigo-50 text-indigo-600"><Map size={21} /></span><span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-1 text-[9px] font-black uppercase text-slate-500">{roadmap.visibility === "private" && <Shield size={10} />} {roadmap.visibility}</span></div><h2 className="mt-5 text-lg font-black tracking-tight group-hover:text-indigo-700">{roadmap.title}</h2><p className="mt-2 line-clamp-2 min-h-10 text-xs leading-5 text-slate-500">{roadmap.description || roadmap.career_goal || "Add a description to clarify the outcome of this roadmap."}</p><div className="mt-5"><div className="flex justify-between text-[10px] font-bold text-slate-500"><span>{roadmap.completed_topic_count} of {roadmap.topic_count} topics</span><span>{roadmap.progress_percentage}%</span></div><div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-indigo-600" style={{ width: `${roadmap.progress_percentage}%` }} /></div></div><div className="mt-5 grid grid-cols-3 gap-2 border-t border-slate-100 pt-4 text-[10px] text-slate-500"><span className="flex items-center gap-1"><Clock3 size={12} /> {formatHours(roadmap.estimated_minutes)}</span><span className="flex items-center gap-1"><Target size={12} /> {roadmap.status}</span><span className="flex items-center justify-end gap-1 text-indigo-600">Open <ArrowRight size={12} /></span></div></div></Link>)}</section> : <section className="mt-6 rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center"><span className="mx-auto grid size-16 place-items-center rounded-2xl bg-indigo-50 text-indigo-600"><Compass size={28} /></span><h2 className="mt-5 text-xl font-black">{query ? "No matching roadmaps" : "Create your first roadmap"}</h2><p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">{query ? "Try a different title or career goal." : "Start with a learning destination, then organize it into phases, modules, and focused topics."}</p>{!query && <button onClick={() => setCreating(true)} className="mt-5 inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-bold text-white"><Plus size={17} /> Create roadmap</button>}</section>}
    <CreateRoadmapDialog open={creating} onClose={() => setCreating(false)} onCreated={roadmap => { setCreating(false); router.push(`/roadmaps/${roadmap.id}`); }} /></div></RoadmapAppLayout>;
}
