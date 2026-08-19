"use client";

import { ArrowRight, LoaderCircle, ShieldCheck, Sparkles } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { BillingAppLayout } from "@/components/billing/app-layout";
import { CheckoutModal } from "@/components/billing/checkout-modal";
import { PaymentResult } from "@/components/billing/payment-result";
import { PricingCard } from "@/components/billing/pricing-card";
import { api } from "@/lib/api";
import type { BillingOrder, BillingPlan, BillingSubscription, User } from "@/lib/types";

type CheckoutResponse = { razorpay_payment_id: string; razorpay_order_id: string; razorpay_signature: string };
type RazorpayInstance = { open(): void; on(event: "payment.failed", handler: (response: { error?: { description?: string } }) => void): void };
type RazorpayOptions = { key: string; amount: number; currency: string; name: string; description: string; order_id: string; prefill: { name: string; email: string }; theme: { color: string }; handler: (response: CheckoutResponse) => void; modal: { ondismiss: () => void; confirm_close: boolean } };
declare global { interface Window { Razorpay?: new (options: RazorpayOptions) => RazorpayInstance } }

let checkoutLoader: Promise<void> | null = null;
function loadCheckout() {
  if (window.Razorpay) return Promise.resolve();
  if (!checkoutLoader) checkoutLoader = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Secure Checkout could not be loaded."));
    document.head.appendChild(script);
  });
  return checkoutLoader;
}

export default function PricingPage() {
  const [user, setUser] = useState<User | null>(null);
  const [plans, setPlans] = useState<BillingPlan[]>([]);
  const [subscription, setSubscription] = useState<BillingSubscription | null>(null);
  const [selected, setSelected] = useState<BillingPlan | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState<{ type: "success" | "failure"; title: string; message: string } | null>(null);

  const refresh = useCallback(async () => {
    const [me, available, current] = await Promise.all([api<User>("/me/"), api<BillingPlan[]>("/billing/plans/"), api<BillingSubscription>("/billing/subscription/")]);
    setUser(me); setPlans(available); setSubscription(current);
  }, []);

  useEffect(() => { const timer = setTimeout(() => void refresh().finally(() => setLoading(false)), 0); return () => clearTimeout(timer); }, [refresh]);

  async function checkout() {
    if (!selected) return;
    setBusy(true);
    try {
      const order = await api<BillingOrder>("/billing/orders/", {
        method: "POST",
        headers: { "Idempotency-Key": crypto.randomUUID() },
        body: JSON.stringify({ plan_code: selected.code }),
      });
      if (order.free_activated) {
        setSelected(null); setResult({ type: "success", title: "Plan activated", message: "Your Free LearnOS subscription is active." }); await refresh(); return;
      }
      if (!order.key_id || !order.order_id || !order.payment_id || order.amount_minor === undefined || !order.currency || !order.prefill) throw new Error("The server returned an incomplete payment order.");
      await loadCheckout();
      setSelected(null);
      const razorpay = new window.Razorpay!({
        key: order.key_id, amount: order.amount_minor, currency: order.currency, name: "LearnOS", description: `${order.plan?.name ?? "LearnOS"} subscription`, order_id: order.order_id, prefill: order.prefill, theme: { color: "#4F46E5" }, confirm_close: true,
        modal: { confirm_close: true, ondismiss: () => { void api(`/billing/payments/${order.payment_id}/cancel/`, { method: "POST" }); setResult({ type: "failure", title: "Checkout cancelled", message: "No payment information was stored. You can try again whenever you are ready." }); } },
        handler: (response) => { void (async () => { try { await api<BillingSubscription>("/billing/payments/verify/", { method: "POST", body: JSON.stringify({ payment_id: order.payment_id, ...response }) }); setResult({ type: "success", title: "Payment successful", message: "Your signature was verified and your subscription is now active." }); await refresh(); } catch (reason) { setResult({ type: "failure", title: "Verification failed", message: reason instanceof Error ? reason.message : "Payment could not be verified." }); } })(); },
      } as RazorpayOptions);
      razorpay.on("payment.failed", (response) => setResult({ type: "failure", title: "Payment failed", message: response.error?.description || "Razorpay could not complete this payment." }));
      razorpay.open();
    } catch (reason) {
      setResult({ type: "failure", title: "Unable to start payment", message: reason instanceof Error ? reason.message : "Please try again." });
    } finally { setBusy(false); }
  }

  return <BillingAppLayout user={user}><div className="mx-auto max-w-7xl px-5 py-10 sm:px-8"><header className="text-center"><span className="inline-flex items-center gap-2 rounded-full bg-indigo-50 px-3 py-1.5 text-[10px] font-black uppercase tracking-wider text-indigo-700"><Sparkles size={13} />Simple, secure plans</span><h1 className="mx-auto mt-5 max-w-3xl text-4xl font-black tracking-tight text-slate-950 sm:text-5xl">Invest in your learning operating system</h1><p className="mx-auto mt-4 max-w-2xl text-sm leading-7 text-slate-500">Compare LearnOS plans. Prices are controlled by the server and payment details are collected securely by Razorpay.</p><Link href="/billing" className="mt-4 inline-flex items-center gap-1 text-xs font-bold text-indigo-600">View billing account <ArrowRight size={13} /></Link></header>{loading ? <div className="grid min-h-96 place-items-center"><LoaderCircle className="animate-spin text-indigo-600" /></div> : <div className="mt-12 grid gap-6 lg:grid-cols-3">{plans.map((plan) => <PricingCard key={plan.id} plan={plan} current={subscription?.plan?.code === plan.code && subscription.status === "active"} onSelect={setSelected} />)}</div>}<div className="mt-10 flex justify-center gap-2 text-xs text-slate-500"><ShieldCheck size={16} className="text-emerald-600" />Payment data goes directly to Razorpay. LearnOS stores only provider identifiers and verified status.</div></div><CheckoutModal plan={selected} busy={busy} onClose={() => !busy && setSelected(null)} onConfirm={() => void checkout()} /><PaymentResult result={result} onClose={() => setResult(null)} /></BillingAppLayout>;
}
