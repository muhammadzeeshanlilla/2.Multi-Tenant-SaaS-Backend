import type { Metadata } from "next";
import { RegistrationForm } from "@/components/auth/registration-form";

export const metadata: Metadata = { title: "Create workspace" };
export default function RegisterPage() {
  return <div><p className="text-sm font-semibold text-indigo-700">Start with TenantFlow</p><h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">Create your company workspace</h2><p className="mt-3 mb-8 text-sm leading-6 text-slate-500">Register your company and its first administrator. You’ll sign in after registration.</p><RegistrationForm /></div>;
}
