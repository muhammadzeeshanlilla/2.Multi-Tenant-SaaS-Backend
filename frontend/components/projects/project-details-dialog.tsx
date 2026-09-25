"use client";

import { useEffect, useState } from "react";
import { CalendarDays, ClipboardCheck, Users } from "lucide-react";
import { Alert } from "@/components/ui/alert";
import { Avatar } from "@/components/ui/avatar";
import { Dialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { ProjectStatusBadge, TaskStatusBadge } from "@/components/ui/entity-badges";
import { Skeleton } from "@/components/ui/skeleton";
import { normalizeApiError } from "@/lib/api-error";
import { formatDate } from "@/lib/format";
import { projectService } from "@/services/project-service";
import { taskService } from "@/services/task-service";
import type { Project, Task } from "@/types/api";

interface Details { project: Project; tasks: Task[]; taskCount: number }

export function ProjectDetailsDialog({ projectId, onClose }: { projectId: number; onClose(): void }) {
  const [details, setDetails] = useState<Details | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    Promise.all([projectService.get(projectId), taskService.list({ project: projectId, page: 1, page_size: 5 })]).then(([project, tasks]) => { if (active) setDetails({ project, tasks: tasks.data, taskCount: tasks.count }); }).catch((requestError) => { if (active) setError(normalizeApiError(requestError).message); });
    return () => { active = false; };
  }, [projectId]);
  return <Dialog open title="Project details" description="Project, membership, and associated task information." onClose={onClose}>{error ? <Alert>{error}</Alert> : !details ? <div className="space-y-3"><Skeleton className="h-24" /><Skeleton className="h-36" /></div> : <div className="space-y-6"><div><div className="flex flex-wrap items-center gap-2"><h3 className="text-xl font-bold text-slate-950">{details.project.name}</h3><ProjectStatusBadge status={details.project.status} /></div><p className="mt-2 text-sm leading-6 text-slate-600">{details.project.description || "No description provided."}</p><div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-500"><span className="flex items-center gap-1.5"><CalendarDays className="size-4" />{details.project.start_date ? formatDate(details.project.start_date) : "No start date"} – {details.project.end_date ? formatDate(details.project.end_date) : "No end date"}</span><span>Created by {details.project.created_by?.username ?? "Unknown"}</span></div></div><section><h4 className="flex items-center gap-2 text-sm font-semibold text-slate-900"><Users className="size-4" />Members ({details.project.members.length})</h4><div className="mt-3 flex flex-wrap gap-2">{details.project.members.length ? details.project.members.map((member) => <span key={member.id} className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white py-1 pl-1 pr-3 text-xs text-slate-700"><Avatar name={member.username} size="sm" />{member.username}</span>) : <span className="text-sm text-slate-500">No active members.</span>}</div></section><section><h4 className="flex items-center gap-2 text-sm font-semibold text-slate-900"><ClipboardCheck className="size-4" />Tasks ({details.taskCount})</h4>{details.tasks.length ? <div className="mt-3 divide-y divide-slate-100 rounded-xl border border-slate-200">{details.tasks.map((task) => <div key={task.id} className="flex items-center justify-between gap-3 p-3"><div className="min-w-0"><p className="truncate text-sm font-medium text-slate-800">{task.title}</p><p className="text-xs text-slate-500">{task.assigned_to?.username ?? "Unassigned"}</p></div><TaskStatusBadge status={task.status} /></div>)}</div> : <div className="mt-3"><EmptyState icon={ClipboardCheck} title="No tasks" description="No visible tasks belong to this project." /></div>}</section></div>}</Dialog>;
}
