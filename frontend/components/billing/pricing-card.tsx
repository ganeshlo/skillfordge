import { Check, Crown, ShieldCheck } from "lucide-react";

import type { BillingPlan } from "@/lib/types";
import { formatMoney } from "./format";

export function PricingCard({ plan, current, onSelect }: { plan: BillingPlan; current: boolean; onSelect: (plan: BillingPlan) => void }) {
  const offer = Boolean(plan.compare_at_amount_minor && plan.compare_at_amount_minor > plan.amount_minor);
  const savings = offer ? Math.round((1 - plan.amount_minor / plan.compare_at_amount_minor!) * 100) : 0;
  return <article className={`relative flex min-h-[31rem] flex-col rounded-3xl border bg-white p-7 shadow-sm ${plan.is_featured ? "border-indigo-500 shadow-xl shadow-indigo-100" : "border-slate-200"}`}>
    {(plan.is_featured || offer) && <span className={`absolute -top-3 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full px-4 py-1 text-[10px] font-black uppercase tracking-wider text-white ${offer ? "bg-gradient-to-r from-rose-500 to-orange-500" : "bg-indigo-600"}`}>{offer ? `Limited offer · Save ${savings}%` : "Most popular"}</span>}
    <span className={`grid size-12 place-items-center rounded-2xl ${plan.code === "enterprise" ? "bg-violet-100 text-violet-700" : "bg-indigo-50 text-indigo-700"}`}>{plan.code === "enterprise" ? <ShieldCheck size={23} /> : <Crown size={23} />}</span>
    <h2 className="mt-5 text-2xl font-black text-slate-950">{plan.name}</h2>
    <p className="mt-2 min-h-12 text-sm leading-6 text-slate-500">{plan.description}</p>
    <div className="mt-5">{offer && <div className="mb-1 flex items-center gap-2"><span className="text-sm font-bold text-slate-400 line-through">{formatMoney(plan.compare_at_amount_minor!, plan.currency)}</span><span className="rounded-full bg-rose-50 px-2 py-0.5 text-[10px] font-black text-rose-600">OFFER PRICE</span></div>}<strong className={`text-4xl font-black ${offer ? "text-rose-600" : "text-slate-950"}`}>{plan.amount_minor ? formatMoney(plan.amount_minor, plan.currency) : "Free"}</strong>{plan.amount_minor > 0 && <span className="text-sm text-slate-400"> / {plan.billing_interval}</span>}</div>
    <ul className="mt-7 flex-1 space-y-3">{plan.features.map((feature) => <li key={feature} className="flex gap-2.5 text-sm text-slate-600"><Check size={17} className="mt-0.5 shrink-0 text-emerald-500" />{feature}</li>)}</ul>
    <button disabled={current} onClick={() => onSelect(plan)} className={`mt-7 w-full rounded-xl py-3 text-sm font-black ${current ? "cursor-default bg-slate-100 text-slate-400" : plan.is_featured ? "bg-indigo-600 text-white hover:bg-indigo-700" : "border border-indigo-200 text-indigo-700 hover:bg-indigo-50"}`}>{current ? "Current plan" : plan.code === "free" ? "Choose Free" : "Upgrade"}</button>
  </article>;
}
