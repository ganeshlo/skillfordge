"use client";

import { ArrowRight, BookOpenCheck, Building2, CalendarClock, Check, CircleAlert, CircleCheck, Clock3, Code2, Compass, Flame, Gauge, Plus, RotateCcw, ShieldCheck, Sparkles, Target, UserRoundCheck } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { DashboardSidebar } from "@/components/dashboard/sidebar";
import { DashboardSkeleton } from "@/components/dashboard/skeleton";
import { DashboardTopbar } from "@/components/dashboard/topbar";
import { MetricCard } from "@/components/dashboard/metric-card";
import { api, saveAccessToken } from "@/lib/api";
import type { DashboardData, Organization } from "@/lib/types";

const moduleIcons = { identity: UserRoundCheck, roadmaps: Compass, study: Clock3, coding: Code2 };

function relativeTime(value: string) {
  const seconds = Math.floor((Date.now() - new Date(value).getTime()) / 1000);
  if (seconds < 60) return "Just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(new Date(value));
}

export default function DashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [navigationCollapsed, setNavigationCollapsed] = useState(false);
  const [creatingOrganization, setCreatingOrganization] = useState(false);

  const load = useCallback(async () => {
    try {
      const dashboard = await api<DashboardData>("/dashboard/");
      if (!dashboard.overview.onboarding_complete) { router.replace("/onboarding"); return; }
      setError("");
      setData(dashboard);
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : "Could not load your dashboard";
      if (/refresh|session|authentication|credential/i.test(message)) router.replace("/login");
      else setError(message);
    }
  }, [router]);

  useEffect(() => {
    const task = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(task);
  }, [load]);
  useEffect(() => {
    const task = window.setTimeout(() => setNavigationCollapsed(window.localStorage.getItem("learnos-navigation-collapsed") === "true"), 0);
    return () => window.clearTimeout(task);
  }, []);

  function changeNavigation(value: boolean) {
    setNavigationCollapsed(value);
    window.localStorage.setItem("learnos-navigation-collapsed", String(value));
  }

  async function logout() {
    try { await api("/auth/token/revoke/", { method: "POST" }); } catch { /* local session is still cleared */ }
    saveAccessToken(null); router.replace("/login");
  }

  async function createOrganization() {
    const name = window.prompt("Organization name");
    if (!name) return;
    setCreatingOrganization(true); setError("");
    try {
      await api<Organization>("/organizations/", { method: "POST", body: JSON.stringify({ name, slug: name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "") }) });
      await load();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not create organization"); }
    finally { setCreatingOrganization(false); }
  }

  const role = data?.overview.professional_role || data?.overview.experience_level || "Learner";
  const weeklyPercent = data ? Math.min(100, Math.round(data.learning_activity.weekly_minutes / Math.max(1, data.learning_activity.weekly_target_minutes) * 100)) : 0;
  const maxDailyMinutes = Math.max(1, ...(data?.learning_activity.days.map(day => day.minutes) ?? [1]));
  return (
    <main className="flex min-h-screen bg-slate-50 dark:bg-slate-950">
      <DashboardSidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} onLogout={logout} currentPath="/dashboard" collapsed={navigationCollapsed} onCollapsedChange={changeNavigation} />
      <section className="min-w-0 flex-1">
        <DashboardTopbar fullName={data?.overview.full_name ?? ""} role={role} onMenu={() => setSidebarOpen(true)} />
        {!data && !error && <DashboardSkeleton />}
        {error && !data && <div className="mx-auto grid min-h-[70vh] max-w-lg place-items-center p-6 text-center"><div><span className="mx-auto grid size-14 place-items-center rounded-2xl bg-rose-50 text-rose-600"><CircleAlert /></span><h1 className="mt-5 text-xl font-black">Dashboard unavailable</h1><p className="mt-2 text-sm leading-6 text-slate-500">{error}</p><button onClick={() => void load()} className="mt-5 inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-bold text-white"><RotateCcw size={16} /> Try again</button></div></div>}
        {data && <div className="mx-auto max-w-7xl p-5 pb-12 sm:p-8">
          {error && <div role="alert" className="mb-5 flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700"><CircleAlert size={17} />{error}</div>}
          <section className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
            <div><div className="flex items-center gap-2 text-xs font-black uppercase tracking-[.15em] text-indigo-600"><span className="h-px w-5 bg-indigo-500" /> Personal learning workspace</div><h1 className="mt-3 text-3xl font-black tracking-[-.045em] text-slate-950 sm:text-4xl">Good to see you, {data.overview.first_name}.</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">{data.overview.career_goal ? <>Your destination is <strong className="font-bold text-slate-700">{data.overview.career_goal}</strong>. LearnOS will keep each next step connected to that goal.</> : "Complete your profile so LearnOS can shape the workspace around your goal."}</p></div>
            <div className="flex gap-2"><button onClick={createOrganization} disabled={creatingOrganization} className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-700 hover:border-indigo-200 hover:text-indigo-700 disabled:opacity-50"><Building2 size={17} /> <span className="hidden sm:inline">Organization</span></button><Link href="/roadmaps" className="inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-indigo-200"><Plus size={17} /> Create roadmap</Link></div>
          </section>

          <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Learning summary">
            <MetricCard icon={CalendarClock} label="Weekly study target" value={`${data.targets.weekly_target_minutes} min`} detail={`${data.targets.daily_minutes} minutes planned each day`} tone="indigo" />
            <MetricCard icon={Target} label="Target skills" value={String(data.targets.target_skills.length)} detail={data.targets.target_skills.join(", ") || "Add skills in your profile"} tone="blue" />
            <MetricCard icon={Building2} label="Organizations" value={String(data.organization_count)} detail={data.organization_count ? "Active tenant memberships" : "Personal workspace only"} tone="violet" />
            <MetricCard icon={Gauge} label="Profile readiness" value={`${data.overview.profile_completion}%`} detail={data.overview.email_verified ? "Profile and email verified" : "Email verification still required"} tone="emerald" />
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-[1.45fr_.8fr]">
            <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm shadow-slate-200/40">
              <div className="learnos-gradient relative overflow-hidden p-6 text-white sm:p-7"><div className="absolute -right-16 -top-24 size-64 rounded-full border border-white/15" /><span className="relative inline-flex items-center gap-1.5 rounded-full bg-white/15 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider"><Sparkles size={12} /> Recommended next action</span><h2 className="relative mt-4 max-w-lg text-2xl font-black tracking-[-.035em]">{data.next_action.title}</h2><p className="relative mt-2 max-w-xl text-sm leading-6 text-indigo-100">{data.next_action.description}</p>{data.next_action.available ? <Link href={data.next_action.href} className="relative mt-5 inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-bold text-indigo-700 shadow-lg">{data.next_action.label} <ArrowRight size={16} /></Link> : <button disabled className="relative mt-5 inline-flex items-center gap-2 rounded-xl bg-white/15 px-4 py-2.5 text-sm font-bold text-white"><Compass size={16} /> {data.next_action.label}</button>}</div>
              <div className="grid gap-4 p-6 sm:grid-cols-3"><div><span className="text-[10px] font-black uppercase tracking-wider text-slate-400">Current level</span><strong className="mt-1 block text-sm capitalize text-slate-800">{data.overview.experience_level || "Not set"}</strong></div><div><span className="text-[10px] font-black uppercase tracking-wider text-slate-400">Preferred languages</span><strong className="mt-1 block truncate text-sm text-slate-800">{data.targets.preferred_languages.join(", ") || "Not set"}</strong></div><div><span className="text-[10px] font-black uppercase tracking-wider text-slate-400">Privacy</span><strong className="mt-1 flex items-center gap-1.5 text-sm text-slate-800"><ShieldCheck size={15} className="text-emerald-600" /> Private by default</strong></div></div>
            </article>

            <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/40"><div className="flex items-center justify-between"><div><h2 className="font-extrabold tracking-tight">Weekly focus</h2><p className="mt-1 text-xs text-slate-500">Focused minutes recorded in Study Workspace.</p></div><span className="grid size-10 place-items-center rounded-xl bg-amber-50 text-amber-600"><Flame size={19} /></span></div><div className="mt-6 flex items-center gap-5"><div className="relative grid size-24 shrink-0 place-items-center rounded-full" style={{ background: `conic-gradient(#4f46e5 ${weeklyPercent * 3.6}deg, #e2e8f0 0deg)` }}><div className="grid size-[4.8rem] place-items-center rounded-full bg-white text-center"><strong className="text-xl font-black">{weeklyPercent}%</strong><span className="-mt-2 text-[9px] text-slate-400">this week</span></div></div><div><strong className="text-2xl font-black">{data.learning_activity.weekly_minutes} <span className="text-sm font-bold text-slate-400">/ {data.targets.weekly_target_minutes}</span></strong><p className="mt-1 text-xs leading-5 text-slate-500">{data.learning_activity.weekly_minutes ? "Keep the streak moving with another focused session." : "Start a focused session to build your activity record."}</p></div></div><div className="mt-6 grid grid-cols-7 gap-1.5">{data.learning_activity.days.map((day, index) => <div key={day.date} className="text-center"><span title={`${day.minutes} minutes`} className="mx-auto block h-12 rounded-lg bg-indigo-100" style={{ opacity: day.minutes ? Math.max(.25, day.minutes / maxDailyMinutes) : .15 }} /><small className="mt-1.5 block text-[9px] font-bold text-slate-400">{["M","T","W","T","F","S","S"][index]}</small></div>)}</div></article>
          </section>

          <section className="mt-6 grid gap-6 lg:grid-cols-[1.15fr_.85fr]">
            <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/40"><div className="flex items-center justify-between"><div><h2 className="font-extrabold tracking-tight">LearnOS modules</h2><p className="mt-1 text-xs text-slate-500">Built in secure, testable increments.</p></div><BookOpenCheck size={20} className="text-indigo-600" /></div><div className="mt-5 grid gap-3 sm:grid-cols-2">{data.modules.map(module => { const Icon = moduleIcons[module.key as keyof typeof moduleIcons] ?? BookOpenCheck; return <div key={module.key} className={`rounded-xl border p-4 ${module.status === "ready" ? "border-emerald-200 bg-emerald-50/40" : module.status === "next" ? "border-blue-200 bg-blue-50/40" : "border-slate-100 bg-slate-50/60"}`}><div className="flex items-start justify-between"><span className={`grid size-9 place-items-center rounded-lg ${module.status === "ready" ? "bg-emerald-100 text-emerald-700" : module.status === "next" ? "bg-blue-100 text-blue-700" : "bg-slate-200/60 text-slate-400"}`}><Icon size={17} /></span><span className={`rounded-full px-2 py-1 text-[8px] font-black uppercase tracking-wider ${module.status === "ready" ? "bg-emerald-100 text-emerald-700" : module.status === "next" ? "bg-blue-100 text-blue-700" : "bg-slate-200/60 text-slate-400"}`}>{module.status}</span></div><strong className="mt-3 block text-sm">{module.label}</strong><p className="mt-1 text-[11px] leading-5 text-slate-500">{module.description}</p></div>; })}</div></article>

            <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-200/40"><div className="flex items-center justify-between"><div><h2 className="font-extrabold tracking-tight">Recent activity</h2><p className="mt-1 text-xs text-slate-500">Security-aware workspace events.</p></div><Clock3 size={19} className="text-slate-400" /></div>{data.recent_activity.length ? <div className="mt-5 grid gap-1">{data.recent_activity.map((event, index) => <div key={event.id} className="relative flex gap-3 py-2.5">{index < data.recent_activity.length - 1 && <span className="absolute left-[.68rem] top-8 h-[calc(100%-1rem)] w-px bg-slate-100" />}<span className="relative mt-0.5 grid size-[1.4rem] shrink-0 place-items-center rounded-full bg-emerald-50 text-emerald-600"><Check size={12} strokeWidth={3} /></span><div className="min-w-0"><strong className="block truncate text-xs text-slate-700">{event.label}</strong><span className="text-[10px] text-slate-400">{relativeTime(event.created_at)}</span></div></div>)}</div> : <div className="mt-5 rounded-xl border border-dashed border-slate-200 p-7 text-center"><CircleCheck className="mx-auto text-slate-300" /><p className="mt-2 text-xs text-slate-400">Your important workspace events will appear here.</p></div>}
              <div className="mt-5 border-t border-slate-100 pt-4"><div className="flex items-center justify-between"><span className="text-xs font-bold text-slate-600">Organization workspaces</span><button onClick={createOrganization} className="text-[10px] font-bold text-indigo-600">Add organization</button></div>{data.organizations.length ? <div className="mt-3 flex flex-wrap gap-2">{data.organizations.map(org => <span key={org.id} className="rounded-lg bg-slate-100 px-2.5 py-1.5 text-[10px] font-bold text-slate-600">{org.name} · <span className="capitalize text-indigo-600">{org.role.replaceAll("_", " ")}</span></span>)}</div> : <p className="mt-2 text-[11px] text-slate-400">You are currently using a private personal workspace.</p>}</div>
            </article>
          </section>
        </div>}
      </section>
    </main>
  );
}
