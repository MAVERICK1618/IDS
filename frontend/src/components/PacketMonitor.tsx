import { useMemo, useState, memo } from "react"
import { cn } from "@/lib/utils"
import { type Packet, type PacketAction } from "@/types/packet"
import { EmptyState } from "@/components/EmptyState"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Activity, Search } from "lucide-react"

interface PacketMonitorProps {
  packets: Packet[]
}

const actionStyles: Record<PacketAction, string> = {
  allowed: "text-success",
  blocked: "text-destructive",
  suspicious: "text-warning",
}

const actionDot: Record<PacketAction, string> = {
  allowed: "bg-success",
  blocked: "bg-destructive",
  suspicious: "bg-warning",
}

const filterOptions: { key: PacketAction | "all"; label: string }[] = [
  { key: "all", label: "All" },
  { key: "allowed", label: "Allowed" },
  { key: "suspicious", label: "Suspicious" },
  { key: "blocked", label: "Blocked" },
]

function PacketMonitorComponent({ packets }: PacketMonitorProps) {
  const [filter, setFilter] = useState<PacketAction | "all">("all")
  const [search, setSearch] = useState("")

  const counts = useMemo(() => {
    return {
      all: packets.length,
      allowed: packets.filter((p) => p.action === "allowed").length,
      suspicious: packets.filter((p) => p.action === "suspicious").length,
      blocked: packets.filter((p) => p.action === "blocked").length,
    }
  }, [packets])

  const filtered = useMemo(() => {
    return packets.filter((pkt) => {
      const matchesFilter = filter === "all" || pkt.action === filter
      const matchesSearch =
        search.trim() === "" ||
        pkt.sourceIp.includes(search.trim()) ||
        pkt.destinationIp.includes(search.trim())
      return matchesFilter && matchesSearch
    })
  }, [packets, filter, search])

  if (packets.length === 0) {
    return (
      <EmptyState
        icon={Activity}
        title="No packet data yet"
        description="Start the system to see real-time network traffic decisions"
      />
    )
  }

  return (
    <div>
      {/* Filters + search */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div className="flex flex-wrap gap-1.5">
          {filterOptions.map((opt) => (
            <Button
              key={opt.key}
              size="sm"
              variant={filter === opt.key ? "default" : "outline"}
              className="h-7 gap-1.5 px-2.5 text-xs"
              onClick={() => setFilter(opt.key)}
            >
              {opt.label}
              <span className="inline-block min-w-5 text-right font-mono text-[10px] opacity-70">{counts[opt.key]}</span>
            </Button>
          ))}
        </div>
        <div className="relative">
          <Search className="absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Filter by IP..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-7 w-44 pl-7 text-xs font-mono"
          />
        </div>
      </div>

      {/* Table */}
      <div className="max-h-80 overflow-y-auto overflow-x-auto rounded-md border border-border">
        <table className="w-full text-xs">
          <thead className="sticky top-0 bg-card">
            <tr className="border-b border-border text-left text-muted-foreground">
              <th className="py-2 pl-3 pr-3 font-medium">Time</th>
              <th className="py-2 pr-3 font-medium">Source</th>
              <th className="py-2 pr-3 font-medium">Destination</th>
              <th className="py-2 pr-3 font-medium">Protocol</th>
              <th className="py-2 pr-3 font-medium">Port</th>
              <th className="py-2 pr-3 font-medium">Anomaly</th>
              <th className="py-2 pr-3 font-medium">Confidence</th>
              <th className="py-2 pr-3 pr-3 font-medium">Action</th>
            </tr>
          </thead>
          <tbody className="font-mono">
            {filtered.map((pkt, i) => (
              <tr
                key={pkt.id}
                className={cn(
                  "border-b border-border/50 hover:bg-accent/50 transition-colors",
                  i === 0 && "animate-in fade-in slide-in-from-top-1 duration-300"
                )}
              >
                <td className="py-2 pl-3 pr-3 text-muted-foreground">{pkt.timestamp}</td>
                <td className="py-2 pr-3">{pkt.sourceIp}</td>
                <td className="py-2 pr-3">{pkt.destinationIp}</td>
                <td className="py-2 pr-3">{pkt.protocol}</td>
                <td className="py-2 pr-3 text-muted-foreground">{pkt.sourcePort} → {pkt.destinationPort}</td>
                <td className="py-2 pr-3">{pkt.anomalyScore.toFixed(2)}</td>
                <td className="py-2 pr-3">{(pkt.confidence * 100).toFixed(0)}%</td>
                <td className="py-2 pr-3">
                  <span className={cn("inline-flex items-center gap-1.5 font-sans font-medium capitalize", actionStyles[pkt.action])}>
                    <span className={cn("h-1.5 w-1.5 rounded-full", actionDot[pkt.action])} />
                    {pkt.action}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export const PacketMonitor = memo(PacketMonitorComponent)
