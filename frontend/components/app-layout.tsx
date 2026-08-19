"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { DashboardSidebar } from "@/components/dashboard/sidebar";
import { DashboardTopbar } from "@/components/dashboard/topbar";
import { api, saveAccessToken } from "@/lib/api";
import type { User } from "@/lib/types";

export function AppLayout({ user, currentPath, children, className = "bg-slate-50 dark:bg-slate-950", contentClassName = "", initiallyCollapsed = false }: { user: User | null; currentPath: string; children: React.ReactNode; className?: string; contentClassName?: string; initiallyCollapsed?: boolean }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(initiallyCollapsed);
  useEffect(() => {
    const task = window.setTimeout(() => {
      const saved = window.localStorage.getItem("learnos-navigation-collapsed");
      if (saved !== null) setCollapsed(saved === "true");
    }, 0);
    return () => window.clearTimeout(task);
  }, []);
  function changeCollapsed(value: boolean) {
    setCollapsed(value);
    window.localStorage.setItem("learnos-navigation-collapsed", String(value));
  }
  async function logout() {
    try { await api("/auth/token/revoke/", { method: "POST" }); } catch { /* browser session must still be cleared */ }
    saveAccessToken(null);
    router.replace("/login");
  }
  return <main className={`flex min-h-screen ${className}`}><DashboardSidebar open={open} onClose={() => setOpen(false)} onLogout={logout} currentPath={currentPath} collapsed={collapsed} onCollapsedChange={changeCollapsed} /><section className={`min-w-0 flex-1 ${contentClassName}`}><DashboardTopbar fullName={user?.full_name ?? ""} role={user?.profile.professional_role || "Learner"} initialTheme={user?.preferences.theme} onMenu={() => setOpen(true)} />{children}</section></main>;
}
