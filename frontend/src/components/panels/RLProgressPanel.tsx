import { Card } from "@/components/ui/card"
import { SectionHeader } from "@/components/SectionHeader"
import { RLProgress } from "@/components/RLProgress"
import { useRLTraining } from "@/hooks/useRLTraining"
import { Brain } from "lucide-react"

export function RLProgressPanel({ active }: { active: boolean }) {
  const { points, latest } = useRLTraining(active)

  return (
    <Card className="p-4 min-h-[420px] card-depth h-full">
      <SectionHeader title="RL Learning Progress" description="Training performance" icon={Brain} />
      <RLProgress points={points} latest={latest} />
    </Card>
  )
}
