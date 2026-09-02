import { type AgentMessage, type AgentType } from "@/types/agent"

const blueMessages = [
  "Detected abnormal traffic from {ip}",
  "Traffic blocked successfully",
  "Anomaly score exceeded threshold on {ip}",
  "Signature match: possible port scan",
  "Session terminated for {ip}",
]

const redMessages = [
  "Attempting port scan on {ip}",
  "Initiating brute-force sequence on SSH",
  "Probing for open services on {ip}",
  "Escalation attempt on internal host",
  "Deploying lateral movement payload",
]

const orchestratorMessages = [
  "Escalating event to threat analysis",
  "Coordinating response across agents",
  "Updating detection policy",
  "Logging incident for review",
  "Synchronizing agent state",
]

const ips = ["10.10.10.101", "10.10.10.102", "10.10.10.115", "10.10.10.1", "185.220.101.4"]

function randomFrom<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]
}

function fillTemplate(template: string): string {
  return template.replace("{ip}", randomFrom(ips))
}

let counter = 0

export function generateMockAgentMessage(): AgentMessage {
  counter += 1
  const agent: AgentType = randomFrom<AgentType>(["blue", "red", "orchestrator"])
  const pool = agent === "blue" ? blueMessages : agent === "red" ? redMessages : orchestratorMessages
  return {
    id: `msg-${Date.now()}-${counter}`,
    timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
    agent,
    text: fillTemplate(randomFrom(pool)),
  }
}