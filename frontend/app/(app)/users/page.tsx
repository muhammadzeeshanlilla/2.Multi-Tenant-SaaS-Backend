"use client";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Ellipsis, Plus, UserRoundX, Users } from "lucide-react";
import { Alert } from "@/components/ui/alert";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ConfirmationDialog } from "@/components/ui/dialog";
import { Dropdown, DropdownItem } from "@/components/ui/dropdown";
import { EmptyState } from "@/components/ui/empty-state";
import { Pagination } from "@/components/ui/pagination";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, Td, Th } from "@/components/ui/table";
import { CreateUserDialog } from "@/components/users/create-user-dialog";
import { EditUserDialog } from "@/components/users/edit-user-dialog";
import { UserDetailsDialog } from "@/components/users/user-details-dialog";
import { useAuth } from "@/hooks/use-auth";
import { normalizeApiError } from "@/lib/api-error";
import { formatDate } from "@/lib/format";
import { useToast } from "@/providers/toast-provider";
import { userService } from "@/services/user-service";
import type { PaginatedResponse, User } from "@/types/api";

const PAGE_SIZE = 10;

export default function UsersPage() {
  const { role } = useAuth();
  const { notify } = useToast();
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [result, setResult] = useState<PaginatedResponse<User> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [viewingId, setViewingId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState<User | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => { if (role && role !== "ADMIN") router.replace("/dashboard"); }, [role, router]);
  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try { setResult(await userService.list(page, PAGE_SIZE)); }
    catch (requestError) { setError(normalizeApiError(requestError).message); }
    finally { setLoading(false); }
  }, [page]);
  useEffect(() => {
    let active = true;
    if (role !== "ADMIN") return;
    userService.list(page, PAGE_SIZE).then((response) => {
      if (active) { setResult(response); setError(null); }
    }).catch((requestError) => {
      if (active) setError(normalizeApiError(requestError).message);
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, [page, role]);

  async function removeUser() {
    if (!deleting) return;
    setIsDeleting(true);
    try {
      await userService.softDelete(deleting.id);
      notify("User deactivated and removed from the active user list.");
      const moveBack = result?.data.length === 1 && page > 1;
      setDeleting(null);
      if (moveBack) setPage((current) => current - 1); else await load();
    } catch (requestError) { notify(normalizeApiError(requestError).message, "error"); }
    finally { setIsDeleting(false); }
  }

  if (role !== "ADMIN") return null;
  const users = result?.data ?? [];
  return <div className="space-y-6"><header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-sm font-semibold text-indigo-700">Administration</p><h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">Users</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">Manage Manager and Employee accounts in your company. The backend does not currently provide server-side user search or filters.</p></div><Button onClick={() => setCreateOpen(true)}><Plus className="size-4" />Add user</Button></header>{error && <Alert>{error}</Alert>}<Card className="overflow-hidden"><div className="flex items-center justify-between border-b border-slate-100 px-5 py-4"><div><h2 className="font-semibold text-slate-950">Company accounts</h2><p className="text-sm text-slate-500">{result ? `${result.count} total users` : "Loading users…"}</p></div><Users className="size-5 text-slate-400" /></div>{loading ? <div className="space-y-3 p-5">{Array.from({ length: 5 }).map((_, index) => <Skeleton key={index} className="h-14" />)}</div> : users.length === 0 ? <div className="p-5"><EmptyState icon={Users} title="No users found" description="Create the first Manager or Employee account for this company." action={<Button onClick={() => setCreateOpen(true)}><Plus className="size-4" />Add user</Button>} /></div> : <><div className="hidden p-5 md:block"><Table><thead><tr><Th>User</Th><Th>Email</Th><Th>Role</Th><Th>Status</Th><Th>Created</Th><Th><span className="sr-only">Actions</span></Th></tr></thead><tbody>{users.map((user) => <tr key={user.id}><Td><div className="flex items-center gap-3"><Avatar name={user.username} size="sm" /><span className="font-semibold text-slate-900">{user.username}</span></div></Td><Td>{user.email}</Td><Td><Badge className={user.role === "ADMIN" ? "bg-violet-50 text-violet-700" : ""}>{user.role}</Badge></Td><Td><span className={`inline-flex items-center gap-1.5 font-medium ${user.is_active ? "text-emerald-700" : "text-slate-500"}`}><span className={`size-2 rounded-full ${user.is_active ? "bg-emerald-500" : "bg-slate-300"}`} />{user.is_active ? "Active" : "Inactive"}</span></Td><Td>{formatDate(user.created_at)}</Td><Td><UserActions user={user} onView={() => setViewingId(user.id)} onEdit={() => setEditing(user)} onDelete={() => setDeleting(user)} /></Td></tr>)}</tbody></Table></div><div className="divide-y divide-slate-100 md:hidden">{users.map((user) => <article key={user.id} className="p-4"><div className="flex items-start justify-between gap-3"><div className="flex min-w-0 items-center gap-3"><Avatar name={user.username} /><div className="min-w-0"><h3 className="truncate font-semibold text-slate-900">{user.username}</h3><p className="truncate text-sm text-slate-500">{user.email}</p></div></div><UserActions user={user} onView={() => setViewingId(user.id)} onEdit={() => setEditing(user)} onDelete={() => setDeleting(user)} /></div><div className="mt-4 flex flex-wrap items-center gap-2"><Badge>{user.role}</Badge><span className={`text-xs font-semibold ${user.is_active ? "text-emerald-700" : "text-slate-500"}`}>{user.is_active ? "Active" : "Inactive"}</span><span className="text-xs text-slate-400">Joined {formatDate(user.created_at)}</span></div></article>)}</div><div className="border-t border-slate-100 px-5"><Pagination count={result?.count ?? 0} page={page} pageSize={PAGE_SIZE} hasNext={Boolean(result?.next)} hasPrevious={Boolean(result?.previous)} onPageChange={(nextPage) => { setLoading(true); setPage(nextPage); }} /></div></>}</Card><CreateUserDialog open={createOpen} onClose={() => setCreateOpen(false)} onCreated={() => { setPage(1); void load(); }} /><EditUserDialog user={editing} onClose={() => setEditing(null)} onUpdated={() => void load()} /><UserDetailsDialog key={viewingId ?? "closed"} userId={viewingId} onClose={() => setViewingId(null)} /><ConfirmationDialog open={Boolean(deleting)} title="Soft-delete this user?" description={`${deleting?.username ?? "This user"} will be marked deleted and inactive, and will disappear from the active user list. This is not presented as permanent deletion.`} confirmLabel="Soft-delete user" isLoading={isDeleting} onClose={() => setDeleting(null)} onConfirm={() => void removeUser()} /></div>;
}

function UserActions({ user, onView, onEdit, onDelete }: { user: User; onView(): void; onEdit(): void; onDelete(): void }) {
  return <Dropdown trigger={<span className="grid size-9 place-items-center rounded-lg text-slate-500 hover:bg-slate-100"><Ellipsis className="size-5" /><span className="sr-only">Actions for {user.username}</span></span>}><DropdownItem onClick={onView}>View details</DropdownItem>{user.role !== "ADMIN" && <><DropdownItem onClick={onEdit}>Edit user</DropdownItem><DropdownItem onClick={onDelete}><UserRoundX className="size-4 text-rose-600" />Soft-delete user</DropdownItem></>}</Dropdown>;
}
