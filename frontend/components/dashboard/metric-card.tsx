import type { LucideIcon } from "lucide-react";

export function MetricCard({ icon: Icon, label, value, detail, tone = "indigo" }: { icon: LucideIcon; label: string; value: string; detail: string; tone?: "indigo" | "blue" | "violet" | "emerald" }) {
  const tones = { indigo: "bg-indigo-50 text-indigo-600", blue: "bg-blue-50 text-blue-600", violet: "bg-violet-50 text-violet-600", emerald: "bg-emerald-50 text-emerald-600" };
  return <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/40"><div className="flex items-start justify-between"><span className="text-xs font-bold text-slate-500">{label}</span><span className={`grid size-9 place-items-center rounded-xl ${tones[tone]}`}><Icon size={18} /></span></div><strong className="mt-4 block text-2xl font-black tracking-[-.03em] text-slate-950">{value}</strong><p className="mt-1 truncate text-[11px] text-slate-400">{detail}</p></article>;
}

