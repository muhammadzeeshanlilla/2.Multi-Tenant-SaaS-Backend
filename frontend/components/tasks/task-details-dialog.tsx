"use client";

import { useEffect, useState } from "react";
import { CalendarDays } from "lucide-react";
import { Alert } from "@/components/ui/alert";
import { Avatar } from "@/components/ui/avatar";
import { Dialog } from "@/components/ui/dialog";
import { PriorityBadge, TaskStatusBadge } from "@/components/ui/entity-badges";
import { Skeleton } from "@/components/ui/skeleton";
import { normalizeApiError } from "@/lib/api-error";
import { formatDate } from "@/lib/format";
import { taskService } from "@/services/task-service";
import type { Task } from "@/types/api";

export function TaskDetailsDialog({ taskId, onClose }: { taskId: number; onClose(): void }) {
  const [task, setTask] = useState<Task | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { let active = true; taskService.get(taskId).then((result) => { if (active) setTask(result); }).catch((requestError) => { if (active) setError(normalizeApiError(requestError).message); }); return () => { active = false; }; }, [taskId]);
  return <Dialog open title="Task details" description="Tenant-scoped task information from the API." onClose={onClose}>{error ? <Alert>{error}</Alert> : !task ? <div className="space-y-3"><Skeleton className="h-20" /><Skeleton className="h-40" /></div> : <div className="space-y-5"><div><div className="flex flex-wrap items-center gap-2"><h3 className="text-xl font-bold text-slate-950">{task.title}</h3><TaskStatusBadge status={task.status} /><PriorityBadge priority={task.priority} /></div><p className="mt-3 text-sm leading-6 text-slate-600">{task.description || "No description provided."}</p></div><dl className="grid gap-4 rounded-xl bg-slate-50 p-4 sm:grid-cols-2"><div><dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Project</dt><dd className="mt-1 text-sm font-semibold text-slate-800">{task.project.name}</dd></div><div><dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Due date</dt><dd className="mt-1 flex items-center gap-1.5 text-sm text-slate-700"><CalendarDays className="size-4" />{task.due_date ? formatDate(task.due_date) : "No due date"}</dd></div><div><dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Assignee</dt><dd className="mt-2">{task.assigned_to ? <span className="inline-flex items-center gap-2 text-sm text-slate-700"><Avatar name={task.assigned_to.username} size="sm" />{task.assigned_to.username}</span> : <span className="text-sm text-slate-500">Unassigned</span>}</dd></div><div><dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Created by</dt><dd className="mt-1 text-sm text-slate-700">{task.created_by?.username ?? "Unknown"}</dd></div><div><dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Created</dt><dd className="mt-1 text-sm text-slate-700">{formatDate(task.created_at)}</dd></div><div><dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Last updated</dt><dd className="mt-1 text-sm text-slate-700">{formatDate(task.updated_at)}</dd></div></dl></div>}</Dialog>;
}
