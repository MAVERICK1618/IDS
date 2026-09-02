export type PacketAction = "allowed" | "blocked" | "suspicious"
export type Protocol = "TCP" | "UDP" | "ICMP" | "HTTP" | "HTTPS" | "SSH" | "DNS"

export interface Packet {
  id: string
  timestamp: string
  sourceIp: string
  destinationIp: string
  sourcePort: number
  destinationPort: number
  protocol: Protocol
  anomalyScore: number
  confidence: number
  action: PacketAction
}