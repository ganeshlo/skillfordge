"use client";

import { ArrowRight, LoaderCircle } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { BillingAppLayout } from "@/components/billing/app-layout";
import { BillingHistory } from "@/components/billing/billing-history";
import { InvoiceList } from "@/components/billing/invoice-list";
import { SubscriptionStatus } from "@/components/billing/subscription-status";
import { api } from "@/lib/api";
import type { BillingInvoice, BillingPayment, BillingSubscription, User } from "@/lib/types";

export default function BillingPage() {
  const [user, setUser] = useState<User | null>(null);
  const [subscription, setSubscription] = useState<BillingSubscription | null>(null);
  const [payments, setPayments] = useState<BillingPayment[]>([]);
  const [invoices, setInvoices] = useState<BillingInvoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    const [me, current, history, invoiceData] = await Promise.all([api<User>("/me/"), api<BillingSubscription>("/billing/subscription/"), api<BillingPayment[]>("/billing/payments/"), api<BillingInvoice[]>("/billing/invoices/")]);
    setUser(me); setSubscription(current); setPayments(history); setInvoices(invoiceData);
  }, []);
  useEffect(() => { const timer = setTimeout(() => void load().catch((reason: Error) => setError(reason.message)).finally(() => setLoading(false)), 0); return () => clearTimeout(timer); }, [load]);

  async function cancel() {
    if (!window.confirm("Cancel renewal at the end of your current billing period?")) return;
    setCancelling(true); setError("");
    try { setSubscription(await api<BillingSubscription>("/billing/subscription/cancel/", { method: "POST" })); } catch (reason) { setError(reason instanceof Error ? reason.message : "Cancellation failed."); } finally { setCancelling(false); }
  }

  return <BillingAppLayout user={user}><div className="mx-auto max-w-7xl p-5 sm:p-8"><div className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-xs font-black uppercase tracking-wider text-indigo-600">Account</p><h1 className="mt-2 text-3xl font-black">Billing & subscription</h1><p className="mt-2 text-sm text-slate-500">Manage your plan, verified payments, and invoices.</p></div><Link href="/pricing" className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-bold text-white">Compare plans <ArrowRight size={15} /></Link></div>{error && <p role="alert" className="mt-5 rounded-xl bg-rose-50 p-3 text-xs font-semibold text-rose-700">{error}</p>}{loading ? <div className="grid min-h-96 place-items-center"><LoaderCircle className="animate-spin text-indigo-600" /></div> : <><div className="mt-7"><SubscriptionStatus subscription={subscription} onCancel={() => void cancel()} cancelling={cancelling} /></div><div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1.5fr)_minmax(300px,1fr)]"><BillingHistory payments={payments} /><InvoiceList invoices={invoices} /></div></>}</div></BillingAppLayout>;
}
