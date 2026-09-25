"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { normalizeApiError } from "@/lib/api-error";
import { authService } from "@/services/auth-service";

const schema = z.object({
  company_name: z.string().trim().min(1, "Company name is required.").max(255),
  company_email: z.email("Enter a valid company email."),
  phone: z.string().max(20, "Phone must be 20 characters or fewer."),
  address: z.string(),
  username: z.string().trim().min(1, "Administrator name is required.").max(150),
  email: z.email("Enter a valid administrator email."),
  password: z.string().min(8, "Use at least 8 characters."),
  confirm_password: z.string().min(1, "Confirm your password."),
}).refine((data) => data.password === data.confirm_password, { path: ["confirm_password"], message: "Passwords do not match." });
type FormValues = z.infer<typeof schema>;

export function RegistrationForm() {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { company_name: "", company_email: "", phone: "", address: "", username: "", email: "", password: "", confirm_password: "" } });

  async function onSubmit(values: FormValues) {
    setFormError(null);
    try {
      await authService.register(values);
      router.replace("/login?registered=1");
    } catch (error) {
      const normalized = normalizeApiError(error);
      for (const [field, messages] of Object.entries(normalized.fields)) {
        if (field in values) setError(field as keyof FormValues, { message: messages[0] });
      }
      setFormError(normalized.fields.non_field_errors?.[0] ?? normalized.fields.registration?.[0] ?? normalized.message);
    }
  }

  const passwordToggle = <button type="button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide passwords" : "Show passwords"} className="rounded-md p-2 text-slate-400 hover:text-slate-700 focus-visible:outline-2 focus-visible:outline-indigo-600">{showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}</button>;

  return <form className="space-y-7" onSubmit={handleSubmit(onSubmit)} noValidate>
    {formError && <Alert>{formError}</Alert>}
    <fieldset className="space-y-4"><legend className="mb-4 text-sm font-bold uppercase tracking-wide text-slate-500">Company details</legend><div className="grid gap-4 sm:grid-cols-2"><Input label="Company name" placeholder="Acme Ltd" autoComplete="organization" error={errors.company_name?.message} {...register("company_name")} /><Input label="Company email" type="email" placeholder="hello@company.com" error={errors.company_email?.message} {...register("company_email")} /><Input label="Phone (optional)" type="tel" placeholder="+1 555 0100" error={errors.phone?.message} {...register("phone")} /><div className="sm:col-span-2"><Textarea label="Address (optional)" placeholder="Company address" error={errors.address?.message} {...register("address")} /></div></div></fieldset>
    <fieldset className="space-y-4"><legend className="mb-4 text-sm font-bold uppercase tracking-wide text-slate-500">Administrator account</legend><div className="grid gap-4 sm:grid-cols-2"><Input label="Username" autoComplete="username" placeholder="alex" error={errors.username?.message} {...register("username")} /><Input label="Email address" type="email" autoComplete="email" placeholder="alex@company.com" error={errors.email?.message} {...register("email")} /><Input label="Password" type={showPassword ? "text" : "password"} autoComplete="new-password" hint="At least 8 characters; backend security rules also apply." error={errors.password?.message} trailing={passwordToggle} {...register("password")} /><Input label="Confirm password" type={showPassword ? "text" : "password"} autoComplete="new-password" error={errors.confirm_password?.message} {...register("confirm_password")} /></div></fieldset>
    <Button type="submit" isLoading={isSubmitting} className="w-full">{isSubmitting ? "Creating workspace…" : "Create company workspace"}</Button>
    <p className="text-center text-sm text-slate-500">Already have an account? <Link href="/login" className="font-semibold text-indigo-700 hover:underline">Sign in</Link></p>
  </form>;
}
