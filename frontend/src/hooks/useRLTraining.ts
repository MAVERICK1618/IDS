import { useState, useRef, useEffect } from "react"
import { type TrainingPoint } from "@/types/rl"

const MAX_POINTS = 40

function nextPoint(prev: TrainingPoint | null): TrainingPoint {
  const cycle = (prev?.cycle ?? 0) + 1
  // Reward trends upward with noise, asymptoting near 0.95
  const prevReward = prev?.reward ?? 0.1
  const reward = Math.min(0.97, prevReward + (Math.random() * 0.08 - 0.015))
  const prevAccuracy = prev?.accuracy ?? 0.5
  const accuracy = Math.min(0.98, prevAccuracy + (Math.random() * 0.03 - 0.005))
  const prevLoss = prev?.loss ?? 0.9
  const loss = Math.max(0.03, prevLoss - (Math.random() * 0.05 - 0.01))

  return {
    cycle,
    reward: Number(reward.toFixed(3)),
    accuracy: Number(accuracy.toFixed(3)),
    loss: Number(loss.toFixed(3)),
  }
}

export function useRLTraining(active: boolean) {
  const [points, setPoints] = useState<TrainingPoint[]>([])
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (active) {
      intervalRef.current = setInterval(() => {
        setPoints((prev) => {
          const next = [...prev, nextPoint(prev[prev.length - 1] ?? null)]
          return next.slice(-MAX_POINTS)
        })
      }, 1200)
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [active])

  const latest = points[points.length - 1] ?? null

  return { points, latest }
}