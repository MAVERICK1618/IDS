import { useState, useCallback } from "react"

export type SystemState = "idle" | "starting" | "running" | "stopping" | "deploying" | "error"

export function useSystemStatus() {
  const [state, setState] = useState<SystemState>("idle")

  const start = useCallback(() => {
    setState("starting")
    setTimeout(() => setState("running"), 1500)
  }, [])

  const stop = useCallback(() => {
    setState("stopping")
    setTimeout(() => setState("idle"), 1200)
  }, [])

  const clean = useCallback(() => {
    setState("idle")
  }, [])

  const deployStart = useCallback(() => {
    setState("deploying")
  }, [])

  const deployFinish = useCallback(() => {
    setState("running")
  }, [])

  const cancel = useCallback(() => {
    setState("idle")
  }, [])

  return { state, start, stop, clean, deployStart, deployFinish, cancel }
}