import { Card } from "@/components/ui/card"
import { SectionHeader } from "@/components/SectionHeader"
import { AttackTimeline } from "@/components/AttackTimeline"
import { useAttackFeed } from "@/hooks/useAttackFeed"
import { ShieldAlert } from "lucide-react"

export function AttackTimelinePanel({ active }: { active: boolean }) {
  const { attacks, error, acknowledge } = useAttackFeed(active)

  return (
    <Card className="p-4 min-h-[420px] card-depth h-full">
      <SectionHeader title="Attack Timeline" description="Detected threats" icon={ShieldAlert} />
      {error && (
        <div className="mb-3 p-2 bg-destructive/10 border border-destructive/30 rounded text-sm text-destructive">
          {error}
        </div>
      )}
      <AttackTimeline attacks={attacks} onAcknowledge={acknowledge} />
    </Card>
  )
}
