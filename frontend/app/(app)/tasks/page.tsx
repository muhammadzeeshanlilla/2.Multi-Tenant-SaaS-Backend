"use client";

import { useEffect, useMemo, useState } from "react";
import { CalendarDays, ClipboardCheck, Ellipsis, Pencil, Plus, RefreshCw, Trash2 } from "lucide-react";
import { Alert } from "@/components/ui/alert";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ConfirmationDialog } from "@/components/ui/dialog";
import { Dropdown, DropdownItem } from "@/components/ui/dropdown";
import { EmptyState } from "@/components/ui/empty-state";
import { PriorityBadge, TaskStatusBadge } from "@/components/ui/entity-badges";
import { Pagination } from "@/components/ui/pagination";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, Td, Th } from "@/components/ui/table";
import { TaskDetailsDialog } from "@/components/tasks/task-details-dialog";
import { TaskFormDialog } from "@/components/tasks/task-form-dialog";
import { TaskStatusDialog } from "@/components/tasks/task-status-dialog";
import { useAuth } from "@/hooks/use-auth";
import { normalizeApiError } from "@/lib/api-error";
import { formatDate } from "@/lib/format";
import { useToast } from "@/providers/toast-provider";
import { projectService } from "@/services/project-service";
import { taskService } from "@/services/task-service";
import type { PaginatedResponse, Project, Task, TaskStatus, UserSummary } from "@/types/api";

const PAGE_SIZE = 10;

