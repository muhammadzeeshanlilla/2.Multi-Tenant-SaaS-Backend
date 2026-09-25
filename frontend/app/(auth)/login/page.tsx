import { Suspense } from "react";
import type { Metadata } from "next";
import { LoginForm } from "@/components/auth/login-form";
import { Skeleton } from "@/components/ui/skeleton";

export const metadata: Metadata = { title: "Sign in" };
export default function LoginPage() {
  return <div className="mx-auto max-w-md"><p className="text-sm font-semibold text-indigo-700">Welcome back</p><h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">Sign in to your workspace</h2><p className="mt-3 mb-8 text-sm leading-6 text-slate-500">Use your company account to continue to TenantFlow.</p><Suspense fallback={<div className="space-y-5"><Skeleton className="h-16" /><Skeleton className="h-16" /><Skeleton className="h-11" /></div>}><LoginForm /></Suspense></div>;
}
