"use client";

import { useState } from "react";
import { Header } from "@/components/layout/header";
import { Sidebar } from "@/components/layout/sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false);
  return <div className="min-h-screen bg-slate-50"><Sidebar open={menuOpen} onClose={() => setMenuOpen(false)} /><div className="lg:pl-72"><Header onMenuOpen={() => setMenuOpen(true)} /><main className="mx-auto w-full max-w-[1600px] p-4 sm:p-6 lg:p-8">{children}</main></div></div>;
}
