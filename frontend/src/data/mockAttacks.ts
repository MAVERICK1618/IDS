import { type Attack, type AttackType, type Severity, type AttackStatus } from "@/types/attack"

const attackTypes: AttackType[] = ["Port Scan", "DDoS", "Brute Force", "SQL Injection", "Malware Traffic", "Unauthorized Access"]
const severities: Severity[] = ["critical", "high", "medium", "low"]
const statuses: AttackStatus[] = ["active", "mitigated", "investigating"]
const internalIps = ["10.10.10.101", "10.10.10.102", "10.10.10.110", "10.10.10.115"]
const externalIps = ["185.220.101.4", "45.155.205.23", "192.241.220.17", "104.244.72.115"]

function randomFrom<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]
}

function randomPort(): number {
  const common = [22, 80, 443, 21, 3389, 53, 3306]
  return randomFrom(common)
}

let counter = 0

export function generateMockAttack(): Attack {
  counter += 1
  return {
    id: `atk-${Date.now()}-${counter}`,
    timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
    type: randomFrom(attackTypes),
    sourceIp: randomFrom(externalIps),
    targetIp: randomFrom(internalIps),
    port: randomPort(),
    severity: randomFrom(severities),
    status: randomFrom(statuses),
    acknowledged: false,
  }
}