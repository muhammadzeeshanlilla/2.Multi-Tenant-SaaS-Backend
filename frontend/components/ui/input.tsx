import { forwardRef } from "react";
import { cn } from "@/lib/cn";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  hint?: string;
  trailing?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, label, error, hint, id, trailing, ...props },
  ref,
) {
  const inputId = id ?? props.name;
  const descriptionId = error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined;
  return (
    <div className="space-y-1.5">
      <label htmlFor={inputId} className="block text-sm font-medium text-slate-700">{label}</label>
      <div className="relative">
        <input
          ref={ref}
          id={inputId}
          aria-invalid={Boolean(error)}
          aria-describedby={descriptionId}
          className={cn("h-11 w-full rounded-lg border bg-white px-3 text-sm text-slate-950 outline-none transition placeholder:text-slate-400 focus:border-indigo-500 focus:ring-3 focus:ring-indigo-100", error ? "border-rose-400" : "border-slate-300", Boolean(trailing) && "pr-11", className)}
          {...props}
        />
        {trailing && <div className="absolute inset-y-0 right-1 flex items-center">{trailing}</div>}
      </div>
      {error ? <p id={descriptionId} className="text-sm text-rose-600">{error}</p> : hint ? <p id={descriptionId} className="text-xs text-slate-500">{hint}</p> : null}
    </div>
  );
});
