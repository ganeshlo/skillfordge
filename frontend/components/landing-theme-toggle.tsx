"use client";

import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

export function LandingThemeToggle() {
  const [dark, setDark] = useState(false);
  useEffect(() => {
    const task = window.setTimeout(() => setDark(document.documentElement.classList.contains("dark")), 0);
    return () => window.clearTimeout(task);
  }, []);
  function toggle() {
    const next = !dark;
    setDark(next);
    window.localStorage.setItem("learnos-theme", next ? "dark" : "light");
    document.documentElement.classList.toggle("dark", next);
    document.documentElement.style.colorScheme = next ? "dark" : "light";
  }
  return <button onClick={toggle} className="grid size-10 place-items-center rounded-xl border border-slate-200 bg-white/80 text-slate-600 shadow-sm backdrop-blur hover:-translate-y-0.5 hover:border-indigo-300 dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-200" aria-label={`Switch to ${dark ? "light" : "dark"} theme`}>{dark ? <Sun size={17} /> : <Moon size={17} />}</button>;
}

