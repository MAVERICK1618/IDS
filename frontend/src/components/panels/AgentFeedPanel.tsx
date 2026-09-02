import { Card } from "@/components/ui/card"
import { SectionHeader } from "@/components/SectionHeader"
import { AgentFeed } from "@/components/AgentFeed"
import { useAgentFeed } from "@/hooks/useAgentFeed"
import { MessageSquare } from "lucide-react"

export function AgentFeedPanel({ active }: { active: boolean }) {
  const { messages, error } = useAgentFeed(active)

  return (
    <Card className="p-4 min-h-[420px] card-depth h-full">
      <SectionHeader title="Agent Communications" description="Blue / Red / Orchestrator" icon={MessageSquare} />
      {error && (
        <div className="mb-3 p-2 bg-destructive/10 border border-destructive/30 rounded text-sm text-destructive">
          {error}
        </div>
      )}
      <AgentFeed messages={messages} />
    </Card>
  )
}
