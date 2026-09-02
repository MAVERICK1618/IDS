import { cn } from "@/lib/utils"

type Status = "active" | "inactive" | "warning" | "error"

interface StatusIndicatorProps {
  status: Status
  label: string
  className?: string
}

const statusConfig: Record<Status, { dot: string; text: string }> = {
  active: { dot: "bg-success", text: "text-success" },
  inactive: { dot: "bg-muted-foreground", text: "text-muted-foreground" },
  warning: { dot: "bg-warning", text: "text-warning" },
  error: { dot: "bg-destructive", text: "text-destructive" },
}

export function StatusIndicator({ status, label, className }: StatusIndicatorProps) {
  const config = statusConfig[status]
  return (
    <div className={cn("flex items-center gap-2 text-sm font-medium transition-colors duration-300", config.text, className)}>
      <span className="relative flex h-2 w-2">
        {status === "active" && (
          <span className={cn("absolute inline-flex h-full w-full animate-ping rounded-full opacity-75", config.dot)} />
        )}
        <span className={cn("relative inline-flex h-2 w-2 rounded-full", config.dot)} />
      </span>
      {label}
    </div>
  )
}
