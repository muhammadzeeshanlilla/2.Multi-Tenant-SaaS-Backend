"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { PageLoader } from "@/components/ui/skeleton";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();
  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.replace("/login");
  }, [isAuthenticated, isLoading, router]);
  if (isLoading || !isAuthenticated) return <main className="min-h-screen bg-slate-50 p-6"><PageLoader /></main>;
  return children;
}

export function GuestRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();
  useEffect(() => {
    if (!isLoading && isAuthenticated) router.replace("/dashboard");
  }, [isAuthenticated, isLoading, router]);
  if (isLoading || isAuthenticated) return <main className="grid min-h-screen place-items-center bg-slate-50"><div className="h-1.5 w-36 overflow-hidden rounded-full bg-slate-200"><div className="h-full w-1/2 animate-pulse rounded-full bg-indigo-600" /></div><span className="sr-only">Checking session</span></main>;
  return children;
}
