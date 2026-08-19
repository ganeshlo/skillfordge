import { Orbit } from "lucide-react";
import Link from "next/link";

export function Logo({ inverse = false }: { inverse?: boolean }) {
  return (
    <Link href="/" className={`inline-flex items-center gap-2.5 font-black tracking-[-0.04em] ${inverse ? "text-white" : "text-slate-950"}`}>
      <span className="learnos-gradient grid size-9 place-items-center rounded-xl text-white shadow-lg shadow-indigo-200/60"><Orbit size={20} /></span>
      <span className="text-xl">Learn<span className={inverse ? "text-indigo-200" : "text-indigo-600"}>OS</span></span>
    </Link>
  );
}

