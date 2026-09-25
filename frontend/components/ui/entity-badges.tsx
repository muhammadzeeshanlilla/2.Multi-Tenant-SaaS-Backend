import { Badge } from "@/components/ui/badge";
import type { ProjectStatus, TaskPriority, TaskStatus } from "@/types/api";

const projectStyles: Record<ProjectStatus, string> = {
  PLANNING: "bg-slate-100 text-slate-700",
  ACTIVE: "bg-emerald-50 text-emerald-700",
  COMPLETED: "bg-blue-50 text-blue-700",
  CANCELLED: "bg-rose-50 text-rose-700",
};
const taskStyles: Record<TaskStatus, string> = {
  PENDING: "bg-amber-50 text-amber-700",
  IN_PROGRESS: "bg-blue-50 text-blue-700",
  COMPLETED: "bg-emerald-50 text-emerald-700",
};
const priorityStyles: Record<TaskPriority, string> = {
  LOW: "bg-slate-100 text-slate-700",
  MEDIUM: "bg-blue-50 text-blue-700",
  HIGH: "bg-orange-50 text-orange-700",
  URGENT: "bg-rose-50 text-rose-700",
};
const label = (value: string) => value.toLowerCase().split("_").map((part) => part[0].toUpperCase() + part.slice(1)).join(" ");

export function ProjectStatusBadge({ status }: { status: ProjectStatus }) { return <Badge className={projectStyles[status]}>{label(status)}</Badge>; }
export function TaskStatusBadge({ status }: { status: TaskStatus }) { return <Badge className={taskStyles[status]}>{label(status)}</Badge>; }
export function PriorityBadge({ priority }: { priority: TaskPriority }) { return <Badge className={priorityStyles[priority]}>{label(priority)}</Badge>; }
