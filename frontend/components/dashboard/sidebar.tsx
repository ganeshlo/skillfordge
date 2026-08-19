import { BarChart3, BookOpen, Braces, CreditCard, FileText, FolderKanban, Goal, GraduationCap, LayoutDashboard, LogOut, PanelLeftClose, PanelLeftOpen, Sparkles, TimerReset, X } from "lucide-react";
import Link from "next/link";
import { Logo } from "@/components/logo";

const navigation = [
  [LayoutDashboard, "Dashboard", "ready", "/dashboard"], [GraduationCap, "My learning", "ready", "/learning"], [BookOpen, "Roadmaps", "ready", "/roadmaps"],
  [TimerReset, "Study workspace", "ready", "/study"], [FileText, "Knowledge base", "ready", "/knowledge"], [Braces, "Code workspace", "ready", "/code"],
  [FolderKanban, "Projects", "ready", "/projects"], [Goal, "Goals", "ready", "/goals"], [BarChart3, "Analytics", "ready", "/analytics"], [CreditCard, "Billing", "ready", "/billing"],
] as const;

export function DashboardSidebar({ open, onClose, onLogout, currentPath = "/dashboard", collapsed = false, onCollapsedChange }: { open: boolean; onClose: () => void; onLogout: () => void; currentPath?: string; collapsed?: boolean; onCollapsedChange?: (collapsed: boolean) => void }) {
  return (
    <>
      {open && <button aria-label="Close navigation" className="fixed inset-0 z-30 bg-slate-950/35 backdrop-blur-[2px] lg:hidden" onClick={onClose} />}
      <aside className={`fixed inset-y-0 left-0 z-40 flex w-[17rem] flex-col border-r border-slate-200 bg-white px-4 py-5 shadow-xl transition-[width,transform] dark:border-slate-800 dark:bg-slate-900 lg:static lg:shadow-none ${collapsed ? "lg:w-[4.75rem] lg:px-2" : "lg:w-[17rem]"} ${open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}>
        <div className="flex items-center justify-between px-2">{collapsed ? <><span className="hidden size-9 place-items-center rounded-xl bg-indigo-600 text-white lg:grid"><GraduationCap size={18} /></span><span className="lg:hidden"><Logo /></span></> : <Logo />}<button onClick={onClose} className="grid size-9 place-items-center rounded-lg text-slate-400 hover:bg-slate-100 lg:hidden" aria-label="Close navigation"><X size={18} /></button>{onCollapsedChange && <button onClick={() => onCollapsedChange(!collapsed)} className="hidden size-9 place-items-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-indigo-600 lg:grid" aria-label={collapsed ? "Expand dashboard navigation" : "Collapse dashboard navigation"} title={collapsed ? "Expand dashboard navigation" : "Collapse dashboard navigation"}>{collapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}</button>}</div>
        <div className={`mt-7 flex items-center gap-2 rounded-xl border border-indigo-100 bg-indigo-50/70 px-3 py-2.5 dark:border-indigo-900 dark:bg-indigo-950/40 ${collapsed ? "lg:justify-center lg:px-1" : ""}`}><span className="grid size-8 shrink-0 place-items-center rounded-lg bg-indigo-600 text-white"><GraduationCap size={16} /></span><div className={`min-w-0 ${collapsed ? "lg:hidden" : ""}`}><strong className="block text-xs text-indigo-950 dark:text-indigo-100">Personal workspace</strong><span className="block truncate text-[10px] text-indigo-500">Private learning data</span></div></div>
        <nav className="mt-6 grid gap-1" aria-label="Main navigation">
          {navigation.map(([Icon, label, , href]) => <Link key={label} href={href} onClick={onClose} title={collapsed ? label : undefined} className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-semibold ${collapsed ? "lg:justify-center lg:px-2" : ""} ${currentPath === href || (href !== "/dashboard" && currentPath.startsWith(href)) || (href === "/billing" && currentPath === "/pricing") ? "bg-indigo-50 text-indigo-700" : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"}`}><Icon size={18} className="shrink-0" /><span className={collapsed ? "lg:hidden" : ""}>{label}</span></Link>)}
        </nav>
        <div className={`mt-auto rounded-2xl bg-slate-950 p-4 text-white ${collapsed ? "lg:p-2" : ""}`}><span className="grid size-9 place-items-center rounded-xl bg-violet-500/20 text-violet-300"><Sparkles size={18} /></span><div className={collapsed ? "lg:hidden" : ""}><strong className="mt-3 block text-sm">AI tutor</strong><p className="mt-1 text-[11px] leading-5 text-slate-400">Grounded AI arrives after the learning and knowledge domains.</p><span className="mt-3 inline-block rounded-full bg-white/10 px-2 py-1 text-[9px] font-bold uppercase tracking-wide text-slate-300">Planned</span></div></div>
        <button onClick={onLogout} title={collapsed ? "Sign out" : undefined} className={`mt-2 flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-slate-500 hover:bg-rose-50 hover:text-rose-700 ${collapsed ? "lg:justify-center lg:px-2" : ""}`}><LogOut size={17} /><span className={collapsed ? "lg:hidden" : ""}>Sign out</span></button>
      </aside>
    </>
  );
}
