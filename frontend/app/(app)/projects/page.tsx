"use client";

import { useEffect, useState } from "react";
import { CalendarDays, Ellipsis, FolderKanban, Pencil, Plus, Trash2, Users } from "lucide-react";
import { Alert } from "@/components/ui/alert";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ConfirmationDialog } from "@/components/ui/dialog";
import { Dropdown, DropdownItem } from "@/components/ui/dropdown";
import { EmptyState } from "@/components/ui/empty-state";
import { ProjectStatusBadge } from "@/components/ui/entity-badges";
import { Pagination } from "@/components/ui/pagination";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { MemberDialog } from "@/components/projects/member-dialog";
import { ProjectDetailsDialog } from "@/components/projects/project-details-dialog";
import { ProjectFormDialog } from "@/components/projects/project-form-dialog";
import { useAuth } from "@/hooks/use-auth";
import { normalizeApiError } from "@/lib/api-error";
import { formatDate } from "@/lib/format";
import { useToast } from "@/providers/toast-provider";
import { projectService } from "@/services/project-service";
import type { PaginatedResponse, Project, ProjectStatus } from "@/types/api";

const PAGE_SIZE = 9;

export default function ProjectsPage() {
  const { role } = useAuth();
  const { notify } = useToast();
  const canManage = role === "ADMIN" || role === "MANAGER";
  const canManageMembers = role === "ADMIN" || role === "MANAGER";
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<ProjectStatus | "">("");
  const [result, setResult] = useState<PaginatedResponse<Project> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Project | null>(null);
  const [membersFor, setMembersFor] = useState<Project | null>(null);
  const [detailsId, setDetailsId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState<Project | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;
    projectService.list({ page, page_size: PAGE_SIZE, ...(status ? { status } : {}) }).then((response) => { if (active) { setResult(response); setError(null); } }).catch((requestError) => { if (active) setError(normalizeApiError(requestError).message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [page, reloadKey, status]);
  function reload() { setLoading(true); setReloadKey((value) => value + 1); }
  async function remove() {
    if (!deleting) return;
    setIsDeleting(true);
    try { await projectService.softDelete(deleting.id); notify("Project deleted successfully."); setDeleting(null); if (result?.data.length === 1 && page > 1) setPage((value) => value - 1); else reload(); }
    catch (requestError) { notify(normalizeApiError(requestError).message, "error"); }
    finally { setIsDeleting(false); }
  }

  const projects = result?.data ?? [];
  return <div className="space-y-6"><header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-sm font-semibold text-indigo-700">Workspace</p><h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">Projects</h1><p className="mt-2 text-sm text-slate-500">{role === "EMPLOYEE" ? "Projects where you are an active member." : "Plan work, manage membership, and coordinate delivery."}</p></div>{canManage && <Button onClick={() => { setEditing(null); setFormOpen(true); }}><Plus className="size-4" />Create project</Button>}</header><div className="max-w-xs"><Select label="Project status" value={status} onChange={(event) => { setLoading(true); setStatus(event.target.value as ProjectStatus | ""); setPage(1); }}><option value="">All statuses</option><option value="PLANNING">Planning</option><option value="ACTIVE">Active</option><option value="COMPLETED">Completed</option><option value="CANCELLED">Cancelled</option></Select></div>{error && <Alert>{error}</Alert>}{loading ? <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{Array.from({ length: 6 }).map((_, index) => <Skeleton key={index} className="h-64" />)}</div> : projects.length === 0 ? <EmptyState icon={FolderKanban} title="No projects found" description={status ? "No projects match this status filter." : "No projects are currently available to your account."} action={canManage && !status ? <Button onClick={() => setFormOpen(true)}><Plus className="size-4" />Create project</Button> : undefined} /> : <><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{projects.map((project) => <Card key={project.id} className="flex min-w-0 flex-col p-5"><div className="flex items-start justify-between gap-3"><ProjectStatusBadge status={project.status} /><ProjectActions project={project} canManage={canManage} canManageMembers={canManageMembers} onView={() => setDetailsId(project.id)} onEdit={() => { setEditing(project); setFormOpen(true); }} onMembers={() => setMembersFor(project)} onDelete={() => setDeleting(project)} /></div><button onClick={() => setDetailsId(project.id)} className="mt-4 text-left focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"><h2 className="truncate text-lg font-bold text-slate-950 hover:text-indigo-700">{project.name}</h2></button><p className="mt-2 line-clamp-2 min-h-10 text-sm leading-5 text-slate-500">{project.description || "No description provided."}</p><div className="mt-5 flex items-center gap-2 text-xs text-slate-500"><CalendarDays className="size-4" /><span>{project.start_date ? formatDate(project.start_date) : "No start"} – {project.end_date ? formatDate(project.end_date) : "No end"}</span></div><div className="mt-auto flex items-center justify-between border-t border-slate-100 pt-4"><div className="flex -space-x-2">{project.members.slice(0, 4).map((member) => <span key={member.id} title={member.username} className="rounded-full ring-2 ring-white"><Avatar name={member.username} size="sm" /></span>)}{project.members.length > 4 && <span className="grid size-8 place-items-center rounded-full bg-slate-100 text-[10px] font-bold text-slate-600 ring-2 ring-white">+{project.members.length - 4}</span>}</div><span className="text-xs text-slate-500">{project.members.length} member{project.members.length === 1 ? "" : "s"}</span></div></Card>)}</div><Pagination count={result?.count ?? 0} page={page} pageSize={PAGE_SIZE} hasNext={Boolean(result?.next)} hasPrevious={Boolean(result?.previous)} onPageChange={(next) => { setLoading(true); setPage(next); }} /></>}<ProjectFormDialog open={formOpen} project={editing} onClose={() => { setFormOpen(false); setEditing(null); }} onSaved={reload} />{membersFor && <MemberDialog key={membersFor.id} project={membersFor} onClose={() => setMembersFor(null)} onSaved={reload} />}{detailsId && <ProjectDetailsDialog key={detailsId} projectId={detailsId} onClose={() => setDetailsId(null)} />}<ConfirmationDialog open={Boolean(deleting)} title="Delete this project?" description={`${deleting?.name ?? "This project"} will be soft-deleted and removed from normal project and task views. Existing tasks beneath it will no longer be visible.`} confirmLabel="Delete project" isLoading={isDeleting} onClose={() => setDeleting(null)} onConfirm={() => void remove()} /></div>;
}

function ProjectActions({ project, canManage, canManageMembers, onView, onEdit, onMembers, onDelete }: { project: Project; canManage: boolean; canManageMembers: boolean; onView(): void; onEdit(): void; onMembers(): void; onDelete(): void }) {
  return <Dropdown trigger={<span className="grid size-9 place-items-center rounded-lg text-slate-500 hover:bg-slate-100"><Ellipsis className="size-5" /><span className="sr-only">Actions for {project.name}</span></span>}><DropdownItem onClick={onView}>View details</DropdownItem>{canManage && <><DropdownItem onClick={onEdit}><Pencil className="size-4" />Edit project</DropdownItem>{canManageMembers && <DropdownItem onClick={onMembers}><Users className="size-4" />Manage members</DropdownItem>}<DropdownItem onClick={onDelete}><Trash2 className="size-4 text-rose-600" />Delete project</DropdownItem></>}</Dropdown>;
}
