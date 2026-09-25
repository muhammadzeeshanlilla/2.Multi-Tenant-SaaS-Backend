import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Pagination({ count, page, pageSize, hasNext, hasPrevious, onPageChange }: { count: number; page: number; pageSize: number; hasNext: boolean; hasPrevious: boolean; onPageChange(page: number): void }) {
  const start = count ? (page - 1) * pageSize + 1 : 0;
  const end = Math.min(page * pageSize, count);
  return <nav className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between" aria-label="Pagination"><p className="text-sm text-slate-500">Showing {start}–{end} of {count}</p><div className="flex gap-2"><Button variant="secondary" disabled={!hasPrevious} onClick={() => onPageChange(page - 1)}><ChevronLeft className="size-4" />Previous</Button><Button variant="secondary" disabled={!hasNext} onClick={() => onPageChange(page + 1)}>Next<ChevronRight className="size-4" /></Button></div></nav>;
}
