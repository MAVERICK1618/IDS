import { cn } from "@/lib/utils"

type Severity = "critical" | "high" | "medium" | "low"

interface SeverityBadgeProps {
  severity: Severity
  className?: string
}

const severityConfig: Record<Severity, { label: string; classes: string }> = {
  critical: {
    label: "Critical",
    classes: "bg-destructive/10 text-destructive border-destructive/30",
  },
  high: {
    label: "High",
    classes: "bg-warning/15 text-warning border-warning/30",
  },
  medium: {
    label: "Medium",
    classes: "bg-info/10 text-info border-info/30",
  },
  low: {
    label: "Low",
    classes: "bg-success/10 text-success border-success/30",
  },
}

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  const config = severityConfig[severity]
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium font-mono uppercase tracking-wide",
        config.classes,
        className
      )}
    >
      {config.label}
    </span>
  )
}
