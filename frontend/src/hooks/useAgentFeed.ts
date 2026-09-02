import { useState, useRef, useEffect } from "react"
import { getAgentMessages, type AgentMessagesResponse } from "@/services/api"
import { type AgentMessage } from "@/types/agent"

const MAX_MESSAGES = 50

export function useAgentFeed(active: boolean) {
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (active) {
      // Fetch immediately
      const fetchMessages = async () => {
        try {
          const response = await getAgentMessages() as AgentMessagesResponse
          const apiMessages = response.messages || []
          
          // Transform API messages to AgentMessage format
          const agentMessages: AgentMessage[] = apiMessages
            .slice(0, MAX_MESSAGES)
            .map((msg, index) => ({
              id: String(index),
              timestamp: msg.time || new Date().toISOString(),
              agent: (msg.type === "error" ? "red" : msg.type === "checkpoint" ? "orchestrator" : "blue") as "blue" | "red" | "orchestrator",
              text: msg.text || "",
            }))
          
          setMessages(agentMessages)
          setError(null)
        } catch (err) {
          setError(err instanceof Error ? err.message : "Failed to fetch agent messages")
        }
      }

      fetchMessages()

      // Poll for new messages
      intervalRef.current = setInterval(fetchMessages, 3000)
    }

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [active])

  return { messages, error }
}