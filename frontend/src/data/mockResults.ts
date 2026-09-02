import { type ResultImage } from "@/types/results"

export function generateMockResults(): ResultImage[] {
  return [
    { id: "confusion-matrix", title: "Confusion Matrix", description: "TP/FP/TN/FN breakdown", status: "ready", placeholder: true },
    { id: "roc-curve", title: "ROC Curve", description: "True vs false positive rate", status: "ready", placeholder: true },
    { id: "pr-curve", title: "Precision-Recall Curve", description: "Precision vs recall trade-off", status: "ready", placeholder: true },
    { id: "training-reward", title: "Training Reward", description: "RL reward over training cycles", status: "ready", placeholder: true },
    { id: "attack-distribution", title: "Attack Distribution", description: "Breakdown by attack type", status: "loading", placeholder: true },
    { id: "detection-performance", title: "Detection Performance", description: "Per-detector accuracy comparison", status: "missing", placeholder: true },
  ]
}