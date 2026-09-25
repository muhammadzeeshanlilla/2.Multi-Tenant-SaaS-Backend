export function Avatar({ name, size = "md" }: { name: string; size?: "sm" | "md" }) {
  const initials = name.split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase();
  return <span aria-hidden="true" className={`${size === "sm" ? "size-8 text-xs" : "size-10 text-sm"} inline-flex shrink-0 items-center justify-center rounded-full bg-indigo-100 font-bold text-indigo-700`}>{initials}</span>;
}
