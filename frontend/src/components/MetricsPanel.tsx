import { memo } from "react"
import { cn } from "@/lib/utils"
import { ConfusionMatrix } from "@/components/ConfusionMatrix"
import { EmptyState } from "@/components/EmptyState"
import { AnimatedNumber } from "@/components/AnimatedNumber"
import { type EvaluationResult, type Metrics, type ConfusionMatrixData } from "@/types/evaluation"
import { BarChart3, TrendingUp, TrendingDown, AlertTriangle, CheckCircle2 } from "lucide-react"

interface MetricsPanelProps {
  evaluation: EvaluationResult | null
}

const metricLabels: { key: keyof Metrics; label: string }[] = [
  { key: "accuracy", label: "Accuracy" },
  { key: "precision", label: "Precision" },
  { key: "recall", label: "Recall" },
  { key: "f1Score", label: "F1 Score" },
]

function MetricsPanelComponent({ evaluation }: MetricsPanelProps) {
  if (!evaluation) {
    return (
      <EmptyState
        icon={BarChart3}
        title="No evaluation data yet"
        description="Run validation to see accuracy, precision, recall and F1 score"
      />
    )
  }

  // Convert new format to old format for compatibility
  const matrix = evaluation.matrix || {
    truePositive: 0,
    falseNegative: 0,
    falsePositive: 0,
    trueNegative: 0,
  } as ConfusionMatrixData
  
  const metrics = evaluation.metrics || {
    accuracy: evaluation.accuracy * 100,
    precision: evaluation.precision * 100,
    recall: evaluation.recall * 100,
    f1Score: evaluation.f1 * 100,
  } as Metrics
  
  const previousMetrics = evaluation.previousMetrics

  // Warning logic: flag if recall dropped meaningfully vs previous cycle, or recall is just low
  const recallDelta = previousMetrics ? metrics.recall - previousMetrics.recall : 0
  const hasHighFalseNegatives = metrics.recall < 50
  const recallDropped = previousMetrics !== null && recallDelta < -2

  return (
    <div className="space-y-4">
      {/* Metric cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {metricLabels.map(({ key, label }) => {
          const value = metrics[key]
          const prev = previousMetrics?.[key]
          const delta = prev !== undefined ? Number((value - prev).toFixed(1)) : null
          return (
            <div key={key} className="rounded-lg border border-border bg-card p-3">
              <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
              <p className="mt-1 font-mono text-xl font-semibold">
                <AnimatedNumber value={value} decimals={1} suffix="%" />
              </p>
              {delta !== null && delta !== 0 && (
                <p
                  className={cn(
                    "mt-0.5 flex items-center gap-1 text-[10px] font-medium",
                    delta > 0 ? "text-success" : "text-destructive"
                  )}
                >
                  {delta > 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                  {delta > 0 ? "+" : ""}
                  {delta}% vs last cycle
                </p>
              )}
            </div>
          )
        })}
      </div>

      {/* Warning / healthy state */}
      {hasHighFalseNegatives || recallDropped ? (
        <div className="flex items-start gap-2.5 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2.5">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
          <div>
            <p className="text-xs font-semibold text-destructive">HIGH FALSE NEGATIVES DETECTED</p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {hasHighFalseNegatives && `The model is missing ${matrix.falseNegative} attacks, classifying them as benign traffic. Recall is ${metrics.recall}%.`}
              {!hasHighFalseNegatives && recallDropped && `Recall has decreased by ${Math.abs(recallDelta).toFixed(1)}% compared with the previous evaluation.`}
            </p>
          </div>
        </div>
      ) : (
        <div className="flex items-center gap-2.5 rounded-lg border border-success/30 bg-success/10 px-3 py-2.5">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-success" />
          <p className="text-xs font-semibold text-success">MODEL PERFORMANCE NORMAL</p>
        </div>
      )}

      {/* Confusion matrix */}
      <div>
        <p className="mb-2 text-xs font-medium text-muted-foreground">Confusion Matrix</p>
        <ConfusionMatrix data={matrix} />
      </div>
    </div>
  )
}

export const MetricsPanel = memo(MetricsPanelComponent)
