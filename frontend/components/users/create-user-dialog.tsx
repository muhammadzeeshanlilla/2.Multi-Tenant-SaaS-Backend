"use client";

import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { useToast } from "@/providers/toast-provider";
import { normalizeApiError } from "@/lib/api-error";
import { userService } from "@/services/user-service";
import type { CreateUserRequest } from "@/types/api";

const schema = z.object({
  username: z.string().trim().min(1, "Username is required.").max(150),
  email: z.email("Enter a valid email address."),
  role: z.enum(["MANAGER", "EMPLOYEE"]),
  password: z.string().min(8, "Use at least 8 characters."),
  confirm_password: z.string().min(1, "Confirm the password."),
  is_active: z.boolean(),
}).refine((data) => data.password === data.confirm_password, { path: ["confirm_password"], message: "Passwords do not match." });

export function CreateUserDialog({ open, onClose, onCreated }: { open: boolean; onClose(): void; onCreated(): void }) {
  const { notify } = useToast();
  const [showPassword, setShowPassword] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const { register, handleSubmit, reset, setError, formState: { errors, isSubmitting } } = useForm<CreateUserRequest>({ resolver: zodResolver(schema), defaultValues: { username: "", email: "", role: "EMPLOYEE", password: "", confirm_password: "", is_active: true } });

  function close() { if (isSubmitting) return; reset(); setFormError(null); onClose(); }
  async function submit(values: CreateUserRequest) {
    setFormError(null);
    try {
      await userService.create(values);
      notify("User created successfully.");
      reset();
      onCreated();
      onClose();
    } catch (error) {
      const normalized = normalizeApiError(error);
      for (const [field, messages] of Object.entries(normalized.fields)) {
        if (field in values) setError(field as keyof CreateUserRequest, { message: messages[0] });
      }
      setFormError(normalized.fields.non_field_errors?.[0] ?? normalized.message);
    }
  }

  return <Dialog open={open} onClose={close} title="Add company user" description="Create a Manager or Employee in your company workspace."><form onSubmit={handleSubmit(submit)} className="space-y-4" noValidate>{formError && <Alert>{formError}</Alert>}<Input label="Username" autoComplete="off" error={errors.username?.message} {...register("username")} /><Input label="Email address" type="email" autoComplete="off" error={errors.email?.message} {...register("email")} /><Select label="Role" error={errors.role?.message} {...register("role")}><option value="EMPLOYEE">Employee</option><option value="MANAGER">Manager</option></Select><Input label="Temporary password" type={showPassword ? "text" : "password"} autoComplete="new-password" hint="Backend password rules are applied on submission." error={errors.password?.message} trailing={<button type="button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"} className="rounded-md p-2 text-slate-400 hover:text-slate-700">{showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}</button>} {...register("password")} /><Input label="Confirm password" type={showPassword ? "text" : "password"} autoComplete="new-password" error={errors.confirm_password?.message} {...register("confirm_password")} /><label className="flex items-start gap-3 rounded-xl border border-slate-200 p-3"><input type="checkbox" className="mt-0.5 size-4 accent-indigo-600" {...register("is_active")} /><span><span className="block text-sm font-medium text-slate-800">Active account</span><span className="block text-xs text-slate-500">Active users may authenticate if their company is active.</span></span></label><div className="flex justify-end gap-3 pt-2"><Button type="button" variant="secondary" onClick={close}>Cancel</Button><Button type="submit" isLoading={isSubmitting}>Create user</Button></div></form></Dialog>;
}
