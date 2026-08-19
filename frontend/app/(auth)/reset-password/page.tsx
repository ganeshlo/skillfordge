"use client";

import { CheckCircle2, LoaderCircle } from "lucide-react";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { AuthShell } from "@/components/auth-shell";
import { api } from "@/lib/api";

export default function ResetPasswordPage() {
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError("");
    const data = new FormData(event.currentTarget);
    const password = String(data.get("password"));
    if (password !== String(data.get("confirm_password"))) { setError("The passwords do not match."); return; }
    const params = new URLSearchParams(window.location.search);
    const credentials = { uid: params.get("uid") ?? "", token: params.get("token") ?? "" };
    if (!credentials.uid || !credentials.token) { setError("This reset link is incomplete or invalid."); return; }
    setLoading(true);
    try { await api("/auth/password/reset/", { method: "POST", body: JSON.stringify({ ...credentials, new_password: password }) }); setDone(true); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to reset your password"); }
    finally { setLoading(false); }
  }

  return (
    <AuthShell title="Choose a new password" subtitle="Use a strong password you do not use on another service.">
      {done ? <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5"><CheckCircle2 className="text-emerald-600" /><h2 className="mt-3 font-extrabold text-emerald-950">Password updated</h2><p className="mt-2 text-sm text-emerald-800">Your old password no longer works.</p><Link href="/login" className="mt-4 inline-flex rounded-lg bg-emerald-700 px-4 py-2 text-xs font-bold text-white">Sign in to LearnOS</Link></div> : <form onSubmit={submit} className="grid gap-5"><div className="grid-field"><label htmlFor="password">New password</label><input id="password" name="password" type="password" minLength={10} autoComplete="new-password" required /><p className="text-[11px] text-slate-400">At least 10 characters. Avoid common or entirely numeric passwords.</p></div><div className="grid-field"><label htmlFor="confirm_password">Confirm new password</label><input id="confirm_password" name="confirm_password" type="password" minLength={10} autoComplete="new-password" required /></div>{error && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}<button disabled={loading} className="flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 py-3.5 font-bold text-white shadow-lg shadow-indigo-200 disabled:opacity-60">{loading ? <LoaderCircle className="animate-spin" size={18} /> : "Update password"}</button></form>}
    </AuthShell>
  );
}
