"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ClipboardCheck, FolderKanban, LayoutDashboard, ScrollText, Users, X } from "lucide-react";
import { Brand } from "@/components/layout/brand";
import { useAuth } from "@/hooks/use-auth";
import { cn } from "@/lib/cn";

const items = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, roles: ["ADMIN", "MANAGER", "EMPLOYEE"] },
  { href: "/projects", label: "Projects", icon: FolderKanban, roles: ["ADMIN", "MANAGER", "EMPLOYEE"] },
  { href: "/tasks", label: "Tasks", icon: ClipboardCheck, roles: ["ADMIN", "MANAGER", "EMPLOYEE"] },
  { href: "/users", label: "Users", icon: Users, roles: ["ADMIN"] },
  { href: "/audit-logs", label: "Audit logs", icon: ScrollText, roles: ["ADMIN"] },
] as const;

export function Sidebar({ open, onClose }: { open: boolean; onClose(): void }) {
  const pathname = usePathname();
  const { role, company } = useAuth();
  const navigation = items.filter((item) => role && (item.roles as readonly string[]).includes(role));
  return <><button aria-label="Close navigation" onClick={onClose} className={cn("fixed inset-0 z-40 bg-slate-950/40 transition lg:hidden", open ? "block" : "hidden")} /><aside className={cn("fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-slate-200 bg-white transition-transform duration-200 lg:translate-x-0", open ? "translate-x-0" : "-translate-x-full")}><div className="flex h-20 items-center justify-between px-6"><Brand /><button onClick={onClose} aria-label="Close menu" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden"><X className="size-5" /></button></div><nav className="flex-1 space-y-1 px-4 py-4" aria-label="Primary navigation">{navigation.map(({ href, label, icon: Icon }) => { const active = pathname === href; return <Link key={href} href={href} onClick={onClose} aria-current={active ? "page" : undefined} className={cn("flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition", active ? "bg-indigo-50 text-indigo-700" : "text-slate-600 hover:bg-slate-50 hover:text-slate-950")}><Icon className="size-5" />{label}</Link>; })}</nav><div className="m-4 rounded-xl bg-slate-50 p-4"><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Workspace</p><p className="mt-1 truncate text-sm font-semibold text-slate-800">{company?.name ?? "TenantFlow"}</p><p className="mt-1 text-xs text-slate-500">Data is isolated to your company.</p></div></aside></>;
}
