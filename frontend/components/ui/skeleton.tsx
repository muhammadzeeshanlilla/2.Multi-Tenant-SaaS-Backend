import { cn } from "@/lib/cn";

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-lg bg-slate-200", className)} aria-hidden="true" />;
}

export function PageLoader() {
  return <div className="space-y-5" role="status" aria-label="Loading page"><Skeleton className="h-8 w-52" /><Skeleton className="h-28 w-full" /><div className="grid gap-4 md:grid-cols-3"><Skeleton className="h-36" /><Skeleton className="h-36" /><Skeleton className="h-36" /></div></div>;
}
