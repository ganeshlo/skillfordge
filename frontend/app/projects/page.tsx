"use client";

import { ArrowRight, Braces, FileCode2, FolderKanban, Plus } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { AppLayout } from "@/components/app-layout";
import { api } from "@/lib/api";
import type { CodingProjectSummary, User } from "@/lib/types";

export default function ProjectsPage() {
  const [user, setUser] = useState<User | null>(null); const [projects, setProjects] = useState<CodingProjectSummary[]>([]); const [error, setError] = useState("");
  useEffect(() => { void Promise.all([api<User>("/me/"), api<CodingProjectSummary[]>("/coding/projects/")]).then(([me, items]) => { setUser(me); setProjects(items); }).catch(reason => setError(reason instanceof Error ? reason.message : "Could not load projects")); }, []);
  return <AppLayout user={user} currentPath="/projects"><div className="mx-auto max-w-7xl p-5 pb-12 sm:p-8"><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="text-xs font-black uppercase tracking-[.15em] text-violet-600">Portfolio delivery</p><h1 className="mt-3 text-3xl font-black tracking-[-.045em]">Projects</h1><p className="mt-2 text-sm text-slate-500">Turn learning into working, versioned portfolio evidence.</p></div><Link href="/code" className="inline-flex items-center justify-center gap-2 rounded-xl bg-violet-600 px-4 py-3 text-sm font-bold text-white"><Plus size={16} /> New project</Link></div>{error && <p className="mt-5 rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
    <section className="mt-8 grid gap-4 sm:grid-cols-3"><Metric label="Projects" value={projects.length} /><Metric label="Versioned files" value={projects.reduce((sum, project) => sum + project.file_count, 0)} /><Metric label="Active" value={projects.filter(project => project.status === "active").length} /></section>
    <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{projects.map(project => <Link href={`/code/${project.id}`} key={project.id} className="group rounded-2xl border border-slate-200 bg-white p-5 hover:border-violet-200 hover:shadow-lg"><div className="flex justify-between"><span className="grid size-11 place-items-center rounded-xl bg-slate-950 text-violet-300"><Braces size={20} /></span><span className="rounded-full bg-violet-50 px-2 py-1 text-[9px] font-black uppercase text-violet-700">{project.primary_language}</span></div><h2 className="mt-5 font-black group-hover:text-violet-700">{project.name}</h2><p className="mt-2 line-clamp-2 min-h-10 text-xs leading-5 text-slate-500">{project.description || "Open the workspace and start building."}</p><div className="mt-5 flex justify-between border-t border-slate-100 pt-4 text-[10px] text-slate-400"><span className="flex items-center gap-1"><FileCode2 size={12} /> {project.file_count} files</span><span className="flex items-center gap-1 text-violet-600">Open workspace <ArrowRight size={12} /></span></div></Link>)}{!projects.length && <div className="col-span-full rounded-3xl border border-dashed border-slate-300 bg-white p-14 text-center"><FolderKanban className="mx-auto text-slate-300" size={32} /><h2 className="mt-4 font-black">Build your first portfolio project</h2><Link href="/code" className="mt-3 inline-block text-sm font-bold text-violet-600">Open code workspace</Link></div>}</section>
  </div></AppLayout>;
}
function Metric({ label, value }: { label: string; value: number }) { return <div className="rounded-2xl border border-slate-200 bg-white p-5"><FolderKanban size={17} className="text-violet-600" /><strong className="mt-3 block text-3xl font-black">{value}</strong><span className="text-xs text-slate-500">{label}</span></div>; }
