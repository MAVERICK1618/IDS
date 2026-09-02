import { memo } from "react"
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"
import { type ConfusionMatrixData } from "@/types/evaluation"

interface ConfusionMatrixProps {
  data: ConfusionMatrixData
}

interface CellConfig {
  label: string
  value: number
  sublabel: string
  detail: string
  classes: string
}

function ConfusionMatrixComponent({ data }: ConfusionMatrixProps) {
  const cells: CellConfig[] = [
    {
      label: "True Positive",
      value: data.truePositive,
      sublabel: "Detected",
      detail: "Malicious traffic correctly flagged as malicious.",
      classes: "bg-success/10 border-success/30 text-success",
    },
    {
      label: "False Negative",
      value: data.falseNegative,
      sublabel: "Missed",
      detail: "Malicious traffic incorrectly classified as benign — a missed attack.",
      classes: "bg-destructive/10 border-destructive/30 text-destructive",
    },
    {
      label: "False Positive",
      value: data.falsePositive,
      sublabel: "Blocked",
      detail: "Benign traffic incorrectly flagged as malicious — a false alarm.",
      classes: "bg-warning/10 border-warning/30 text-warning",
    },
    {
      label: "True Negative",
      value: data.trueNegative,
      sublabel: "Allowed",
      detail: "Benign traffic correctly classified as benign.",
      classes: "bg-info/10 border-info/30 text-info",
    },
  ]

  return (
    <TooltipProvider>
      <div className="grid grid-cols-[auto_1fr_1fr] gap-1.5 text-xs">
        <div />
        <div className="pb-1 text-center font-medium text-muted-foreground">Predicted Malicious</div>
        <div className="pb-1 text-center font-medium text-muted-foreground">Predicted Benign</div>

        <div className="flex items-center justify-center pr-1 text-center font-medium text-muted-foreground [writing-mode:vertical-rl] rotate-180">
          Actual Malicious
        </div>
        {[cells[0], cells[1]].map((cell) => (
          <Tooltip key={cell.label}>
            <TooltipTrigger
              render={
                <div
                  className={cn(
                    "flex flex-col items-center justify-center rounded-lg border py-4 cursor-default",
                    cell.classes
                  )}
                />
              }
            >
              <p className="font-mono text-2xl font-bold">{cell.value}</p>
              <p className="text-[10px] font-semibold uppercase tracking-wide">{cell.sublabel}</p>
            </TooltipTrigger>
            <TooltipContent className="max-w-[200px]">
              <p className="text-xs font-medium">{cell.label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{cell.detail}</p>
            </TooltipContent>
          </Tooltip>
        ))}

        <div className="flex items-center justify-center pr-1 text-center font-medium text-muted-foreground [writing-mode:vertical-rl] rotate-180">
          Actual Benign
        </div>
        {[cells[2], cells[3]].map((cell) => (
          <Tooltip key={cell.label}>
            <TooltipTrigger
              render={
                <div
                  className={cn(
                    "flex flex-col items-center justify-center rounded-lg border py-4 cursor-default",
                    cell.classes
                  )}
                />
              }
            >
              <p className="font-mono text-2xl font-bold">{cell.value}</p>
              <p className="text-[10px] font-semibold uppercase tracking-wide">{cell.sublabel}</p>
            </TooltipTrigger>
            <TooltipContent className="max-w-[200px]">
              <p className="text-xs font-medium">{cell.label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{cell.detail}</p>
            </TooltipContent>
          </Tooltip>
        ))}
      </div>
    </TooltipProvider>
  )
}

export const ConfusionMatrix = memo(ConfusionMatrixComponent)