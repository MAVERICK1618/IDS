export interface ConfusionMatrixData {
  truePositive: number
  falseNegative: number
  falsePositive: number
  trueNegative: number
}

export interface Metrics {
  accuracy: number
  precision: number
  recall: number
  f1Score: number
}

export interface MetricTrend {
  accuracy: number
  precision: number
  recall: number
  f1Score: number
}

export interface DetectorMetrics {
  name: string
  precision: number
  recall: number
  f1: number
}

export interface EvaluationResult {
  timestamp?: string
  precision: number
  recall: number
  f1: number
  accuracy: number
  detectors?: DetectorMetrics[]
  matrix?: ConfusionMatrixData
  metrics?: Metrics
  previousMetrics?: Metrics | null
  cycle?: number
}