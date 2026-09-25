"use client";

import { useEffect, useState } from "react";
import { Alert } from "@/components/ui/alert";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { normalizeApiError } from "@/lib/api-error";
import { formatDate } from "@/lib/format";
import { userService } from "@/services/user-service";
import type { User } from "@/types/api";

export function UserDetailsDialog({ userId, onClose }: { userId: number | null; onClose(): void }) {
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    if (!userId) return;
    userService.get(userId).then((result) => { if (active) setUser(result); }).catch((requestError) => { if (active) setError(normalizeApiError(requestError).message); });
    return () => { active = false; };
  }, [userId]);
  return <Dialog open={Boolean(userId)} onClose={onClose} title="User details" description="Tenant-scoped account information from the user detail endpoint.">{error ? <Alert>{error}</Alert> : !user ? <div className="space-y-4"><Skeleton className="h-16" /><Skeleton className="h-28" /></div> : <div><div className="flex items-center gap-3"><Avatar name={user.username} /><div><p className="font-semibold text-slate-950">{user.username}</p><p className="text-sm text-slate-500">{user.email}</p></div></div><dl className="mt-6 grid gap-4 rounded-xl bg-slate-50 p-4 sm:grid-cols-2"><div><dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Role</dt><dd className="mt-1"><Badge>{user.role}</Badge></dd></div><div><dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Status</dt><dd className={`mt-1 text-sm font-semibold ${user.is_active ? "text-emerald-700" : "text-slate-500"}`}>{user.is_active ? "Active" : "Inactive"}</dd></div><div><dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Company</dt><dd className="mt-1 text-sm text-slate-700">{user.company?.name ?? "—"}</dd></div><div><dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Created</dt><dd className="mt-1 text-sm text-slate-700">{formatDate(user.created_at)}</dd></div></dl></div>}</Dialog>;
}
