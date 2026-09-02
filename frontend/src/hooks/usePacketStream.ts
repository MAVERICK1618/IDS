import { useState, useRef, useCallback, useEffect } from "react"
import { getTrafficLive, type TrafficLiveResponse, type TrafficRow } from "@/services/api"
import { type Packet, type Protocol } from "@/types/packet"

const MAX_PACKETS = 100

export function usePacketStream(active: boolean) {
  const [packets, setPackets] = useState<Packet[]>([])
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (active) {
      // Fetch live traffic
      const fetchPackets = async () => {
        try {
          const response = await getTrafficLive() as TrafficLiveResponse
          const rows = response.rows || []
          
          // Transform CSV rows to Packet format
          const packets: Packet[] = rows
            .slice(-MAX_PACKETS)
            .map((row: TrafficRow, index: number) => {
              const protocol = String(row["Protocol"] || row["protocol"] || "TCP").toUpperCase() as Protocol
              return {
                id: `${Date.now()}-${index}`,
                timestamp: new Date().toLocaleTimeString(),
                sourceIp: String(row["Source IP"] || row["src_ip"] || "0.0.0.0"),
                destinationIp: String(row["Destination IP"] || row["dst_ip"] || "0.0.0.0"),
                sourcePort: parseInt(String(row["Source Port"] || row["src_port"] || "0"), 10),
                destinationPort: parseInt(String(row["Destination Port"] || row["port"] || "0"), 10),
                protocol: protocol,
                anomalyScore: Math.random(),
                confidence: Math.random(),
                action: (Math.random() > 0.7 ? "blocked" : Math.random() > 0.3 ? "suspicious" : "allowed") as "allowed" | "blocked" | "suspicious",
              }
            })

          setPackets(packets)
          setError(null)
        } catch (err) {
          setError(err instanceof Error ? err.message : "Failed to fetch traffic data")
        }
      }

      fetchPackets()
      intervalRef.current = setInterval(fetchPackets, 2000)
    }

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [active])

  const clearPackets = useCallback(() => setPackets([]), [])

  return { packets, error, clearPackets }
}