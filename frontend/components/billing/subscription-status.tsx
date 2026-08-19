import { CalendarClock, CheckCircle2 } from "lucide-react";

import type { BillingSubscription } from "@/lib/types";
import { formatDate } from "./format";

export function SubscriptionStatus({ subscription, onCancel, cancelling }: { subscription: BillingSubscription | null; onCancel: () => void; cancelling: boolean }) {
  if (!subscription?.plan) return <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500">Loading subscription…</div>;
  const paid = subscription.plan.amount_minor > 0;
  return <section className="rounded-3xl bg-gradient-to-br from-indigo-600 to-blue-600 p-7 text-white shadow-xl"><div className="flex flex-wrap items-start justify-between gap-4"><div><span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-[10px] font-black uppercase tracking-wider"><CheckCircle2 size={13} />{subscription.status}</span><h2 className="mt-4 text-3xl font-black">{subscription.plan.name} plan</h2><p className="mt-2 text-sm text-indigo-100">{subscription.cancel_at_period_end ? "Cancels at the end of the current period" : paid ? "Your paid learning access is active" : "Your essential LearnOS access is active"}</p></div><CalendarClock className="text-indigo-200" size={34} /></div>{subscription.current_period_end && <p className="mt-6 text-xs text-indigo-100">Current period ends <strong className="text-white">{formatDate(subscription.current_period_end)}</strong></p>}{paid && !subscription.cancel_at_period_end && <button disabled={cancelling} onClick={onCancel} className="mt-6 rounded-xl border border-white/25 bg-white/10 px-4 py-2.5 text-xs font-bold hover:bg-white/20 disabled:opacity-50">{cancelling ? "Cancelling…" : "Cancel at period end"}</button>}</section>;
}
