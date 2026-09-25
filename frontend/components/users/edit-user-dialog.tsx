"use client";

import { useEffect, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { ConfirmationDialog, Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { normalizeApiError } from "@/lib/api-error";
import { useToast } from "@/providers/toast-provider";
import { userService } from "@/services/user-service";
import type { UpdateUserRequest, User } from "@/types/api";

const schema = z.object({ username: z.string().trim().min(1, "Username is required.").max(150), email: z.email("Enter a valid email address."), role: z.enum(["MANAGER", "EMPLOYEE"]), is_active: z.boolean() });
type Values = z.infer<typeof schema>;

export function EditUserDialog({ user, onClose, onUpdated }: { user: User | null; onClose(): void; onUpdated(): void }) {
  const { notify } = useToast();
  const [formError, setFormError] = useState<string | null>(null);
  const [pending, setPending] = useState<Values | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const { register, handleSubmit, reset, setError, formState: { errors } } = useForm<Values>({ resolver: zodResolver(schema) });

  useEffect(() => { if (user) reset({ username: user.username, email: user.email, role: user.role === "MANAGER" ? "MANAGER" : "EMPLOYEE", is_active: user.is_active }); }, [reset, user]);
  function requestSave(values: Values) {
    const accessChanged = values.role !== user?.role || values.is_active !== user?.is_active;
    if (accessChanged) setPending(values); else void save(values);
  }
  async function save(values: Values) {
    if (!user) return;
    setIsSaving(true); setFormError(null);
    try {
      await userService.update(user.id, values satisfies UpdateUserRequest);
      notify("User updated successfully.");
      setPending(null); onUpdated(); onClose();
    } catch (error) {
      const normalized = normalizeApiError(error);
      for (const [field, messages] of Object.entries(normalized.fields)) if (field in values) setError(field as keyof Values, { message: messages[0] });
      setFormError(normalized.message); setPending(null);
    } finally { setIsSaving(false); }
  }

  return <><Dialog open={Boolean(user)} onClose={onClose} title="Edit user" description="Update profile and access fields supported by the backend."><form onSubmit={handleSubmit(requestSave)} className="space-y-4" noValidate>{formError && <Alert>{formError}</Alert>}<Input label="Username" error={errors.username?.message} {...register("username")} /><Input label="Email address" type="email" error={errors.email?.message} {...register("email")} /><Select label="Role" error={errors.role?.message} {...register("role")}><option value="EMPLOYEE">Employee</option><option value="MANAGER">Manager</option></Select><label className="flex items-start gap-3 rounded-xl border border-slate-200 p-3"><input type="checkbox" className="mt-0.5 size-4 accent-indigo-600" {...register("is_active")} /><span><span className="block text-sm font-medium text-slate-800">Active account</span><span className="block text-xs text-slate-500">Deactivation prevents normal authentication and protected API use.</span></span></label><p className="text-xs leading-5 text-slate-500">Password changes are intentionally not mixed into this profile form.</p><div className="flex justify-end gap-3 pt-2"><Button type="button" variant="secondary" onClick={onClose}>Cancel</Button><Button type="submit" isLoading={isSaving}>Save changes</Button></div></form></Dialog><ConfirmationDialog open={Boolean(pending)} title="Confirm access change" description="You are changing this user’s role or active status. This can immediately affect their access to the workspace." confirmLabel="Confirm changes" isLoading={isSaving} onClose={() => setPending(null)} onConfirm={() => pending && void save(pending)} /></>;
}
