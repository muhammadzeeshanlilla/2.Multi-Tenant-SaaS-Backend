export type UserRole = "ADMIN" | "MANAGER" | "EMPLOYEE";

export interface CompanySummary {
  id: number;
  name: string;
  slug: string;
  email?: string;
}

export interface UserSummary {
  id: number;
  username: string;
  email: string;
  role: UserRole;
}

export interface User extends UserSummary {
  company: CompanySummary | null;
  is_active: boolean;
  is_deleted?: boolean;
  created_at: string;
  updated_at?: string;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  confirm_password: string;
  role: Exclude<UserRole, "ADMIN">;
  is_active: boolean;
}

export interface UpdateUserRequest {
  username?: string;
  email?: string;
  role?: Exclude<UserRole, "ADMIN">;
  password?: string;
  is_active?: boolean;
}

export interface Project {
  id: number;
  name: string;
  description: string | null;
  status: "PLANNING" | "ACTIVE" | "COMPLETED" | "CANCELLED";
  start_date: string | null;
  end_date: string | null;
  company: CompanySummary;
  created_by: UserSummary | null;
  members: UserSummary[];
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export type ProjectStatus = Project["status"];

export interface ProjectMutationRequest {
  name: string;
  description?: string;
  status: ProjectStatus;
  start_date?: string | null;
  end_date?: string | null;
}

export interface Task {
  id: number;
  title: string;
  description: string | null;
  company: CompanySummary;
  project: Pick<Project, "id" | "name" | "status">;
  assigned_to: UserSummary | null;
  status: "PENDING" | "IN_PROGRESS" | "COMPLETED";
  priority: "LOW" | "MEDIUM" | "HIGH" | "URGENT";
  due_date: string | null;
  created_by: UserSummary | null;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export type TaskStatus = Task["status"];
export type TaskPriority = Task["priority"];

export interface TaskMutationRequest {
  project_id: number;
  title: string;
  description?: string;
  assigned_to_id?: number | null;
  status: TaskStatus;
  priority: TaskPriority;
  due_date?: string | null;
}

export interface AuditLog {
  id: number;
  company: CompanySummary;
  user: UserSummary | null;
  action: string;
  object_type: string | null;
  object_id: number | null;
  description: string | null;
  ip_address: string | null;
  created_at: string;
}

export interface ApiEnvelope<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface PaginatedResponse<T> extends ApiEnvelope<T[]> {
  count: number;
  next: string | null;
  previous: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export type LoginResponse = ApiEnvelope<{
  user: User;
  tokens: TokenPair;
}>;

export interface RefreshResponse {
  access: string;
  refresh?: string;
}

export interface RegistrationRequest {
  company_name: string;
  company_email: string;
  phone?: string;
  address?: string;
  username: string;
  email: string;
  password: string;
  confirm_password: string;
}

export type RegistrationResponse = ApiEnvelope<{
  company: CompanySummary & { phone?: string; address?: string };
  admin: UserSummary;
}>;

export type FieldErrors = Record<string, string[]>;

export interface NormalizedApiError {
  message: string;
  status?: number;
  fields: FieldErrors;
}
