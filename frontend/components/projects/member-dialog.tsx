"use client";

import { useEffect, useState } from "react";
import { Alert } from "@/components/ui/alert";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { normalizeApiError } from "@/lib/api-error";
import { useToast } from "@/providers/toast-provider";
import { projectService } from "@/services/project-service";
import { userService } from "@/services/user-service";
import type { Project, User } from "@/types/api";

export function MemberDialog({ project, onClose, onSaved }: { project: Project; onClose(): void; onSaved(): void }) {
  const { notify } = useToast();
  const [users, setUsers] = useState<User[]>([]);
  const [selected, setSelected] = useState(() => new Set(project.members.map((member) => member.id)));
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    userService.listAllActive().then((result) => { if (active) setUsers(result); }).catch((requestError) => { if (active) setError(normalizeApiError(requestError).message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);
  function toggle(id: number) { setSelected((current) => { const next = new Set(current); if (next.has(id)) next.delete(id); else next.add(id); return next; }); }
  async function save() {
    setSaving(true); setError(null);
    try { await projectService.assignUsers(project.id, [...selected]); notify("Project membership updated."); onSaved(); onClose(); }
    catch (requestError) { setError(normalizeApiError(requestError).message); }
    finally { setSaving(false); }
  }
  return <Dialog open title={`Manage members · ${project.name}`} description="Membership is replaced atomically with the selected active company users." onClose={onClose}>{error && <Alert className="mb-4">{error}</Alert>}{loading ? <div className="space-y-2"><Skeleton className="h-14" /><Skeleton className="h-14" /><Skeleton className="h-14" /></div> : <div className="max-h-80 space-y-2 overflow-y-auto pr-1">{users.map((user) => <label key={user.id} className="flex cursor-pointer items-center gap-3 rounded-xl border border-slate-200 p-3 hover:bg-slate-50"><input type="checkbox" checked={selected.has(user.id)} onChange={() => toggle(user.id)} className="size-4 accent-indigo-600" /><Avatar name={user.username} size="sm" /><span className="min-w-0 flex-1"><span className="block truncate text-sm font-semibold text-slate-800">{user.username}</span><span className="block truncate text-xs text-slate-500">{user.email} · {user.role}</span></span></label>)}</div>}<p className="mt-3 text-xs text-slate-500">Only active, non-deleted users from this company are shown. Clear every selection to leave the project without members.</p><div className="mt-5 flex justify-end gap-3"><Button variant="secondary" onClick={onClose}>Cancel</Button><Button isLoading={saving} onClick={() => void save()}>Save members</Button></div></Dialog>;
}
