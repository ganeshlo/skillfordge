import { AppLayout } from "@/components/app-layout";
import type { User } from "@/lib/types";

export function BillingAppLayout({ user, children }: { user: User | null; children: React.ReactNode }) {
  return <AppLayout user={user} currentPath="/billing">{children}</AppLayout>;
}
