export type Severity = "critical" | "high" | "medium" | "low"
export type AttackStatus = "active" | "mitigated" | "investigating"

export type AttackType =
  | "Port Scan"
  | "DDoS"
  | "Brute Force"
  | "SQL Injection"
  | "Malware Traffic"
  | "Unauthorized Access"

export interface Attack {
  id: string
  timestamp: string
  type: AttackType
  sourceIp: string
  targetIp: string
  port: number
  severity: Severity
  status: AttackStatus
  acknowledged: boolean
}