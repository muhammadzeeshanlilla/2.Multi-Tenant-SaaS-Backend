import { forwardRef } from "react";
import { cn } from "@/lib/cn";

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(function Textarea(
  { label, error, id, className, ...props }, ref,
) {
  const fieldId = id ?? props.name;
  return <div className="space-y-1.5">
    <label htmlFor={fieldId} className="block text-sm font-medium text-slate-700">{label}</label>
    <textarea ref={ref} id={fieldId} aria-invalid={Boolean(error)} className={cn("min-h-24 w-full resize-y rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100", error && "border-rose-400", className)} {...props} />
    {error && <p className="text-sm text-rose-600">{error}</p>}
  </div>;
});