export default function TasksPage() {
  const { role } = useAuth();
  const { notify } = useToast();
  const canManage = role === "ADMIN" || role === "MANAGER";
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<TaskStatus | "">("");
  const [projectId, setProjectId] = useState("");
  const [assigneeId, setAssigneeId] = useState("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [result, setResult] = useState<PaginatedResponse<Task> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Task | null>(null);
  const [statusFor, setStatusFor] = useState<Task | null>(null);
  const [detailsId, setDetailsId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState<Task | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => { let active = true; projectService.listAll().then((response) => { if (active) setProjects(response); }).catch(() => undefined); return () => { active = false; }; }, [reloadKey]);
  useEffect(() => {
    let active = true;
    const assignee = assigneeId === "null" ? "null" : assigneeId ? Number(assigneeId) : undefined;
    taskService.list({ page, page_size: PAGE_SIZE, ...(status ? { status } : {}), ...(projectId ? { project: Number(projectId) } : {}), ...(assignee !== undefined ? { assignee } : {}) }).then((response) => { if (active) { setResult(response); setError(null); } }).catch((requestError) => { if (active) setError(normalizeApiError(requestError).message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [assigneeId, page, projectId, reloadKey, status]);
  const assignees = useMemo(() => { const map = new Map<number, UserSummary>(); for (const project of projects) for (const member of project.members) map.set(member.id, member); return [...map.values()].sort((a, b) => a.username.localeCompare(b.username)); }, [projects]);
  function changeFilter(update: () => void) { setLoading(true); setPage(1); update(); }
  function reload() { setLoading(true); setReloadKey((value) => value + 1); }
  async function remove() {
    if (!deleting) return;
    setIsDeleting(true);
    try { await taskService.softDelete(deleting.id); notify("Task deleted successfully."); setDeleting(null); if (result?.data.length === 1 && page > 1) setPage((value) => value - 1); else reload(); }
    catch (requestError) { notify(normalizeApiError(requestError).message, "error"); }
    finally { setIsDeleting(false); }
  }

  const tasks = result?.data ?? [];
  return <div className="space-y-6"><header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-sm font-semibold text-indigo-700">Workspace</p><h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">Tasks</h1><p className="mt-2 text-sm text-slate-500">{role === "EMPLOYEE" ? "Tasks assigned to you across active projects." : "Coordinate project assignments, priorities, and progress."}</p></div>{canManage && <Button onClick={() => { setEditing(null); setFormOpen(true); }}><Plus className="size-4" />Create task</Button>}</header><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3"><Select label="Task status" value={status} onChange={(event) => changeFilter(() => setStatus(event.target.value as TaskStatus | ""))}><option value="">All statuses</option><option value="PENDING">Pending</option><option value="IN_PROGRESS">In Progress</option><option value="COMPLETED">Completed</option></Select><Select label="Project" value={projectId} onChange={(event) => changeFilter(() => setProjectId(event.target.value))}><option value="">All projects</option>{projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}</Select>{canManage && <Select label="Assignee" value={assigneeId} onChange={(event) => changeFilter(() => setAssigneeId(event.target.value))}><option value="">All assignees</option><option value="null">Unassigned</option>{assignees.map((user) => <option key={user.id} value={user.id}>{user.username}</option>)}</Select>}</div>{error && <Alert>{error}</Alert>}<Card className="overflow-hidden">{loading ? <div className="space-y-3 p-5">{Array.from({ length: 6 }).map((_, index) => <Skeleton key={index} className="h-16" />)}</div> : tasks.length === 0 ? <div className="p-5"><EmptyState icon={ClipboardCheck} title="No tasks found" description="No tasks match the current role scope and server-side filters." action={canManage && !status && !projectId && !assigneeId ? <Button onClick={() => setFormOpen(true)}><Plus className="size-4" />Create task</Button> : undefined} /></div> : <><div className="hidden p-5 lg:block"><Table><thead><tr><Th>Task</Th><Th>Project</Th><Th>Assignee</Th><Th>Status</Th><Th>Priority</Th><Th>Due</Th><Th><span className="sr-only">Actions</span></Th></tr></thead><tbody>{tasks.map((task) => <tr key={task.id}><Td><button onClick={() => setDetailsId(task.id)} className="max-w-56 truncate font-semibold text-slate-900 hover:text-indigo-700">{task.title}</button></Td><Td>{task.project.name}</Td><Td>{task.assigned_to ? <span className="inline-flex items-center gap-2"><Avatar name={task.assigned_to.username} size="sm" />{task.assigned_to.username}</span> : <span className="text-slate-400">Unassigned</span>}</Td><Td><TaskStatusBadge status={task.status} /></Td><Td><PriorityBadge priority={task.priority} /></Td><Td>{task.due_date ? formatDate(task.due_date) : "—"}</Td><Td><TaskActions task={task} canManage={canManage} onView={() => setDetailsId(task.id)} onStatus={() => setStatusFor(task)} onEdit={() => { setEditing(task); setFormOpen(true); }} onDelete={() => setDeleting(task)} /></Td></tr>)}</tbody></Table></div><div className="divide-y divide-slate-100 lg:hidden">{tasks.map((task) => <article key={task.id} className="p-4"><div className="flex items-start justify-between gap-3"><div className="min-w-0"><button onClick={() => setDetailsId(task.id)} className="block max-w-full truncate text-left font-semibold text-slate-900">{task.title}</button><p className="mt-1 truncate text-sm text-slate-500">{task.project.name}</p></div><TaskActions task={task} canManage={canManage} onView={() => setDetailsId(task.id)} onStatus={() => setStatusFor(task)} onEdit={() => { setEditing(task); setFormOpen(true); }} onDelete={() => setDeleting(task)} /></div><div className="mt-3 flex flex-wrap gap-2"><TaskStatusBadge status={task.status} /><PriorityBadge priority={task.priority} /></div><div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500"><span>{task.assigned_to ? `Assigned to ${task.assigned_to.username}` : "Unassigned"}</span><span className="flex items-center gap-1"><CalendarDays className="size-3.5" />{task.due_date ? formatDate(task.due_date) : "No due date"}</span></div></article>)}</div><div className="border-t border-slate-100 px-5"><Pagination count={result?.count ?? 0} page={page} pageSize={PAGE_SIZE} hasNext={Boolean(result?.next)} hasPrevious={Boolean(result?.previous)} onPageChange={(next) => { setLoading(true); setPage(next); }} /></div></>}</Card>{canManage && <TaskFormDialog open={formOpen} task={editing} onClose={() => { setFormOpen(false); setEditing(null); }} onSaved={reload} />}{statusFor && <TaskStatusDialog key={statusFor.id} task={statusFor} onClose={() => setStatusFor(null)} onSaved={reload} />}{detailsId && <TaskDetailsDialog key={detailsId} taskId={detailsId} onClose={() => setDetailsId(null)} />}<ConfirmationDialog open={Boolean(deleting)} title="Delete this task?" description={`${deleting?.title ?? "This task"} will be soft-deleted and removed from normal task views.`} confirmLabel="Delete task" isLoading={isDeleting} onClose={() => setDeleting(null)} onConfirm={() => void remove()} /></div>;
}

function TaskActions({ task, canManage, onView, onStatus, onEdit, onDelete }: { task: Task; canManage: boolean; onView(): void; onStatus(): void; onEdit(): void; onDelete(): void }) {
  return <Dropdown trigger={<span className="grid size-9 place-items-center rounded-lg text-slate-500 hover:bg-slate-100"><Ellipsis className="size-5" /><span className="sr-only">Actions for {task.title}</span></span>}><DropdownItem onClick={onView}>View details</DropdownItem><DropdownItem onClick={onStatus}><RefreshCw className="size-4" />Update status</DropdownItem>{canManage && <><DropdownItem onClick={onEdit}><Pencil className="size-4" />Edit task</DropdownItem><DropdownItem onClick={onDelete}><Trash2 className="size-4 text-rose-600" />Delete task</DropdownItem></>}</Dropdown>;
}
