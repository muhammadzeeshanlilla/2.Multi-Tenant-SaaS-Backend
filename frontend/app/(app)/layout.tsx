import { ProtectedRoute } from "@/components/auth/auth-guard";
import { AppShell } from "@/components/layout/app-shell";

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  return <ProtectedRoute><AppShell>{children}</AppShell></ProtectedRoute>;
}
