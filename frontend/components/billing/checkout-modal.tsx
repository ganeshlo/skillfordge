"use client";

import { CreditCard, LoaderCircle, LockKeyhole, X } from "lucide-react";

import type { BillingPlan } from "@/lib/types";
import { formatMoney } from "./format";

export function CheckoutModal({ plan, busy, onClose, onConfirm }: { plan: BillingPlan | null; busy: boolean; onClose: () => void; onConfirm: () => void }) {
  if (!plan) return null;
  return <div className="fixed inset-0 z-[90] grid place-items-center bg-slate-950/65 p-4"><section role="dialog" aria-modal="true" aria-labelledby="checkout-title" className="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl">
    <div className="flex items-start justify-between"><span className="grid size-11 place-items-center rounded-2xl bg-indigo-100 text-indigo-700"><CreditCard size={21} /></span><button disabled={busy} onClick={onClose} aria-label="Close checkout" className="rounded-lg p-2 text-slate-400 hover:bg-slate-100"><X size={18} /></button></div>
    <h2 id="checkout-title" className="mt-5 text-xl font-black">Upgrade to {plan.name}</h2><p className="mt-2 text-sm leading-6 text-slate-500">Your order amount is calculated securely by LearnOS. Payment details are collected directly by Razorpay.</p>
    <div className="mt-5 flex items-center justify-between rounded-2xl bg-slate-50 p-4"><div><p className="text-xs font-bold text-slate-500">Total</p><p className="mt-1 text-xs text-slate-400">{plan.billing_interval} access</p></div><strong className="text-2xl font-black">{plan.amount_minor ? formatMoney(plan.amount_minor, plan.currency) : "Free"}</strong></div>
    <div className="mt-4 flex items-center gap-2 text-[11px] text-slate-500"><LockKeyhole size={14} className="text-emerald-600" />Secure Razorpay Checkout. LearnOS never receives card or UPI credentials.</div>
    <button disabled={busy} onClick={onConfirm} className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 py-3 text-sm font-black text-white disabled:opacity-60">{busy && <LoaderCircle size={16} className="animate-spin" />}{plan.amount_minor ? "Continue to secure payment" : "Activate Free plan"}</button>
  </section></div>;
}
