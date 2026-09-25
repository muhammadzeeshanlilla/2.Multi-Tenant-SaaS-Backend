"use client";

import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { CheckCircle2, X, XCircle } from "lucide-react";

type ToastTone = "success" | "error";
interface Toast { id: number; message: string; tone: ToastTone }
interface ToastContextValue { notify(message: string, tone?: ToastTone): void }

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);
  const notify = useCallback((message: string, tone: ToastTone = "success") => {
    const id = Date.now();
    setToasts((current) => [...current, { id, message, tone }]);
    window.setTimeout(() => dismiss(id), 4500);
  }, [dismiss]);
  const value = useMemo(() => ({ notify }), [notify]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed bottom-4 right-4 z-[70] flex w-[calc(100%-2rem)] max-w-sm flex-col gap-2" aria-live="polite">
        {toasts.map((toast) => (
          <div key={toast.id} className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 text-sm shadow-lg">
            {toast.tone === "success" ? <CheckCircle2 className="mt-0.5 size-5 text-emerald-600" /> : <XCircle className="mt-0.5 size-5 text-rose-600" />}
            <p className="flex-1 text-slate-700">{toast.message}</p>
            <button onClick={() => dismiss(toast.id)} aria-label="Dismiss notification" className="rounded text-slate-400 hover:text-slate-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"><X className="size-4" /></button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const value = useContext(ToastContext);
  if (!value) throw new Error("useToast must be used within ToastProvider.");
  return value;
}
