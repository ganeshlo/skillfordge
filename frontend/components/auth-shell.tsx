import { BookOpenCheck, BrainCircuit, ChartNoAxesCombined, ShieldCheck } from "lucide-react";
import { Logo } from "./logo";

const benefits = [
  [BrainCircuit, "Personalized learning", "One plan shaped around your goals, evidence, and available time."],
  [BookOpenCheck, "Everything in context", "Roadmaps, resources, notes, practice, and projects stay connected."],
  [ChartNoAxesCombined, "Progress you can trust", "Measure active learning and demonstrated skills—not vanity metrics."],
  [ShieldCheck, "Private by default", "Your personal notes and code remain yours unless you explicitly share them."],
] as const;

export function AuthShell({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <main className="grid min-h-screen lg:grid-cols-[1.05fr_.95fr]">
      <section className="learnos-gradient relative hidden overflow-hidden p-12 text-white lg:flex lg:flex-col">
        <div className="absolute -right-32 -top-32 size-96 rounded-full border border-white/15" />
        <div className="absolute -bottom-40 -left-24 size-[30rem] rounded-full bg-white/5" />
        <Logo inverse />
        <div className="relative my-auto max-w-xl">
          <p className="mb-4 text-xs font-bold uppercase tracking-[.2em] text-indigo-200">Your learning operating system</p>
          <h2 className="text-5xl font-black leading-[1.05] tracking-[-.05em]">Turn ambition into evidence of progress.</h2>
          <div className="mt-10 grid gap-5">
            {benefits.map(([Icon, heading, text]) => (
              <div key={heading} className="flex gap-4">
                <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-white/10"><Icon size={20} /></span>
                <div><h3 className="font-bold">{heading}</h3><p className="mt-1 text-sm leading-6 text-indigo-100/80">{text}</p></div>
              </div>
            ))}
          </div>
        </div>
        <p className="relative text-xs text-indigo-200/80">Built for focused learners and ambitious teams.</p>
      </section>
      <section className="flex items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-md">
          <div className="mb-10 lg:hidden"><Logo /></div>
          <h1 className="text-3xl font-black tracking-[-.04em] text-slate-950">{title}</h1>
          <p className="mt-2 text-sm leading-6 text-slate-500">{subtitle}</p>
          <div className="mt-8">{children}</div>
        </div>
      </section>
    </main>
  );
}

