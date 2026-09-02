import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { StatusIndicator } from "@/components/StatusIndicator"
import { Play, Square, Trash2, Rocket, XCircle, Loader2 } from "lucide-react"
import { type SystemState } from "@/hooks/useSystemStatus"
import { cn } from "@/lib/utils"
import { toast } from "sonner"

interface ControlBarProps {
  state: SystemState
  onStart: () => void
  onStop: () => void
  onClean: () => void
  onDeployClick: () => void
  onCancel: () => void
}

const statusMap: Record<SystemState, { status: "active" | "inactive" | "warning" | "error"; label: string }> = {
  idle: { status: "inactive", label: "System Idle" },
  starting: { status: "warning", label: "Starting..." },
  running: { status: "active", label: "System Active" },
  stopping: { status: "warning", label: "Stopping..." },
  deploying: { status: "warning", label: "Deploying..." },
  error: { status: "error", label: "System Error" },
}

export function ControlBar({ state, onStart, onStop, onClean, onDeployClick, onCancel }: ControlBarProps) {
  const busy = state === "starting" || state === "stopping" || state === "deploying"

  return (
    <Card className="p-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <Button
            size="sm"
            className={cn(
              "gap-1.5 transition-transform duration-150 hover:-translate-y-0.5 active:translate-y-0",
              state === "idle" && "ring-2 ring-primary/25"
            )}
            disabled={state === "running" || busy}
            onClick={() => {
              onStart()
              toast.success("System starting", { description: "Initializing IDS pipeline..." })
            }}
          >
            {state === "starting" ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
            Start
          </Button>

          <AlertDialog>
            <AlertDialogTrigger
              render={
                <Button
                  size="sm"
                  variant="secondary"
                  className="gap-1.5 transition-transform duration-150 hover:-translate-y-0.5 active:translate-y-0"
                  disabled={state === "idle" || busy}
                />
              }
            >
              {state === "stopping" ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Square className="h-3.5 w-3.5" />}
              Stop
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Stop the system?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will halt live capture, attacks, and detectors. You can restart at any time.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={() => {
                    onStop()
                    toast("System stopping", { description: "Shutting down active processes..." })
                  }}
                >
                  Stop System
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>

          <div className="mx-1 h-5 w-px bg-border" />

          <AlertDialog>
            <AlertDialogTrigger
              render={
                <Button
                  size="sm"
                  variant="outline"
                  className="gap-1.5 transition-transform duration-150 hover:-translate-y-0.5 active:translate-y-0"
                  disabled={busy}
                />
              }
            >
              <Trash2 className="h-3.5 w-3.5" /> Clean
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Clean all data?</AlertDialogTitle>
                <AlertDialogDescription>
                  This clears packet logs, alerts, and evaluation results. This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={() => {
                    onClean()
                    toast.success("Data cleaned", { description: "All logs and results cleared." })
                  }}
                >
                  Clean
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>

          <Button
            size="sm"
            variant="outline"
            className="gap-1.5 transition-transform duration-150 hover:-translate-y-0.5 active:translate-y-0"
            disabled={busy}
            onClick={onDeployClick}
          >
            {state === "deploying" ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Rocket className="h-3.5 w-3.5" />}
            Deploy
          </Button>

          <Button
            size="sm"
            variant="ghost"
            className="gap-1.5 text-destructive hover:text-destructive transition-transform duration-150 hover:-translate-y-0.5 active:translate-y-0"
            disabled={!busy}
            onClick={() => {
              onCancel()
              toast.error("Operation cancelled")
            }}
          >
            <XCircle className="h-3.5 w-3.5" /> Cancel
          </Button>
        </div>

        <StatusIndicator status={statusMap[state].status} label={statusMap[state].label} />
      </div>
    </Card>
  )
}
