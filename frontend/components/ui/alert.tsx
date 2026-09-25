import { AlertCircle, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/cn";

export function Alert({ children, tone = "error", className }: { children: React.ReactNode; tone?: "error" | "success"; className?: string }) {
  const success = tone === "success";
  const Icon = success ? CheckCircle2 : AlertCircle;
  return <div role={success ? "status" : "alert"} className={cn("flex items-start gap-3 rounded-xl border p-3.5 text-sm", success ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-rose-200 bg-rose-50 text-rose-800", className)}><Icon className="mt-0.5 size-4 shrink-0" /><div>{children}</div></div>;
}
