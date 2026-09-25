import Link from "next/link";
import { Layers3 } from "lucide-react";

export function Brand({ compact = false, inverse = false }: { compact?: boolean; inverse?: boolean }) {
  return <Link href="/dashboard" className="inline-flex items-center gap-3 rounded-lg focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-indigo-500"><span className="grid size-10 place-items-center rounded-xl bg-indigo-600 text-white shadow-sm"><Layers3 className="size-5" /></span>{!compact && <span><span className={`block text-base font-bold tracking-tight ${inverse ? "text-white" : "text-slate-950"}`}>TenantFlow</span><span className={`block text-[11px] font-medium uppercase tracking-[0.18em] ${inverse ? "text-slate-400" : "text-slate-400"}`}>Workspace</span></span>}</Link>;
}
