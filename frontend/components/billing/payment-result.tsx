"use client";

import { CheckCircle2, X, XCircle } from "lucide-react";

export function PaymentResult({ result, onClose }: { result: { type: "success" | "failure"; title: string; message: string } | null; onClose: () => void }) {
  if (!result) return null;
  const success = result.type === "success";
  return <div className="fixed inset-0 z-[100] grid place-items-center bg-slate-950/65 p-4"><section role="alertdialog" className="w-full max-w-sm rounded-3xl bg-white p-7 text-center shadow-2xl"><button onClick={onClose} className="ml-auto grid size-8 place-items-center rounded-lg text-slate-400 hover:bg-slate-100"><X size={17} /></button><span className={`mx-auto grid size-16 place-items-center rounded-full ${success ? "bg-emerald-100 text-emerald-600" : "bg-rose-100 text-rose-600"}`}>{success ? <CheckCircle2 size={32} /> : <XCircle size={32} />}</span><h2 className="mt-5 text-xl font-black">{result.title}</h2><p className="mt-2 text-sm leading-6 text-slate-500">{result.message}</p><button onClick={onClose} className={`mt-6 w-full rounded-xl py-3 text-sm font-black text-white ${success ? "bg-emerald-600" : "bg-slate-900"}`}>{success ? "View billing" : "Try again"}</button></section></div>;
}

export function PaymentSuccess({ message, onClose }: { message: string; onClose: () => void }) {
  return <PaymentResult result={{ type: "success", title: "Payment successful", message }} onClose={onClose} />;
}

export function PaymentFailure({ message, onClose }: { message: string; onClose: () => void }) {
  return <PaymentResult result={{ type: "failure", title: "Payment failed", message }} onClose={onClose} />;
}
