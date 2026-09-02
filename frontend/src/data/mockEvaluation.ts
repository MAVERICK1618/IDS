import { type EvaluationResult, type ConfusionMatrixData, type Metrics } from "@/types/evaluation"

function computeMetrics(matrix: ConfusionMatrixData): Metrics {
  const { truePositive: tp, falseNegative: fn, falsePositive: fp, trueNegative: tn } = matrix
  const accuracy = (tp + tn) / (tp + tn + fp + fn)
  const precision = tp / (tp + fp || 1)
  const recall = tp / (tp + fn || 1)
  const f1Score = (2 * precision * recall) / (precision + recall || 1)
  return {
    accuracy: Number((accuracy * 100).toFixed(1)),
    precision: Number((precision * 100).toFixed(1)),
    recall: Number((recall * 100).toFixed(1)),
    f1Score: Number((f1Score * 100).toFixed(1)),
  }
}

export function generateMockEvaluation(previous: EvaluationResult | null): EvaluationResult {
  // Simulate a somewhat realistic, occasionally-weak-recall model like the reference screenshots
  const truePositive = 15 + Math.floor(Math.random() * 10)
  const falseNegative = 20 + Math.floor(Math.random() * 25)
  const falsePositive = 400 + Math.floor(Math.random() * 300)
  const trueNegative = 100 + Math.floor(Math.random() * 60)

  const matrix: ConfusionMatrixData = { truePositive, falseNegative, falsePositive, trueNegative }
  const metrics = computeMetrics(matrix)

  // Compute new format fields
  const accuracy = (truePositive + trueNegative) / (truePositive + trueNegative + falsePositive + falseNegative)
  const precision = truePositive / (truePositive + falsePositive || 1)
  const recall = truePositive / (truePositive + falseNegative || 1)
  const f1 = (2 * precision * recall) / (precision + recall || 1)

  return {
    timestamp: new Date().toISOString(),
    precision: Number((precision * 100).toFixed(1)) / 100,
    recall: Number((recall * 100).toFixed(1)) / 100,
    f1: Number((f1 * 100).toFixed(1)) / 100,
    accuracy: Number((accuracy * 100).toFixed(1)) / 100,
    matrix,
    metrics,
    previousMetrics: previous?.metrics ?? null,
    cycle: (previous?.cycle ?? 0) + 1,
  }
}