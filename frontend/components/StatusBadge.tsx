import { formatStatus } from "@/lib/utils";

interface StatusBadgeProps {
  status: string;
  size?: "sm" | "md" | "lg";
}

export function StatusBadge({ status, size = "md" }: StatusBadgeProps) {
  const { label, color } = formatStatus(status);

  const sizeClasses = {
    sm: "text-xs px-2 py-1",
    md: "text-sm px-3 py-1",
    lg: "text-base px-4 py-2",
  };

  return (
    <span className={`inline-block rounded-full ${sizeClasses[size]} ${color} font-medium bg-opacity-10`}>
      {label}
    </span>
  );
}
