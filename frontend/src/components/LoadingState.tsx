import { cn } from "@/lib/utils"

interface LoadingStateProps {
  rows?: number
  className?: string
}

export function LoadingState({ rows = 3, className }: LoadingStateProps) {
  return (
    <div className={cn("space-y-2.5 py-2", className)}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-4 rounded-md bg-muted animate-pulse" style={{ width: `${85 - i * 10}%` }} />
      ))}
    </div>
  )
}