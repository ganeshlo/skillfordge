"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, Check, LoaderCircle } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { z } from "zod";
import { AuthShell } from "@/components/auth-shell";
import { api, saveAccessToken } from "@/lib/api";

const schema = z.object({
  full_name: z.string().min(2, "Enter your full name").max(160),
  email: z.email("Enter a valid email address"),
  password: z.string().min(10, "Use at least 10 characters").regex(/[A-Z]/, "Add an uppercase letter").regex(/[0-9]/, "Add a number"),
});
type Form = z.infer<typeof schema>;

export default function RegisterPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const { register, handleSubmit, control, formState: { errors, isSubmitting } } = useForm<Form>({ resolver: zodResolver(schema) });
  const password = useWatch({ control, name: "password", defaultValue: "" });

  async function submit(values: Form) {
    setError("");
    try {
      await api("/auth/register/", { method: "POST", body: JSON.stringify(values) });
      const token = await api<{ access: string }>("/auth/token/", { method: "POST", body: JSON.stringify({ email: values.email, password: values.password }) });
      saveAccessToken(token.access);
      router.push("/onboarding");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to create your account");
    }
  }

  return (
    <AuthShell title="Build your learning system" subtitle="Create a private workspace now. Organization features can be added later.">
      <form onSubmit={handleSubmit(submit)} className="grid gap-4" noValidate>
        <div className="grid-field"><label htmlFor="name">Full name</label><input id="name" autoComplete="name" {...register("full_name")} />{errors.full_name && <p className="text-xs text-rose-600">{errors.full_name.message}</p>}</div>
        <div className="grid-field"><label htmlFor="email">Email address</label><input id="email" autoComplete="email" {...register("email")} />{errors.email && <p className="text-xs text-rose-600">{errors.email.message}</p>}</div>
        <div className="grid-field"><label htmlFor="password">Password</label><input id="password" type="password" autoComplete="new-password" {...register("password")} />{errors.password && <p className="text-xs text-rose-600">{errors.password.message}</p>}</div>
        <div className="flex flex-wrap gap-2 text-[11px] font-bold text-slate-500">
          <span className={password.length >= 10 ? "text-emerald-600" : ""}><Check size={12} className="inline" /> 10+ characters</span>
          <span className={/[A-Z]/.test(password) ? "text-emerald-600" : ""}><Check size={12} className="inline" /> uppercase</span>
          <span className={/[0-9]/.test(password) ? "text-emerald-600" : ""}><Check size={12} className="inline" /> number</span>
        </div>
        {error && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
        <button disabled={isSubmitting} className="mt-1 flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 py-3.5 font-bold text-white shadow-lg shadow-indigo-200 hover:bg-indigo-700 disabled:opacity-60">{isSubmitting ? <LoaderCircle className="animate-spin" size={18} /> : <>Create workspace <ArrowRight size={18} /></>}</button>
      </form>
      <p className="mt-6 text-center text-xs leading-5 text-slate-400">By continuing, you agree to the platform terms and acknowledge the privacy policy.</p>
      <p className="mt-4 text-center text-sm text-slate-500">Already have an account? <Link href="/login" className="font-bold text-indigo-600">Sign in</Link></p>
    </AuthShell>
  );
}
