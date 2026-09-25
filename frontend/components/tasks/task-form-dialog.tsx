"use client";

import { useEffect, useMemo, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm, useWatch } from "react-hook-form";
import { z } from "zod";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { normalizeApiError } from "@/lib/api-error";
import { useToast } from "@/providers/toast-provider";
import { projectService } from "@/services/project-service";
import { taskService } from "@/services/task-service";
import type { Project, Task, TaskMutationRequest } from "@/types/api";

const schema = z.object({
  project_id: z.string().min(1, "Project is required."),
  title: z.string().trim().min(1, "Task title is required.").max(255),
  description: z.string(),
  assigned_to_id: z.string(),
  status: z.enum(["PENDING", "IN_PROGRESS", "COMPLETED"]),
  priority: z.enum(["LOW", "MEDIUM", "HIGH", "URGENT"]),
  due_date: z.string(),
});
type Values = z.infer<typeof schema>;

export function TaskFormDialog({ open, task, onClose, onSaved }: { open: boolean; task?: Task | null; onClose(): void; onSaved(): void }) {
  const { notify } = useToast();
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [formError, setFormError] = useState<string | null>(null);
  const { control, register, handleSubmit, reset, setError, setValue, formState: { errors, isSubmitting } } = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { project_id: "", title: "", description: "", assigned_to_id: "", status: "PENDING", priority: "MEDIUM", due_date: "" } });
  const projectId = useWatch({ control, name: "project_id" });
  const assigneeId = useWatch({ control, name: "assigned_to_id" });
  const selectedProject = useMemo(() => projects.find((project) => String(project.id) === projectId), [projectId, projects]);

  useEffect(() => {
    let active = true;
    projectService.listAll().then((result) => { if (active) setProjects(result); }).catch((requestError) => { if (active) setFormError(normalizeApiError(requestError).message); }).finally(() => { if (active) setProjectsLoading(false); });
    return () => { active = false; };
  }, []);
  useEffect(() => { reset(task ? { project_id: String(task.project.id), title: task.title, description: task.description ?? "", assigned_to_id: task.assigned_to ? String(task.assigned_to.id) : "", status: task.status, priority: task.priority, due_date: task.due_date ?? "" } : { project_id: "", title: "", description: "", assigned_to_id: "", status: "PENDING", priority: "MEDIUM", due_date: "" }); }, [open, reset, task]);
  useEffect(() => { if (assigneeId && selectedProject && !selectedProject.members.some((member) => String(member.id) === assigneeId)) setValue("assigned_to_id", ""); }, [assigneeId, selectedProject, setValue]);

  async function submit(values: Values) {
    setFormError(null);
    const payload: TaskMutationRequest = { project_id: Number(values.project_id), title: values.title, description: values.description || "", assigned_to_id: values.assigned_to_id ? Number(values.assigned_to_id) : null, status: values.status, priority: values.priority, due_date: values.due_date || null };
    try { if (task) await taskService.update(task.id, payload); else await taskService.create(payload); notify(task ? "Task updated successfully." : "Task created successfully."); onSaved(); onClose(); }
    catch (error) { const normalized = normalizeApiError(error); for (const [field, messages] of Object.entries(normalized.fields)) if (field in values) setError(field as keyof Values, { message: messages[0] }); setFormError(normalized.message); }
  }
  return <Dialog open={open} onClose={onClose} title={task ? "Edit task" : "Create task"} description="Assignees are limited to active members of the selected project.">{formError && <Alert className="mb-4">{formError}</Alert>}{projectsLoading ? <div className="space-y-3"><Skeleton className="h-12" /><Skeleton className="h-12" /><Skeleton className="h-24" /></div> : projects.length === 0 ? <Alert>No accessible active project is available. Create or join a project before creating tasks.</Alert> : <form onSubmit={handleSubmit(submit)} className="space-y-4" noValidate><Select label="Project" error={errors.project_id?.message} {...register("project_id")}><option value="">Select a project</option>{projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}</Select><Input label="Task title" error={errors.title?.message} {...register("title")} /><Textarea label="Description (optional)" error={errors.description?.message} {...register("description")} /><Select label="Assignee" error={errors.assigned_to_id?.message} {...register("assigned_to_id")}><option value="">Unassigned</option>{selectedProject?.members.map((member) => <option key={member.id} value={member.id}>{member.username} · {member.role}</option>)}</Select><div className="grid gap-4 sm:grid-cols-2"><Select label="Status" error={errors.status?.message} {...register("status")}><option value="PENDING">Pending</option><option value="IN_PROGRESS">In Progress</option><option value="COMPLETED">Completed</option></Select><Select label="Priority" error={errors.priority?.message} {...register("priority")}><option value="LOW">Low</option><option value="MEDIUM">Medium</option><option value="HIGH">High</option><option value="URGENT">Urgent</option></Select></div><Input label="Due date (optional)" type="date" error={errors.due_date?.message} {...register("due_date")} /><div className="flex justify-end gap-3 pt-2"><Button type="button" variant="secondary" onClick={onClose}>Cancel</Button><Button type="submit" isLoading={isSubmitting}>{task ? "Save task" : "Create task"}</Button></div></form>}</Dialog>;
}
