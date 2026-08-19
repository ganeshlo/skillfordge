export function DashboardSkeleton() {
  return <div className="mx-auto max-w-7xl animate-pulse p-5 sm:p-8"><div className="h-4 w-36 rounded bg-slate-200" /><div className="mt-4 h-10 w-80 max-w-full rounded bg-slate-200" /><div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{Array.from({ length: 4 }, (_, index) => <div key={index} className="h-36 rounded-2xl bg-white ring-1 ring-slate-200" />)}</div><div className="mt-6 grid gap-6 lg:grid-cols-[1.45fr_.8fr]"><div className="h-80 rounded-2xl bg-white ring-1 ring-slate-200" /><div className="h-80 rounded-2xl bg-white ring-1 ring-slate-200" /></div></div>;
}

