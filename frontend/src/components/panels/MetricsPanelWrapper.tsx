import { Card } from "@/components/ui/card"
import { SectionHeader } from "@/components/SectionHeader"
import { MetricsPanel } from "@/components/MetricsPanel"
import { useEvaluation } from "@/hooks/useEvaluation"
import { BarChart3 } from "lucide-react"

export function MetricsPanelWrapper({ active }: { active: boolean }) {
  const { evaluation, error } = useEvaluation(active)
  return (
    <Card className="p-4 min-h-[420px] card-depth">
      <SectionHeader title="Model Metrics" description="Confusion matrix & evaluation scores" icon={BarChart3} />
      {error && (
        <div className="mb-3 p-2 bg-destructive/10 border border-destructive/30 rounded text-sm text-destructive">
          {error}
        </div>
      )}
      <MetricsPanel evaluation={evaluation} />
    </Card>
  )
}
