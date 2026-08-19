import { AppLayout } from "@/components/app-layout";
import type { User } from "@/lib/types";

export function CodeAppLayout({ user, children, immersive = false }: { user: User | null; children: React.ReactNode; immersive?: boolean }) {
  return <AppLayout user={user} currentPath="/code" initiallyCollapsed contentClassName={immersive ? "flex h-screen flex-col overflow-hidden" : ""}>{children}</AppLayout>;
}
