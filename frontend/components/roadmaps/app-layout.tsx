import { AppLayout } from "@/components/app-layout";
import type { User } from "@/lib/types";

export function RoadmapAppLayout({ user, children }: { user: User | null; children: React.ReactNode }) {
  return <AppLayout user={user} currentPath="/roadmaps">{children}</AppLayout>;
}
