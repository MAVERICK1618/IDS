import { useState, useRef, useEffect } from "react"
import { getMetrics, type MetricsResponse, type DetectorMetrics } from "@/services/api"
import { type EvaluationResult } from "@/types/evaluation"

export function useEvaluation(active: boolean) {
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (active) {
      // Fetch metrics/evaluation
      const fetchEvaluation = async () => {
        try {
          const response = await getMetrics() as MetricsResponse
          
          const overallMetrics = response.overall || {
            avg_precision: 0,
            avg_recall: 0,
            avg_f1: 0,
            total_tp: 0,
            total_fp: 0,
            total_fn: 0,
          }
          const perDetector = response.per_detector || []

          const totalSamples = (overallMetrics.total_tp || 0) + (overallMetrics.total_fp || 0) + (overallMetrics.total_fn || 0)
          const accuracy = totalSamples > 0 ? (overallMetrics.total_tp || 0) / totalSamples : 0

          const evaluation: EvaluationResult = {
            timestamp: response.timestamp || new Date().toISOString(),
            precision: Number(overallMetrics.avg_precision) || 0,
            recall: Number(overallMetrics.avg_recall) || 0,
            f1: Number(overallMetrics.avg_f1) || 0,
            accuracy: accuracy,
            detectors: (perDetector as DetectorMetrics[]).map((d: DetectorMetrics) => ({
              name: String(d.name || "Unknown"),
              precision: Number(d.precision || 0),
              recall: Number(d.recall || 0),
              f1: Number(d.f1 || 0),
            })),
          }

          setEvaluation(evaluation)
          setError(null)
        } catch (err) {
          setError(err instanceof Error ? err.message : "Failed to fetch metrics")
          // Keep showing previous evaluation if available
        }
      }

      // Run first evaluation shortly after start
      const timeout = setTimeout(fetchEvaluation, 1000)

      // Then repeat every 8 seconds
      intervalRef.current = setInterval(fetchEvaluation, 8000)

      return () => {
        clearTimeout(timeout)
        if (intervalRef.current) clearInterval(intervalRef.current)
      }
    }
  }, [active])

  return { evaluation, error }
}