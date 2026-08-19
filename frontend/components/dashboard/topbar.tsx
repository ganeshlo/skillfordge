"use client";

import { Bell, ChevronDown, LoaderCircle, Menu, Moon, Pencil, Sun, UserRound, X } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { User } from "@/lib/types";

export function DashboardTopbar({ fullName, role, onMenu, initialTheme = "system" }: { fullName: string; role: string; onMenu: () => void; initialTheme?: string }) {
  const [profile, setProfile] = useState<User | null>(null);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const visibleName = profile?.full_name || fullName;
  const visibleRole = profile?.profile.professional_role || role;
  const initials = visibleName.split(" ").filter(Boolean).map((part) => part[0]).slice(0, 2).join("").toUpperCase() || "LO";

  useEffect(() => {
    const task = window.setTimeout(() => {
      const stored = window.localStorage.getItem("learnos-theme");
      const next = stored === "dark" || stored === "light" ? stored : initialTheme === "dark" || (initialTheme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches) ? "dark" : "light";
      setTheme(next);
      document.documentElement.classList.toggle("dark", next === "dark");
      document.documentElement.style.colorScheme = next;
    }, 0);
    return () => window.clearTimeout(task);
  }, [initialTheme]);
  useEffect(() => {
    const sync = (event: Event) => setTheme((event as CustomEvent<"light" | "dark">).detail);
    window.addEventListener("learnos-theme-change", sync);
    return () => window.removeEventListener("learnos-theme-change", sync);
  }, []);

  async function toggleTheme() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    window.localStorage.setItem("learnos-theme", next);
    document.documentElement.classList.toggle("dark", next === "dark");
    document.documentElement.style.colorScheme = next;
    window.dispatchEvent(new CustomEvent("learnos-theme-change", { detail: next }));
    try { await api<User>("/me/", { method: "PATCH", body: JSON.stringify({ theme: next }) }); } catch { /* local preference still works offline */ }
  }

  async function openProfile() {
    setOpen(true);
    setError("");
    if (profile) return;
    setLoading(true);
    try {
      setProfile(await api<User>("/me/"));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load your profile.");
    } finally {
      setLoading(false);
    }
  }

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setSaving(true);
    setError("");
    try {
      const updated = await api<User>("/me/", {
        method: "PATCH",
        body: JSON.stringify({
          full_name: form.get("full_name"),
          professional_role: form.get("professional_role"),
          experience_level: form.get("experience_level"),
          career_goal: form.get("career_goal"),
          daily_minutes: Number(form.get("daily_minutes")),
          weekly_target_minutes: Number(form.get("weekly_target_minutes")),
        }),
      });
      setProfile(updated);
      setOpen(false);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not update your profile.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <header className="sticky top-0 z-20 flex h-[4.5rem] items-center gap-3 border-b border-slate-200 bg-white/90 px-4 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-900/90 sm:px-7">
        <button className="grid size-10 place-items-center rounded-xl border border-slate-200 text-slate-600 lg:hidden" onClick={onMenu} aria-label="Open navigation"><Menu size={20} /></button>
        <div className="hidden sm:block"><p className="text-xs font-black text-slate-700">LearnOS</p><p className="text-[10px] text-slate-400">Your learning operating system</p></div>
        <div className="ml-auto flex items-center gap-2">
          <button onClick={() => void toggleTheme()} className="grid size-10 place-items-center rounded-xl text-slate-500 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800" aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`} title={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}>{theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}</button>
          <button className="relative grid size-10 place-items-center rounded-xl text-slate-500 hover:bg-slate-50" aria-label="Notifications"><Bell size={19} /><span className="absolute right-2.5 top-2.5 size-1.5 rounded-full bg-indigo-500" /></button>
          <button onClick={() => void openProfile()} className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-white px-2 py-1.5 text-left hover:border-indigo-300 hover:shadow-sm" aria-label="Open and edit profile">
            <span className="grid size-8 place-items-center rounded-lg bg-gradient-to-br from-violet-100 to-indigo-100 text-xs font-black text-violet-700">{initials}</span>
            <span className="hidden sm:block"><strong className="block max-w-32 truncate text-xs text-slate-800">{visibleName || "Loading…"}</strong><small className="block max-w-32 truncate text-[10px] capitalize text-slate-400">{visibleRole || "Learner"}</small></span>
            <ChevronDown size={14} className="hidden text-slate-400 sm:block" />
          </button>
        </div>
      </header>

      {open && <div className="fixed inset-0 z-[80] grid place-items-center bg-slate-950/60 p-4" onMouseDown={(event) => event.target === event.currentTarget && setOpen(false)}>
        <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-3xl bg-white p-6 shadow-2xl">
          <div className="flex items-start justify-between"><div className="flex items-center gap-3"><span className="grid size-11 place-items-center rounded-2xl bg-indigo-100 text-indigo-700"><UserRound size={21} /></span><div><h2 className="text-lg font-black text-slate-900">Edit profile</h2><p className="text-xs text-slate-500">Keep your learning plan personalized.</p></div></div><button onClick={() => setOpen(false)} className="rounded-lg p-2 text-slate-400 hover:bg-slate-100" aria-label="Close profile"><X size={18} /></button></div>
          {loading ? <div className="grid min-h-56 place-items-center"><LoaderCircle className="animate-spin text-indigo-600" /></div> : profile ? <form onSubmit={saveProfile} className="mt-6 grid gap-4 sm:grid-cols-2">
            <label className="grid gap-1.5 text-xs font-bold text-slate-700 sm:col-span-2">Full name<input name="full_name" required maxLength={160} defaultValue={profile.full_name} className="rounded-xl border border-slate-200 px-3 py-2.5 font-normal outline-none focus:border-indigo-400" /></label>
            <label className="grid gap-1.5 text-xs font-bold text-slate-700">Professional role<input name="professional_role" maxLength={80} defaultValue={profile.profile.professional_role} className="rounded-xl border border-slate-200 px-3 py-2.5 font-normal outline-none focus:border-indigo-400" /></label>
            <label className="grid gap-1.5 text-xs font-bold text-slate-700">Experience<select name="experience_level" defaultValue={profile.profile.experience_level} className="rounded-xl border border-slate-200 px-3 py-2.5 font-normal outline-none focus:border-indigo-400"><option value="">Not specified</option><option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="advanced">Advanced</option></select></label>
            <label className="grid gap-1.5 text-xs font-bold text-slate-700 sm:col-span-2">Career goal<input name="career_goal" maxLength={120} defaultValue={profile.profile.career_goal} className="rounded-xl border border-slate-200 px-3 py-2.5 font-normal outline-none focus:border-indigo-400" /></label>
            <label className="grid gap-1.5 text-xs font-bold text-slate-700">Daily minutes<input name="daily_minutes" type="number" min={10} max={720} defaultValue={profile.profile.daily_minutes} className="rounded-xl border border-slate-200 px-3 py-2.5 font-normal outline-none focus:border-indigo-400" /></label>
            <label className="grid gap-1.5 text-xs font-bold text-slate-700">Weekly minutes<input name="weekly_target_minutes" type="number" min={30} max={5040} defaultValue={profile.profile.weekly_target_minutes} className="rounded-xl border border-slate-200 px-3 py-2.5 font-normal outline-none focus:border-indigo-400" /></label>
            <div className="rounded-xl bg-slate-50 p-3 text-xs text-slate-500 sm:col-span-2"><strong className="block text-slate-700">Email</strong>{profile.email}<span className="ml-2 text-[10px]">Email is protected and cannot be changed here.</span></div>
            {error && <p role="alert" className="text-xs font-semibold text-rose-600 sm:col-span-2">{error}</p>}
            <div className="flex justify-end gap-2 sm:col-span-2"><button type="button" onClick={() => setOpen(false)} className="rounded-xl border border-slate-200 px-4 py-2.5 text-xs font-bold text-slate-600">Cancel</button><button disabled={saving} className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-bold text-white disabled:opacity-50">{saving ? <LoaderCircle size={14} className="animate-spin" /> : <Pencil size={14} />} Save profile</button></div>
          </form> : <div className="py-12 text-center"><p className="text-sm text-rose-600">{error || "Profile unavailable."}</p><button onClick={() => { setProfile(null); void openProfile(); }} className="mt-3 text-xs font-bold text-indigo-600">Try again</button></div>}
        </div>
      </div>}
    </>
  );
}
