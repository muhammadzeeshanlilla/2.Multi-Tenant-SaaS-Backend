"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Activity, ArrowRight, ClipboardCheck, FolderKanban, Plus, Users } from "lucide-react";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/use-auth";
import { normalizeApiError } from "@/lib/api-error";
import { formatDateTime, humanizeAction } from "@/lib/format";
import { auditService } from "@/services/audit-service";
import { projectService } from "@/services/project-service";
import { taskService } from "@/services/task-service";
import { userService } from "@/services/user-service";
import type { AuditLog } from "@/types/api";

interface DashboardData { users: number; projects: number; tasks: number; activity: AuditLog[] }

export function AdminDashboard() {
  const { user, company } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        setError(null);
        const [users, projects, tasks, audit] = await Promise.all([
          userService.list(1, 1),
          projectService.list({ page: 1, page_size: 1 }),
          taskService.list({ page: 1, page_size: 1 }),
          auditService.list({ page: 1, page_size: 5 }),
        ]);
        if (active) setData({ users: users.count, projects: projects.count, tasks: tasks.count, activity: audit.data });
      } catch (requestError) {
        if (active) setError(normalizeApiError(requestError).message);
      }
    }
    void load();
    return () => { active = false; };
  }, []);

  const cards = data ? [
    { label: "Company users", value: data.users, icon: Users, color: "bg-indigo-50 text-indigo-700" },
    { label: "Projects", value: data.projects, icon: FolderKanban, color: "bg-sky-50 text-sky-700" },
    { label: "Tasks", value: data.tasks, icon: ClipboardCheck, color: "bg-emerald-50 text-emerald-700" },
  ] : [];

  return <div className="space-y-8"><section className="flex flex-col gap-6 overflow-hidden rounded-3xl bg-slate-950 px-6 py-8 text-white shadow-sm sm:px-8 sm:py-10 lg:flex-row lg:items-end lg:justify-between"><div><Badge className="bg-white/10 text-indigo-200">ADMIN</Badge><h1 className="mt-5 text-3xl font-bold tracking-tight sm:text-4xl">Good to see you, {user?.username}.</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300 sm:text-base">Here’s the current operational overview for <strong className="font-semibold text-white">{company?.name}</strong>.</p></div><Link href="/users" className="inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-lg bg-white px-4 py-2 text-sm font-semibold text-slate-950 shadow-sm hover:bg-indigo-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white sm:w-auto"><Plus className="size-4" />Manage users</Link></section>{error && <Alert>{error}</Alert>}<section aria-labelledby="summary-title"><div className="mb-4"><p className="text-sm font-semibold text-indigo-700">Live overview</p><h2 id="summary-title" className="mt-1 text-2xl font-bold tracking-tight text-slate-950">Company summary</h2></div>{data ? <div className="grid gap-4 sm:grid-cols-3">{cards.map(({ label, value, icon: Icon, color }) => <Card key={label} className="p-5"><div className="flex items-center justify-between"><span className={`rounded-xl p-3 ${color}`}><Icon className="size-5" /></span><span className="text-3xl font-bold tracking-tight text-slate-950">{value}</span></div><p className="mt-5 text-sm font-medium text-slate-600">{label}</p></Card>)}</div> : <div className="grid gap-4 sm:grid-cols-3"><Skeleton className="h-32" /><Skeleton className="h-32" /><Skeleton className="h-32" /></div>}</section><div className="grid gap-6 xl:grid-cols-[minmax(0,1.5fr)_minmax(280px,0.7fr)]"><Card className="overflow-hidden"><div className="flex items-center justify-between border-b border-slate-100 px-5 py-4"><div><h2 className="font-semibold text-slate-950">Recent activity</h2><p className="text-sm text-slate-500">Latest tenant audit entries</p></div><Activity className="size-5 text-slate-400" /></div><div className="divide-y divide-slate-100">{!data ? Array.from({ length: 4 }).map((_, index) => <div key={index} className="p-4"><Skeleton className="h-5 w-2/3" /><Skeleton className="mt-2 h-4 w-1/3" /></div>) : data.activity.length ? data.activity.map((entry) => <div key={entry.id} className="flex gap-3 px-5 py-4"><span className="mt-1 size-2 shrink-0 rounded-full bg-indigo-500" /><div className="min-w-0"><p className="text-sm font-medium text-slate-800">{entry.description || humanizeAction(entry.action)}</p><p className="mt-1 text-xs text-slate-500">{entry.user?.username ?? "System"} · {formatDateTime(entry.created_at)}</p></div></div>) : <p className="px-5 py-10 text-center text-sm text-slate-500">No audit activity has been recorded yet.</p>}</div></Card><Card className="p-5"><h2 className="font-semibold text-slate-950">Quick actions</h2><p className="mt-1 text-sm text-slate-500">Move directly to supported areas.</p><div className="mt-5 space-y-2">{[{ href: "/users", label: "Manage users", icon: Users }, { href: "/projects", label: "View projects", icon: FolderKanban }, { href: "/tasks", label: "View tasks", icon: ClipboardCheck }].map(({ href, label, icon: Icon }) => <Link key={label} href={href} className="flex items-center justify-between rounded-xl border border-slate-200 px-3 py-3 text-sm font-semibold text-slate-700 hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700"><span className="flex items-center gap-3"><Icon className="size-4" />{label}</span><ArrowRight className="size-4" /></Link>)}</div></Card></div></div>;
}
