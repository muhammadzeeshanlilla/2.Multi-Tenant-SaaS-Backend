"use client";

import { useEffect, useState } from "react";
import { ArrowRight, ClipboardCheck, FolderKanban, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { TaskStatusBadge } from "@/components/ui/entity-badges";
import { Skeleton } from "@/components/ui/skeleton";
import { normalizeApiError } from "@/lib/api-error";
import { projectService } from "@/services/project-service";
import { taskService } from "@/services/task-service";
import type { Task, User } from "@/types/api";

interface DashboardData { projects: number; tasks: number; recentTasks: Task[] }

export function RoleDashboard({ user }: { user: User }) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    Promise.all([projectService.list({ page: 1, page_size: 1 }), taskService.list({ page: 1, page_size: 5 })]).then(([projects, tasks]) => { if (active) setData({ projects: projects.count, tasks: tasks.count, recentTasks: tasks.data }); }).catch((requestError) => { if (active) setError(normalizeApiError(requestError).message); });
    return () => { active = false; };
  }, []);
  const copy = user.role === "MANAGER"
    ? { title: "Project coordination", body: "Create and maintain projects, manage membership, and coordinate task delivery." }
    : { title: "Your assigned work", body: "Review projects you belong to and keep the status of your assigned tasks current." };
  const cards = [
    { title: "Projects", body: user.role === "EMPLOYEE" ? "View projects where you are a member." : "Organize work and manage project membership.", href: "/projects", icon: FolderKanban },
    { title: "Tasks", body: user.role === "EMPLOYEE" ? "Review and update your assigned task status." : "Coordinate assignments, priorities, and progress.", href: "/tasks", icon: ClipboardCheck },
  ];
  return <div className="space-y-8"><section className="overflow-hidden rounded-3xl bg-slate-950 px-6 py-8 text-white shadow-sm sm:px-8 sm:py-10"><Badge className="bg-white/10 text-indigo-200">{user.role}</Badge><h1 className="mt-5 text-3xl font-bold tracking-tight sm:text-4xl">Welcome back, {user.username}.</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300 sm:text-base">You’re working in <strong className="font-semibold text-white">{user.company?.name}</strong>. Counts reflect the project and task scope returned for your account.</p></section>{error && <Alert>{error}</Alert>}<section><div className="mb-4 flex items-end justify-between gap-4"><div><p className="text-sm font-semibold text-indigo-700">Your workspace</p><h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-950">{copy.title}</h2><p className="mt-1 text-sm text-slate-500">{copy.body}</p></div><ShieldCheck className="hidden size-8 text-emerald-600 sm:block" /></div>{data ? <div className="grid gap-4 sm:grid-cols-2"><Card className="p-5"><span className="rounded-xl bg-indigo-50 p-3 text-indigo-700 inline-block"><FolderKanban className="size-5" /></span><p className="mt-5 text-3xl font-bold text-slate-950">{data.projects}</p><p className="text-sm text-slate-500">Accessible projects</p></Card><Card className="p-5"><span className="rounded-xl bg-emerald-50 p-3 text-emerald-700 inline-block"><ClipboardCheck className="size-5" /></span><p className="mt-5 text-3xl font-bold text-slate-950">{data.tasks}</p><p className="text-sm text-slate-500">{user.role === "EMPLOYEE" ? "Assigned tasks" : "Company tasks"}</p></Card></div> : <div className="grid gap-4 sm:grid-cols-2"><Skeleton className="h-36" /><Skeleton className="h-36" /></div>}</section><div className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(280px,0.8fr)]"><Card className="overflow-hidden"><div className="border-b border-slate-100 px-5 py-4"><h2 className="font-semibold text-slate-950">Recent tasks</h2><p className="text-sm text-slate-500">Newest tasks visible to your role</p></div>{!data ? <div className="space-y-3 p-5"><Skeleton className="h-12" /><Skeleton className="h-12" /><Skeleton className="h-12" /></div> : data.recentTasks.length ? <div className="divide-y divide-slate-100">{data.recentTasks.map((task) => <div key={task.id} className="flex items-center justify-between gap-3 px-5 py-3"><div className="min-w-0"><p className="truncate text-sm font-semibold text-slate-800">{task.title}</p><p className="truncate text-xs text-slate-500">{task.project.name} · {task.assigned_to?.username ?? "Unassigned"}</p></div><TaskStatusBadge status={task.status} /></div>)}</div> : <p className="p-8 text-center text-sm text-slate-500">No visible tasks yet.</p>}</Card><div className="grid gap-4">{cards.map(({ title, body, href, icon: Icon }) => <Card key={title} className="group p-5 transition hover:border-indigo-200 hover:shadow-md"><div className="flex items-start justify-between"><span className="rounded-xl bg-indigo-50 p-3 text-indigo-700"><Icon className="size-5" /></span><ArrowRight className="size-5 text-slate-300 group-hover:text-indigo-600" /></div><h3 className="mt-4 font-semibold text-slate-950">{title}</h3><p className="mt-1 text-sm text-slate-500">{body}</p><Link href={href} className="mt-4 inline-flex text-sm font-semibold text-indigo-700">Open {title.toLowerCase()}</Link></Card>)}</div></div></div>;
}
