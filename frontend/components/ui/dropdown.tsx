"use client";

import { useEffect, useRef, useState } from "react";

export function Dropdown({ trigger, children, align = "right" }: { trigger: React.ReactNode; children: React.ReactNode; align?: "left" | "right" }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    function close(event: MouseEvent) { if (!ref.current?.contains(event.target as Node)) setOpen(false); }
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);
  return <div className="relative" ref={ref}><button type="button" aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen((value) => !value)} className="rounded-lg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">{trigger}</button>{open && <div role="menu" className={`absolute top-full z-40 mt-2 min-w-48 rounded-xl border border-slate-200 bg-white p-1.5 shadow-lg ${align === "right" ? "right-0" : "left-0"}`} onClick={() => setOpen(false)}>{children}</div>}</div>;
}

export function DropdownItem({ children, onClick }: { children: React.ReactNode; onClick?(): void }) {
  return <button role="menuitem" type="button" onClick={onClick} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-100 focus:bg-slate-100 focus:outline-none">{children}</button>;
}
