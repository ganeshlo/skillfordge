"use client";

import { ArrowLeft, LoaderCircle, MailCheck } from "lucide-react";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { AuthShell } from "@/components/auth-shell";
import { api } from "@/lib/api";

type Result = { message: string; debug_reset_url?: string };

export default function ForgotPasswordPage() {
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true); setError("");
    const email = String(new FormData(event.currentTarget).get("email"));
    try { setResult(await api<Result>("/auth/password/forgot/", { method: "POST", body: JSON.stringify({ email }) })); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to request a reset link"); }
    finally { setLoading(false); }
  }

  return (
    <AuthShell title="Reset your password" subtitle="Enter your account email and we’ll send a secure, single-use reset link.">
      {result ? <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5"><MailCheck className="text-emerald-600" /><h2 className="mt-3 font-extrabold text-emerald-950">Check your email</h2><p className="mt-2 text-sm leading-6 text-emerald-800">{result.message}</p>{result.debug_reset_url && <Link href={result.debug_reset_url} className="mt-4 inline-flex rounded-lg bg-emerald-700 px-4 py-2 text-xs font-bold text-white">Open development reset link</Link>}</div> : <form onSubmit={submit} className="grid gap-5"><div className="grid-field"><label htmlFor="email">Email address</label><input id="email" name="email" type="email" autoComplete="email" required /></div>{error && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}<button disabled={loading} className="flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 py-3.5 font-bold text-white shadow-lg shadow-indigo-200 disabled:opacity-60">{loading ? <LoaderCircle className="animate-spin" size={18} /> : "Send reset link"}</button></form>}
      <Link href="/login" className="mt-7 flex items-center justify-center gap-2 text-sm font-bold text-slate-500 hover:text-indigo-600"><ArrowLeft size={16} /> Back to sign in</Link>
    </AuthShell>
  );
}

