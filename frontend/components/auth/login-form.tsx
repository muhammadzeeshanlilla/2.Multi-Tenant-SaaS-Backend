"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/use-auth";
import type { NormalizedApiError } from "@/types/api";

const schema = z.object({
  email: z.email("Enter a valid email address."),
  password: z.string().min(1, "Password is required."),
});
type FormValues = z.infer<typeof schema>;

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { email: "", password: "" } });

  async function onSubmit(values: FormValues) {
    setFormError(null);
    try {
      await login(values);
      router.replace("/dashboard");
    } catch (error) {
      const normalized = error as NormalizedApiError;
      Object.entries(normalized.fields).forEach(([field, messages]) => {
        if (field === "email" || field === "password") setError(field, { message: messages[0] });
      });
      setFormError(normalized.fields.non_field_errors?.[0] ?? normalized.fields.account?.[0] ?? normalized.message);
    }
  }

  return <form className="space-y-5" onSubmit={handleSubmit(onSubmit)} noValidate>
    {searchParams.get("registered") === "1" && <Alert tone="success">Company created successfully. Sign in with your administrator account.</Alert>}
    {searchParams.get("session") === "expired" && <Alert>Your session expired. Please sign in again.</Alert>}
    {formError && <Alert>{formError}</Alert>}
    <Input label="Email address" type="email" autoComplete="email" placeholder="you@company.com" error={errors.email?.message} {...register("email")} />
    <Input label="Password" type={showPassword ? "text" : "password"} autoComplete="current-password" placeholder="Enter your password" error={errors.password?.message} trailing={<button type="button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"} className="rounded-md p-2 text-slate-400 hover:text-slate-700 focus-visible:outline-2 focus-visible:outline-indigo-600">{showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}</button>} {...register("password")} />
    <Button type="submit" isLoading={isSubmitting} className="w-full">{isSubmitting ? "Signing in…" : "Sign in"}</Button>
    <p className="text-center text-sm text-slate-500">Setting up a new company? <Link href="/register" className="font-semibold text-indigo-700 hover:text-indigo-800 hover:underline">Create a workspace</Link></p>
  </form>;
}
