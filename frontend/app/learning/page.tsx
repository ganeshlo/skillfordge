"use client";

import { ArrowRight, BookOpenCheck, CheckCircle2, Clock3, Compass, Goal, Target } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { AppLayout } from "@/components/app-layout";
import { api } from "@/lib/api";
import type { LearningAnalytics, LearningGoal, RoadmapSummary, User } from "@/lib/types";

export default function MyLearningPage() {
  const [user, setUser] = useState<User | null>(null);
  const [roadmaps, setRoadmaps] = useState<RoadmapSummary[]>([]);
  const [goals, setGoals] = useState<LearningGoal[]>([]);
  const [analytics, setAnalytics] = useState<LearningAnalytics | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { void Promise.all([api<User>("/me/"), api<RoadmapSummary[]>("/roadmaps/"), api<LearningGoal[]>("/goals/"), api<LearningAnalytics>("/analytics/")]).then(([me, maps, goalItems, metrics]) => { setUser(me); setRoadmaps(maps); setGoals(goalItems); setAnalytics(metrics); }).catch(reason => setError(reason instanceof Error ? reason.message : "Could not load your learning workspace")); }, []);
  const activeRoadmaps = useMemo(() => roadmaps.filter(item => item.status === "active").sort((a, b) => b.progress_percentage - a.progress_percentage), [roadmaps]);
  const activeGoals = goals.filter(item => item.status !== "completed" && item.status !== "paused").slice(0, 3);
  const weeklyPercent = analytics && user ? Math.min(100, Math.round(analytics.overview.weekly_study_minutes / Math.max(1, user.profile.weekly_target_minutes) * 100)) : 0;

  return <AppLayout user={user} currentPath="/learning"><div className="mx-auto max-w-7xl p-5 pb-12 sm:p-8">
    <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><p className="text-xs font-black uppercase tracking-[.15em] text-indigo-600">Your command center</p><h1 className="mt-3 text-3xl font-black tracking-[-.045em] text-slate-950 sm:text-4xl">My learning</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">One view of what you are learning, why it matters, and the next useful action.</p></div><Link href="/study" className="inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-bold text-white">Start studying <ArrowRight size={16} /></Link></div>
    {error && <p className="mt-5 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
    <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><Summary icon={Clock3} label="This week" value={`${analytics?.overview.weekly_study_minutes ?? 0} min`} detail={`${weeklyPercent}% of weekly target`} /><Summary icon={CheckCircle2} label="Topics complete" value={`${analytics?.overview.completed_topics ?? 0}/${analytics?.overview.total_topics ?? 0}`} detail="Across your roadmaps" /><Summary icon={Compass} label="Active roadmaps" value={String(analytics?.overview.active_roadmaps ?? 0)} detail="Structured learning paths" /><Summary icon={Goal} label="Open goals" value={String(activeGoals.length)} detail="Outcomes in progress" /></section>
    <section className="mt-6 grid gap-6 xl:grid-cols-[1.35fr_.65fr]"><article className="rounded-2xl border border-slate-200 bg-white p-6"><div className="flex items-center justify-between"><div><h2 className="font-black">Continue learning</h2><p className="mt-1 text-xs text-slate-500">Your active paths, ordered by progress.</p></div><Link href="/roadmaps" className="text-xs font-bold text-indigo-600">All roadmaps</Link></div><div className="mt-5 grid gap-3">{activeRoadmaps.length ? activeRoadmaps.slice(0, 4).map(item => <Link href={`/roadmaps/${item.id}`} key={item.id} className="group rounded-xl border border-slate-100 p-4 hover:border-indigo-200 hover:bg-indigo-50/30"><div className="flex items-start justify-between gap-4"><div><strong className="text-sm group-hover:text-indigo-700">{item.title}</strong><p className="mt-1 line-clamp-1 text-xs text-slate-500">{item.career_goal || item.description}</p></div><span className="text-sm font-black text-indigo-600">{item.progress_percentage}%</span></div><div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-indigo-600" style={{ width: `${item.progress_percentage}%` }} /></div><p className="mt-2 text-[10px] text-slate-400">{item.completed_topic_count} of {item.topic_count} topics completed</p></Link>) : <Empty icon={BookOpenCheck} title="No active roadmap" action="Create roadmap" href="/roadmaps" />}</div></article>
      <article className="rounded-2xl border border-slate-200 bg-white p-6"><div className="flex items-center justify-between"><div><h2 className="font-black">Priority goals</h2><p className="mt-1 text-xs text-slate-500">Keep outcomes connected to work.</p></div><Link href="/goals" className="text-xs font-bold text-indigo-600">Manage</Link></div><div className="mt-5 grid gap-3">{activeGoals.length ? activeGoals.map(goal => <Link href="/goals" key={goal.id} className="rounded-xl bg-slate-50 p-4"><div className="flex justify-between gap-3"><strong className="text-xs text-slate-800">{goal.title}</strong><span className="text-[10px] font-bold uppercase text-indigo-600">{goal.priority}</span></div><div className="mt-3 h-1.5 rounded-full bg-slate-200"><div className="h-full rounded-full bg-emerald-500" style={{ width: `${goal.progress_percentage}%` }} /></div><p className="mt-2 text-[10px] text-slate-400">{goal.current_value} / {goal.target_value} {goal.unit}</p></Link>) : <Empty icon={Target} title="No active goals" action="Set a goal" href="/goals" />}</div></article></section>
  </div></AppLayout>;
}

function Summary({ icon: Icon, label, value, detail }: { icon: typeof Clock3; label: string; value: string; detail: string }) { return <article className="rounded-2xl border border-slate-200 bg-white p-5"><Icon size={18} className="text-indigo-600" /><strong className="mt-3 block text-2xl font-black">{value}</strong><span className="text-xs font-bold text-slate-600">{label}</span><p className="mt-1 text-[10px] text-slate-400">{detail}</p></article>; }
function Empty({ icon: Icon, title, action, href }: { icon: typeof Goal; title: string; action: string; href: string }) { return <div className="rounded-xl border border-dashed border-slate-200 p-7 text-center"><Icon className="mx-auto text-slate-300" /><p className="mt-2 text-xs text-slate-500">{title}</p><Link href={href} className="mt-2 inline-block text-xs font-bold text-indigo-600">{action}</Link></div>; }

