"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, LoaderCircle } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { AuthShell } from "@/components/auth-shell";
import { api, saveAccessToken } from "@/lib/api";

const schema = z.object({ email: z.email("Enter a valid email address"), password: z.string().min(1, "Enter your password") });
type Form = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<Form>({ resolver: zodResolver(schema) });

  async function submit(values: Form) {
    setError("");
    try {
      const result = await api<{ access: string }>("/auth/token/", { method: "POST", body: JSON.stringify(values) });
      saveAccessToken(result.access);
      router.push("/dashboard");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to sign in");
    }
  }

  return (
    <AuthShell title="Welcome back" subtitle="Continue your learning plan and pick up where you left off.">
      <form onSubmit={handleSubmit(submit)} className="grid gap-5" noValidate>
        <div className="grid-field"><label htmlFor="email">Email address</label><input id="email" autoComplete="email" {...register("email")} />{errors.email && <p className="text-xs text-rose-600">{errors.email.message}</p>}</div>
        <div className="grid-field"><div className="flex justify-between"><label htmlFor="password">Password</label><Link href="/forgot-password" className="text-xs font-bold text-indigo-600 hover:text-indigo-700">Forgot password?</Link></div><input id="password" type="password" autoComplete="current-password" {...register("password")} />{errors.password && <p className="text-xs text-rose-600">{errors.password.message}</p>}</div>
        {error && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
        <button disabled={isSubmitting} className="flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 py-3.5 font-bold text-white shadow-lg shadow-indigo-200 hover:bg-indigo-700 disabled:opacity-60">{isSubmitting ? <LoaderCircle className="animate-spin" size={18} /> : <>Sign in <ArrowRight size={18} /></>}</button>
      </form>
      <p className="mt-7 text-center text-sm text-slate-500">New to LearnOS? <Link href="/register" className="font-bold text-indigo-600 hover:text-indigo-700">Create an account</Link></p>
    </AuthShell>
  );
}
