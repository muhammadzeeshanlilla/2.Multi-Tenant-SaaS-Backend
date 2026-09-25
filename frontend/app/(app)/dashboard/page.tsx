"use client";

import { AdminDashboard } from "@/components/dashboard/admin-dashboard";
import { RoleDashboard } from "@/components/dashboard/role-dashboard";
import { useAuth } from "@/hooks/use-auth";

export default function DashboardPage() {
  const { user } = useAuth();
  if (!user) return null;
  return user.role === "ADMIN" ? <AdminDashboard /> : <RoleDashboard user={user} />;
}
