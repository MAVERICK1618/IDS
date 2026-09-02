import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { type LucideIcon } from "lucide-react"

interface MetricCardProps {
  label: string
  value: string | number
  icon?: LucideIcon
  trend?: { value: string; direction: "up" | "down" | "neutral" }
  variant?: "default" | "success" | "warning" | "destructive"
  className?: string
}

const variantClasses = {
  default: "text-foreground",
  success: "text-success",
  warning: "text-warning",
  destructive: "text-destructive",
}

export function MetricCard({ label, value, icon: Icon, trend, variant = "default", className }: MetricCardProps) {
  return (
    <Card className={cn("p-4 transition-shadow hover:shadow-md", className)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">{label}</p>
          <p className={cn("mt-1.5 text-2xl font-semibold font-mono", variantClasses[variant])}>{value}</p>
          {trend && (
            <p
              className={cn(
                "mt-1 text-xs font-medium",
                trend.direction === "up" && "text-success",
                trend.direction === "down" && "text-destructive",
                trend.direction === "neutral" && "text-muted-foreground"
              )}
            >
              {trend.value}
            </p>
          )}
        </div>
        {Icon && (
          <div className="rounded-lg bg-accent p-2">
            <Icon className="h-4 w-4 text-primary" />
          </div>
        )}
      </div>
    </Card>
  )
}