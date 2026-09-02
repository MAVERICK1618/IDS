import { type Packet, type Protocol, type PacketAction } from "@/types/packet"

const protocols: Protocol[] = ["TCP", "UDP", "ICMP", "HTTP", "HTTPS", "SSH", "DNS"]
const internalIps = ["10.10.10.101", "10.10.10.102", "10.10.10.103", "10.10.10.110", "10.10.10.115"]
const externalIps = ["185.220.101.4", "45.155.205.23", "192.241.220.17", "104.244.72.115", "10.10.10.1"]

function randomFrom<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]
}

function randomPort(): number {
  const common = [22, 80, 443, 21, 3389, 53, 8080]
  return Math.random() > 0.4 ? randomFrom(common) : Math.floor(1024 + Math.random() * 60000)
}

function deriveAction(anomalyScore: number): PacketAction {
  if (anomalyScore >= 0.75) return "blocked"
  if (anomalyScore >= 0.4) return "suspicious"
  return "allowed"
}

let counter = 0

export function generateMockPacket(): Packet {
  counter += 1
  const anomalyScore = Math.random()
  return {
    id: `pkt-${Date.now()}-${counter}`,
    timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
    sourceIp: Math.random() > 0.5 ? randomFrom(internalIps) : randomFrom(externalIps),
    destinationIp: Math.random() > 0.5 ? randomFrom(internalIps) : randomFrom(externalIps),
    sourcePort: randomPort(),
    destinationPort: randomPort(),
    protocol: randomFrom(protocols),
    anomalyScore: Number(anomalyScore.toFixed(2)),
    confidence: Number((0.6 + Math.random() * 0.4).toFixed(2)),
    action: deriveAction(anomalyScore),
  }
}

export function generatePacketBatch(count: number): Packet[] {
  return Array.from({ length: count }, () => generateMockPacket())
}