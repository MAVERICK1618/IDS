import { memo } from "react"
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "@/components/ui/tooltip"
import { LoadingState } from "@/components/LoadingState"
import { cn } from "@/lib/utils"
import { Globe, Server, Monitor, Globe2, Wifi } from "lucide-react"
import { type NetworkConfig } from "@/types/network"
import { buildTopologyNodes } from "@/data/mockTopology"

interface TopologyViewProps {
  config: NetworkConfig
  loading?: boolean
}

const iconMap = {
  internet: Globe,
  dmz: Server,
  internal: Monitor,
  dns: Globe2,
  dhcp: Wifi,
}

function statusDot(status: "online" | "warning" | "offline") {
  return cn(
    "h-2 w-2 rounded-full",
    status === "online" && "bg-success",
    status === "warning" && "bg-warning",
    status === "offline" && "bg-destructive"
  )
}

function NodeBox({ node }: { node: ReturnType<typeof buildTopologyNodes>[number] }) {
  const Icon = iconMap[node.type]
  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <div className="flex min-w-35 flex-col items-center gap-2 rounded-lg border border-border bg-card px-5 py-4 shadow-sm transition-shadow hover:shadow-md cursor-default" />
        }
      >
        <div className="flex items-center gap-2">
          <div className="rounded-md bg-accent p-1.5">
            <Icon className="h-4 w-4 text-primary" />
          </div>
          <span className={statusDot(node.status)} />
        </div>
        <div className="text-center">
          <p className="text-sm font-semibold">{node.label}</p>
          {node.count !== undefined && (
            <p className="font-mono text-xs text-muted-foreground">× {String(node.count).padStart(2, "0")}</p>
          )}
        </div>
      </TooltipTrigger>
      <TooltipContent>
        <p className="text-xs">{node.detail}</p>
      </TooltipContent>
    </Tooltip>
  )
}

function TopologyViewComponent({ config, loading }: TopologyViewProps) {
  if (loading) return <LoadingState rows={4} />

  const nodes = buildTopologyNodes(config)
  const [internet, dmz, internal, dns, dhcp] = nodes

  return (
    <TooltipProvider>
      <div className="flex flex-col items-center gap-1 py-6">
        <NodeBox node={internet} />
        <div className="h-6 w-px bg-border" />
        <NodeBox node={dmz} />
        <div className="h-6 w-px bg-border" />
        <NodeBox node={internal} />

        {/* Branches for DNS + DHCP off the DMZ layer */}
        <div className="mt-6 flex items-start gap-10">
          <div className="flex flex-col items-center gap-1">
            <div className="h-4 w-px bg-border" />
            <NodeBox node={dns} />
          </div>
          <div className="flex flex-col items-center gap-1">
            <div className="h-4 w-px bg-border" />
            <NodeBox node={dhcp} />
          </div>
        </div>
      </div>
    </TooltipProvider>
  )
}

export const TopologyView = memo(TopologyViewComponent)
