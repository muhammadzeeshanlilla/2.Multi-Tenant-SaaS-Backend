import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/providers/auth-provider";
import { ToastProvider } from "@/providers/toast-provider";

export const metadata: Metadata = {
  title: { default: "TenantFlow", template: "%s | TenantFlow" },
  description: "A secure multi-tenant workspace for teams, projects, and tasks.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><ToastProvider><AuthProvider>{children}</AuthProvider></ToastProvider></body></html>;
}
