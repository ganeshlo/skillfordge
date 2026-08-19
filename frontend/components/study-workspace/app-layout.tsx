import { AppLayout } from "@/components/app-layout";
import type { User } from "@/lib/types";

export function StudyAppLayout({ user, children, focused = false }: { user: User | null; children: React.ReactNode; focused?: boolean }) {
  if (focused) return <main className="min-h-screen bg-slate-950">{children}</main>;
  return <AppLayout user={user} currentPath="/study">{children}</AppLayout>;
}
