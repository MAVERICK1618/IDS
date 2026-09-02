export type AgentType = "blue" | "red" | "orchestrator"

export interface AgentMessage {
  id: string
  timestamp: string
  agent: AgentType
  text: string
}