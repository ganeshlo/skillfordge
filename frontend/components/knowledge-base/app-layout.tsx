import { AppLayout } from "@/components/app-layout";
import type { User } from "@/lib/types";

export function KnowledgeAppLayout({
  user,
  children,
}: {
  user: User | null;
  children: React.ReactNode;
}) {
  return <AppLayout user={user} currentPath="/knowledge" className="bg-slate-50 dark:bg-slate-950">{children}</AppLayout>;
}
