"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, ScrollText } from "lucide-react";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Pagination } from "@/components/ui/pagination";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, Td, Th } from "@/components/ui/table";
import { useAuth } from "@/hooks/use-auth";
import { normalizeApiError } from "@/lib/api-error";
import { formatDateTime, humanizeAction } from "@/lib/format";
import { auditService } from "@/services/audit-service";
import type { AuditLog, PaginatedResponse } from "@/types/api";

const PAGE_SIZE = 10;
const ACTIONS = [
  "USER_LOGIN", "USER_LOGOUT", "USER_CREATED", "USER_UPDATED", "USER_DELETED", "USER_RESTORED",
  "PROJECT_CREATED", "PROJECT_UPDATED", "PROJECT_DELETED", "PROJECT_RESTORED", "PROJECT_USERS_ASSIGNED",
  "TASK_CREATED", "TASK_UPDATED", "TASK_DELETED", "TASK_RESTORED", "TASK_STATUS_CHANGED",
] as const;

export default function AuditLogsPage() {
  const { role } = useAuth();
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [action, setAction] = useState("");
  const [result, setResult] = useState<PaginatedResponse<AuditLog> | null>(null);
  const [selected, setSelected] = useState<AuditLog | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (role && role !== "ADMIN") router.replace("/dashboard");
  }, [role, router]);

  useEffect(() => {
    let active = true;
    if (role !== "ADMIN") return;
    auditService.list({ page, page_size: PAGE_SIZE, action: action || undefined })
      .then((response) => { if (active) { setResult(response); setError(null); } })
      .catch((requestError) => { if (active) setError(normalizeApiError(requestError).message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [action, page, role]);

  if (role !== "ADMIN") return null;
  const logs = result?.data ?? [];

  return <div className="space-y-6">
    <header>
      <p className="text-sm font-semibold text-indigo-700">Administration</p>
      <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">Audit logs</h1>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">Review recorded activity for your company. This read-only view is available to Administrators only.</p>
    </header>
    <div className="max-w-sm">
      <Select label="Action type" value={action} onChange={(event) => { setLoading(true); setAction(event.target.value); setPage(1); }}>
        <option value="">All actions</option>
        {ACTIONS.map((value) => <option key={value} value={value}>{humanizeAction(value)}</option>)}
      </Select>
    </div>
    {error && <Alert>{error}</Alert>}
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-100 px-4 py-4 sm:px-5"><div><h2 className="font-semibold text-slate-950">Company activity</h2><p className="text-sm text-slate-500" aria-live="polite">{result ? `${result.count} total ${result.count === 1 ? "record" : "records"}` : "Loading audit records…"}</p></div><ScrollText className="size-5 text-slate-400" aria-hidden="true" /></div>
      {loading ? <div className="space-y-3 p-5" role="status" aria-label="Loading audit logs">{Array.from({ length: 6 }).map((_, index) => <Skeleton key={index} className="h-16" />)}</div>
        : logs.length === 0 ? <div className="p-5"><EmptyState icon={ScrollText} title={action ? "No matching audit entries" : "No audit entries yet"} description={action ? "No recorded activity matches this action type." : "Recorded company activity will appear here."} /></div>
        : <>
          <div className="hidden p-5 lg:block"><Table><thead><tr><Th>Action</Th><Th>Actor</Th><Th>Related object</Th><Th>IP address</Th><Th>Timestamp</Th><Th><span className="sr-only">Details</span></Th></tr></thead><tbody>{logs.map((log) => <tr key={log.id}><Td><Badge>{humanizeAction(log.action)}</Badge></Td><Td><p className="font-medium text-slate-900">{log.user?.username ?? "System"}</p>{log.user?.email && <p className="text-xs text-slate-500">{log.user.email}</p>}</Td><Td>{formatObject(log)}</Td><Td>{log.ip_address ?? "Not recorded"}</Td><Td className="whitespace-nowrap">{formatDateTime(log.created_at)}</Td><Td><Button variant="ghost" className="px-2" aria-label={`View details for audit record ${log.id}`} onClick={() => setSelected(log)}><Eye className="size-4" aria-hidden="true" />Details</Button></Td></tr>)}</tbody></Table></div>
          <div className="divide-y divide-slate-100 lg:hidden">{logs.map((log) => <article key={log.id} className="p-4 sm:p-5"><div className="flex items-start justify-between gap-3"><div className="min-w-0"><Badge>{humanizeAction(log.action)}</Badge><h3 className="mt-2 truncate font-semibold text-slate-900">{log.description || formatObject(log)}</h3><p className="mt-1 text-sm text-slate-500">{log.user?.username ?? "System"} · {formatDateTime(log.created_at)}</p></div><Button variant="ghost" className="shrink-0 px-2" aria-label={`View details for audit record ${log.id}`} onClick={() => setSelected(log)}><Eye className="size-4" aria-hidden="true" /><span className="hidden sm:inline">Details</span></Button></div></article>)}</div>
          <div className="border-t border-slate-100 px-4 sm:px-5"><Pagination count={result?.count ?? 0} page={page} pageSize={PAGE_SIZE} hasNext={Boolean(result?.next)} hasPrevious={Boolean(result?.previous)} onPageChange={(nextPage) => { setLoading(true); setPage(nextPage); }} /></div>
        </>}
    </Card>
    <AuditDetailsDialog log={selected} onClose={() => setSelected(null)} />
  </div>;
}

function formatObject(log: AuditLog) {
  if (!log.object_type && log.object_id == null) return "Not recorded";
  if (log.object_type && log.object_id != null) return `${log.object_type} #${log.object_id}`;
  return log.object_type ?? `Object #${log.object_id}`;
}

function AuditDetailsDialog({ log, onClose }: { log: AuditLog | null; onClose(): void }) {
  return <Dialog open={Boolean(log)} title="Audit record details" description="Recorded metadata for this tenant activity." onClose={onClose}>{log && <dl className="grid gap-4 text-sm sm:grid-cols-2"><Detail label="Record ID" value={String(log.id)} /><Detail label="Action" value={humanizeAction(log.action)} /><Detail label="Actor" value={log.user ? `${log.user.username} (${log.user.email})` : "System"} /><Detail label="Actor role" value={log.user?.role ?? "Not applicable"} /><Detail label="Related object" value={formatObject(log)} /><Detail label="IP address" value={log.ip_address ?? "Not recorded"} /><Detail label="Timestamp" value={formatDateTime(log.created_at)} /><Detail label="Company" value={log.company.name} /><div className="sm:col-span-2"><Detail label="Description" value={log.description ?? "No description recorded."} /></div></dl>}</Dialog>;
}

function Detail({ label, value }: { label: string; value: string }) {
  return <div><dt className="font-medium text-slate-500">{label}</dt><dd className="mt-1 break-words text-slate-900">{value}</dd></div>;
}
