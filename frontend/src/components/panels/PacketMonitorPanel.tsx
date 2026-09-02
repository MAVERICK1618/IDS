import { Card } from "@/components/ui/card"
import { SectionHeader } from "@/components/SectionHeader"
import { PacketMonitor } from "@/components/PacketMonitor"
import { usePacketStream } from "@/hooks/usePacketStream"
import { Activity } from "lucide-react"

export function PacketMonitorPanel({ active }: { active: boolean }) {
  const { packets, error } = usePacketStream(active)

  return (
    <Card className="p-4 min-h-[420px] card-depth h-full">
      <SectionHeader title="Live Packet Monitor" description="Real-time traffic feed" icon={Activity} />
      {error && (
        <div className="mb-3 p-2 bg-destructive/10 border border-destructive/30 rounded text-sm text-destructive">
          {error}
        </div>
      )}
      <PacketMonitor packets={packets} />
    </Card>
  )
}
