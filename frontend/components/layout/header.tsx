"use client";

import { ChevronDown, LogOut, Menu } from "lucide-react";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Dropdown, DropdownItem } from "@/components/ui/dropdown";
import { useAuth } from "@/hooks/use-auth";

export function Header({ onMenuOpen }: { onMenuOpen(): void }) {
  const { user, company, role, logout } = useAuth();
  return <header className="sticky top-0 z-30 flex h-20 items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur sm:px-6 lg:px-8"><div className="flex min-w-0 items-center gap-3"><button onClick={onMenuOpen} aria-label="Open navigation" className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden"><Menu className="size-5" /></button><div className="min-w-0"><p className="truncate text-sm font-semibold text-slate-900">{company?.name}</p><p className="text-xs text-slate-500">Company workspace</p></div></div><Dropdown trigger={<span className="flex items-center gap-2 rounded-xl p-1.5 hover:bg-slate-50"><Avatar name={user?.username ?? "User"} size="sm" /><span className="hidden text-left sm:block"><span className="block max-w-36 truncate text-sm font-semibold text-slate-800">{user?.username}</span><Badge className="mt-0.5 py-0 text-[10px]">{role}</Badge></span><ChevronDown className="size-4 text-slate-400" /></span>}><div className="border-b border-slate-100 px-3 py-2"><p className="font-semibold text-slate-900">{user?.username}</p><p className="truncate text-xs text-slate-500">{user?.email}</p></div><DropdownItem onClick={() => void logout()}><LogOut className="size-4" />Log out</DropdownItem></Dropdown></header>;
}
