"use client";

import { useEffect, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { normalizeApiError } from "@/lib/api-error";
import { useToast } from "@/providers/toast-provider";
import { projectService } from "@/services/project-service";
import type { Project, ProjectMutationRequest } from "@/types/api";

const schema = z.object({
  name: z.string().trim().min(1, "Project name is required.").max(255),
  description: z.string(),
  status: z.enum(["PLANNING", "ACTIVE", "COMPLETED", "CANCELLED"]),
  start_date: z.string(),
  end_date: z.string(),
}).refine((data) => !data.start_date || !data.end_date || data.end_date >= data.start_date, { path: ["end_date"], message: "End date cannot be before start date." });
type Values = z.infer<typeof schema>;

export function ProjectFormDialog({ open, project, onClose, onSaved }: { open: boolean; project?: Project | null; onClose(): void; onSaved(): void }) {
  const { notify } = useToast();
  const [formError, setFormError] = useState<string | null>(null);
  const { register, handleSubmit, reset, setError, formState: { errors, isSubmitting } } = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { name: "", description: "", status: "PLANNING", start_date: "", end_date: "" } });
  useEffect(() => { reset(project ? { name: project.name, description: project.description ?? "", status: project.status, start_date: project.start_date ?? "", end_date: project.end_date ?? "" } : { name: "", description: "", status: "PLANNING", start_date: "", end_date: "" }); }, [project, reset, open]);
  async function submit(values: Values) {
    setFormError(null);
    const payload: ProjectMutationRequest = { ...values, description: values.description || "", start_date: values.start_date || null, end_date: values.end_date || null };
    try {
      if (project) await projectService.update(project.id, payload); else await projectService.create(payload);
      notify(project ? "Project updated successfully." : "Project created successfully.");
      onSaved(); onClose();
    } catch (error) {
      const normalized = normalizeApiError(error);
      for (const [field, messages] of Object.entries(normalized.fields)) if (field in values) setError(field as keyof Values, { message: messages[0] });
      setFormError(normalized.message);
    }
  }
  return <Dialog open={open} onClose={onClose} title={project ? "Edit project" : "Create project"} description="Project fields and date rules match the Django API contract."><form onSubmit={handleSubmit(submit)} className="space-y-4" noValidate>{formError && <Alert>{formError}</Alert>}<Input label="Project name" error={errors.name?.message} {...register("name")} /><Textarea label="Description (optional)" error={errors.description?.message} {...register("description")} /><Select label="Status" error={errors.status?.message} {...register("status")}><option value="PLANNING">Planning</option><option value="ACTIVE">Active</option><option value="COMPLETED">Completed</option><option value="CANCELLED">Cancelled</option></Select><div className="grid gap-4 sm:grid-cols-2"><Input label="Start date (optional)" type="date" error={errors.start_date?.message} {...register("start_date")} /><Input label="End date (optional)" type="date" error={errors.end_date?.message} {...register("end_date")} /></div><div className="flex justify-end gap-3 pt-2"><Button type="button" variant="secondary" onClick={onClose}>Cancel</Button><Button type="submit" isLoading={isSubmitting}>{project ? "Save project" : "Create project"}</Button></div></form></Dialog>;
}
