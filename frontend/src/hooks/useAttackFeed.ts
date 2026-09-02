import { useState, useRef, useEffect, useCallback } from "react"
import { getAllAlerts, type AlertsResponse, type AlertData } from "@/services/api"
import { type Attack, type AttackType, type Severity } from "@/types/attack"

const MAX_ATTACKS = 40

// Map attack detector names to AttackType
const attackTypeMap: Record<string, AttackType> = {
  "Port Scan": "Port Scan",
  "SSH": "Brute Force",
  "DDoS": "DDoS",
  "SQL": "SQL Injection",
  "Malware": "Malware Traffic",
  "Unauthorized": "Unauthorized Access",
}

function getAttackType(detectorName: string): AttackType {
  for (const [key, value] of Object.entries(attackTypeMap)) {
    if (detectorName.toLowerCase().includes(key.toLowerCase())) {
      return value
    }
  }
  return "Port Scan" as AttackType
}

export function useAttackFeed(active: boolean) {
  const [attacks, setAttacks] = useState<Attack[]>([])
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (active) {
      // Fetch alerts
      const fetchAttacks = async () => {
        try {
          const response = await getAllAlerts() as AlertsResponse
          const alerts = response.alerts || []
          
          // Transform alerts to Attack format
          const attacks: Attack[] = alerts
            .slice(0, MAX_ATTACKS)
            .map((alert: AlertData, index: number) => ({
              id: String(alert.id || index),
              type: getAttackType(String(alert.type || alert.detector_name || "Port Scan")),
              severity: (String(alert.severity || "medium").toLowerCase()) as Severity,
              status: "active" as const,
              timestamp: new Date().toLocaleTimeString(),
              sourceIp: String(alert.source_ip || alert.src_ip || "0.0.0.0"),
              targetIp: String(alert.target_ip || alert.dst_ip || "0.0.0.0"),
              port: parseInt(String(alert.port || alert.destination_port || "0"), 10),
              acknowledged: false,
            }))

          setAttacks(attacks)
          setError(null)
        } catch (err) {
          setError(err instanceof Error ? err.message : "Failed to fetch alerts")
        }
      }

      fetchAttacks()
      intervalRef.current = setInterval(fetchAttacks, 4000)
    }

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [active])

  const acknowledge = useCallback((id: string) => {
    setAttacks((prev) => prev.map((a) => (a.id === id ? { ...a, acknowledged: true } : a)))
  }, [])

  return { attacks, error, acknowledge }
}