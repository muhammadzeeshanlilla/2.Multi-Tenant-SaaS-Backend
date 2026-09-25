import { Search } from "lucide-react";

export function SearchFilter({ value, onChange, placeholder = "Search…" }: { value: string; onChange(value: string): void; placeholder?: string }) {
  return <label className="relative block"><span className="sr-only">Search</span><Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" /><input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} className="h-10 w-full rounded-lg border border-slate-300 bg-white pl-9 pr-3 text-sm outline-none focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100 sm:w-72" /></label>;
}
