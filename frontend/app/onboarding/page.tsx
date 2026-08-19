"use client";

import { ArrowRight, LoaderCircle, Orbit } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

const goals = ["Full-stack engineer", "Backend engineer", "Frontend engineer", "AI engineer", "Data engineer", "DevOps engineer", "Interview preparation", "Certification preparation"];

export default function OnboardingPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [goal, setGoal] = useState("Full-stack engineer");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    const form = new FormData(event.currentTarget);
    try {
      await api("/me/onboarding/", {
        method: "POST",
        body: JSON.stringify({
          professional_role: form.get("role"), experience_level: form.get("experience"), career_goal: goal,
          learning_goals: [String(form.get("learning_goal"))], current_skills: String(form.get("current_skills")).split(",").map(s => s.trim()).filter(Boolean),
          target_skills: String(form.get("target_skills")).split(",").map(s => s.trim()).filter(Boolean), preferred_languages: String(form.get("languages")).split(",").map(s => s.trim()).filter(Boolean),
          daily_minutes: Number(form.get("daily_minutes")), weekly_target_minutes: Number(form.get("daily_minutes")) * 7,
          learning_style: form.get("learning_style"), timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        }),
      });
      router.push("/dashboard");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to save your learning profile");
    } finally { setLoading(false); }
  }

  return (
    <main className="min-h-screen bg-slate-50 px-5 py-8 sm:py-12">
      <form onSubmit={submit} className="mx-auto max-w-4xl overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-xl shadow-slate-200/50">
        <header className="border-b border-slate-100 px-7 py-6 sm:px-10"><div className="flex items-center gap-3"><span className="learnos-gradient grid size-10 place-items-center rounded-xl text-white"><Orbit size={21} /></span><div><strong className="text-lg">Set up your learning profile</strong><p className="text-xs text-slate-500">This shapes your future roadmap and dashboard.</p></div></div><div className="mt-5 h-1.5 overflow-hidden rounded-full bg-slate-100"><div className="h-full w-2/3 rounded-full bg-indigo-600" /></div></header>
        <div className="grid gap-8 p-7 sm:p-10">
          <div className="grid gap-5 sm:grid-cols-2"><div className="grid-field"><label htmlFor="role">What best describes you?</label><select id="role" name="role" required><option>Student</option><option>Developer</option><option>Professional</option><option>Job seeker</option><option>Mentor</option><option>Instructor</option></select></div><div className="grid-field"><label htmlFor="experience">Current experience</label><select id="experience" name="experience"><option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="advanced">Advanced</option></select></div></div>
          <fieldset><legend className="text-sm font-extrabold">Your primary goal</legend><div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">{goals.map(item => <button key={item} type="button" onClick={() => setGoal(item)} className={`rounded-xl border px-3 py-3 text-left text-xs font-bold ${goal === item ? "border-indigo-500 bg-indigo-50 text-indigo-700" : "border-slate-200 hover:border-indigo-200"}`}>{item}</button>)}</div></fieldset>
          <div className="grid-field"><label htmlFor="learning_goal">What do you want to accomplish?</label><textarea id="learning_goal" name="learning_goal" required rows={3} placeholder="For example: Become job-ready by building three full-stack projects..." /></div>
          <div className="grid gap-5 sm:grid-cols-2"><div className="grid-field"><label htmlFor="current_skills">Current skills <span className="font-normal text-slate-400">(comma separated)</span></label><input id="current_skills" name="current_skills" placeholder="HTML, CSS, Python" /></div><div className="grid-field"><label htmlFor="target_skills">Target skills</label><input id="target_skills" name="target_skills" required placeholder="React, Django, PostgreSQL" /></div></div>
          <div className="grid gap-5 sm:grid-cols-3"><div className="grid-field"><label htmlFor="daily_minutes">Daily time</label><select id="daily_minutes" name="daily_minutes"><option value="30">30 minutes</option><option value="60">1 hour</option><option value="90">1.5 hours</option><option value="120">2 hours</option></select></div><div className="grid-field"><label htmlFor="learning_style">Learning style</label><select id="learning_style" name="learning_style"><option>Project based</option><option>Video first</option><option>Reading first</option><option>Practice first</option></select></div><div className="grid-field"><label htmlFor="languages">Languages</label><input id="languages" name="languages" placeholder="Python, TypeScript" /></div></div>
          {error && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
        </div>
        <footer className="flex items-center justify-between border-t border-slate-100 bg-slate-50 px-7 py-5 sm:px-10"><span className="text-xs text-slate-400">You can change these preferences later.</span><button disabled={loading} className="flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-indigo-200 disabled:opacity-60">{loading ? <LoaderCircle className="animate-spin" size={17} /> : <>Build my workspace <ArrowRight size={17} /></>}</button></footer>
      </form>
    </main>
  );
}

