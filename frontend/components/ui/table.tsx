import { cn } from "@/lib/cn";

export function Table({ className, ...props }: React.TableHTMLAttributes<HTMLTableElement>) {
  return <div className="max-w-full overflow-x-auto rounded-xl border border-slate-200"><table className={cn("w-full min-w-[640px] border-collapse text-left text-sm", className)} {...props} /></div>;
}
export function Th(props: React.ThHTMLAttributes<HTMLTableCellElement>) { return <th className="border-b border-slate-200 bg-slate-50 px-4 py-3 font-semibold text-slate-600" {...props} />; }
export function Td(props: React.TdHTMLAttributes<HTMLTableCellElement>) { return <td className="border-b border-slate-100 px-4 py-3 text-slate-700" {...props} />; }
