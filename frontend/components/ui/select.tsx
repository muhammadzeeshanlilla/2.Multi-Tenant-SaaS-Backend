import { forwardRef } from "react";
import { cn } from "@/lib/cn";

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  error?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { label, error, id, className, children, ...props }, ref,
) {
  const fieldId = id ?? props.name;
  return <div className="space-y-1.5">
    <label htmlFor={fieldId} className="block text-sm font-medium text-slate-700">{label}</label>
    <select ref={ref} id={fieldId} aria-invalid={Boolean(error)} className={cn("h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-sm outline-none focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100", error && "border-rose-400", className)} {...props}>{children}</select>
    {error && <p className="text-sm text-rose-600">{error}</p>}
  </div>;
});
