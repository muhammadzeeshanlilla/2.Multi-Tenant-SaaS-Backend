"use client";

import { useState } from "react";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Select } from "@/components/ui/select";
import { normalizeApiError } from "@/lib/api-error";
import { useToast } from "@/providers/toast-provider";
import { taskService } from "@/services/task-service";
import type { Task, TaskStatus } from "@/types/api";

export function TaskStatusDialog({ task, onClose, onSaved }: { task: Task; onClose(): void; onSaved(): void }) {
  const { notify } = useToast();
  const [status, setStatus] = useState<TaskStatus>(task.status);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function save() { setSaving(true); setError(null); try { await taskService.updateStatus(task.id, status); notify("Task status updated."); onSaved(); onClose(); } catch (requestError) { setError(normalizeApiError(requestError).message); } finally { setSaving(false); } }
  return <Dialog open title={`Update status · ${task.title}`} description="Employees may update only tasks assigned to them; the backend remains authoritative." onClose={onClose}>{error && <Alert className="mb-4">{error}</Alert>}<Select label="Task status" value={status} onChange={(event) => setStatus(event.target.value as TaskStatus)}><option value="PENDING">Pending</option><option value="IN_PROGRESS">In Progress</option><option value="COMPLETED">Completed</option></Select><div className="mt-5 flex justify-end gap-3"><Button variant="secondary" onClick={onClose}>Cancel</Button><Button isLoading={saving} onClick={() => void save()}>Update status</Button></div></Dialog>;
}
