import type { LucideIcon } from "lucide-react";

export function EmptyState({ icon: Icon, title, description, action }: { icon: LucideIcon; title: string; description: string; action?: React.ReactNode }) {
  return <div className="flex flex-col items-center rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center"><span className="mb-4 rounded-xl bg-slate-100 p-3"><Icon className="size-6 text-slate-500" /></span><h3 className="font-semibold text-slate-900">{title}</h3><p className="mt-1 max-w-sm text-sm text-slate-500">{description}</p>{action && <div className="mt-5">{action}</div>}</div>;
}
