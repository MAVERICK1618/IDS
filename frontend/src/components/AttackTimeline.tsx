import { useState, useMemo, memo } from "react"
import { cn } from "@/lib/utils"
import { type Attack, type Severity } from "@/types/attack"
import { SeverityBadge } from "@/components/SeverityBadge"
import { EmptyState } from "@/components/EmptyState"
import { Button } from "@/components/ui/button"
import { ShieldAlert, ChevronDown, Check } from "lucide-react"

interface AttackTimelineProps {
  attacks: Attack[]
  onAcknowledge: (id: string) => void
}

const severityOrder: Severity[] = ["critical", "high", "medium", "low"]

const statusStyles: Record<Attack["status"], string> = {
  active: "text-destructive",
  investigating: "text-warning",
  mitigated: "text-success",
}

function AttackTimelineComponent({ attacks, onAcknowledge }: AttackTimelineProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const counts = useMemo(() => {
    return severityOrder.reduce(
      (acc, sev) => {
        acc[sev] = attacks.filter((a) => a.severity === sev).length
        return acc
      },
      {} as Record<Severity, number>
    )
  }, [attacks])

  const newestId = attacks[0]?.id

  if (attacks.length === 0) {
    return (
      <EmptyState
        icon={ShieldAlert}
        title="No attacks detected"
        description="Attack events will be logged here as they occur"
      />
    )
  }

  return (
    <div>
      {/* Severity counters */}
      <div className="grid grid-cols-4 gap-2 mb-3">
        {severityOrder.map((sev) => (
          <div key={sev} className="rounded-md border border-border bg-muted/40 px-2.5 py-1.5 text-center">
            <p className="font-mono text-lg font-semibold">{String(counts[sev]).padStart(2, "0")}</p>
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground">{sev}</p>
          </div>
        ))}
      </div>

      {/* Timeline list */}
      <div className="max-h-72 space-y-1.5 overflow-y-auto pr-1">
        {attacks.map((attack) => {
          const expanded = expandedId === attack.id
          return (
            <div
              key={attack.id}
              className={cn(
                "rounded-lg border border-border bg-card",
                attack.id === newestId && "animate-in fade-in slide-in-from-top-1 duration-300",
                attack.acknowledged && "opacity-60"
              )}
            >
              <button
                className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left"
                onClick={() => setExpandedId(expanded ? null : attack.id)}
              >
                <div className="flex min-w-0 flex-1 items-center gap-3">
                  <SeverityBadge severity={attack.severity} />
                  <span className="truncate text-sm font-medium">{attack.type}</span>
                  <span className={cn("text-xs font-medium capitalize shrink-0", statusStyles[attack.status])}>
                    {attack.status}
                  </span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="font-mono text-[10px] text-muted-foreground">{attack.timestamp}</span>
                  <ChevronDown className={cn("h-3.5 w-3.5 text-muted-foreground transition-transform", expanded && "rotate-180")} />
                </div>
              </button>

              {expanded && (
                <div className="border-t border-border px-3 py-2.5">
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 font-mono text-xs">
                    <div>
                      <span className="text-muted-foreground">Source: </span>
                      {attack.sourceIp}
                    </div>
                    <div>
                      <span className="text-muted-foreground">Target: </span>
                      {attack.targetIp}
                    </div>
                    <div>
                      <span className="text-muted-foreground">Port: </span>
                      {attack.port}
                    </div>
                  </div>
                  {!attack.acknowledged && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="mt-2.5 h-7 gap-1.5 text-xs"
                      onClick={(e) => {
                        e.stopPropagation()
                        onAcknowledge(attack.id)
                      }}
                    >
                      <Check className="h-3 w-3" /> Acknowledge
                    </Button>
                  )}
                  {attack.acknowledged && (
                    <p className="mt-2.5 text-xs text-success flex items-center gap-1.5">
                      <Check className="h-3 w-3" /> Acknowledged
                    </p>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export const AttackTimeline = memo(AttackTimelineComponent)
