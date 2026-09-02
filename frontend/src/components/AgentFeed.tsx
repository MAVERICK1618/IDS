import { memo } from "react"
import { cn } from "@/lib/utils"
import { type AgentMessage, type AgentType } from "@/types/agent"
import { EmptyState } from "@/components/EmptyState"
import { MessageSquare, Shield, Swords, Bot } from "lucide-react"

interface AgentFeedProps {
  messages: AgentMessage[]
}

const agentConfig: Record<AgentType, { label: string; icon: typeof Shield; classes: string }> = {
  blue: { label: "BLUE AGENT", icon: Shield, classes: "text-info bg-info/10 border-info/20" },
  red: { label: "RED AGENT", icon: Swords, classes: "text-destructive bg-destructive/10 border-destructive/20" },
  orchestrator: { label: "ORCHESTRATOR", icon: Bot, classes: "text-primary bg-primary/10 border-primary/20" },
}

function AgentFeedComponent({ messages }: AgentFeedProps) {
  if (messages.length === 0) {
    return (
      <EmptyState
        icon={MessageSquare}
        title="No agent activity yet"
        description="Agent messages will appear here once the system starts"
      />
    )
  }

  return (
    <div className="max-h-80 space-y-2 overflow-y-auto rounded-md border border-border p-2">
      {messages.map((msg, i) => {
        const config = agentConfig[msg.agent]
        const Icon = config.icon
        return (
          <div
            key={msg.id}
            className={cn(
              "flex items-start gap-2.5 rounded-lg border px-3 py-2",
              config.classes,
              i === 0 && "animate-in fade-in slide-in-from-top-1 duration-300"
            )}
          >
            <Icon className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-semibold tracking-wide">{config.label}</span>
                <span className="font-mono text-[10px] text-muted-foreground">{msg.timestamp}</span>
              </div>
              <p className="mt-0.5 text-xs text-foreground">{msg.text}</p>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export const AgentFeed = memo(AgentFeedComponent)
