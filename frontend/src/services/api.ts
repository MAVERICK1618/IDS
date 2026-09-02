/**
 * API Client Service
 * Centralized API communication layer for all backend requests
 */

// API Response Types
export interface AgentMessage {
  time: string
  text: string
  type: string
  status: string
}

export interface AgentMessagesResponse {
  total: number
  messages: AgentMessage[]
}

export interface TrafficRow {
  "Source IP"?: string
  "Destination IP"?: string
  "Source Port"?: string
  "Destination Port"?: string
  "Protocol"?: string
  [key: string]: unknown
}

export interface TrafficLiveResponse {
  total: number
  showing: number
  rows: TrafficRow[]
}

export interface AlertData {
  id?: string | number
  type?: string
  detector_name?: string
  severity?: string
  source_ip?: string
  src_ip?: string
  target_ip?: string
  dst_ip?: string
  port?: string | number
  destination_port?: string | number
  [key: string]: unknown
}

export interface AlertsResponse {
  total: number
  alerts: AlertData[]
}

export interface DetectorMetrics {
  name: string
  precision: number
  recall: number
  f1: number
}

export interface MetricsResponse {
  timestamp?: string
  overall?: {
    avg_precision: number
    avg_recall: number
    avg_f1: number
    total_tp: number
    total_fp: number
    total_fn: number
  }
  per_detector?: DetectorMetrics[]
}

export interface ApiError {
  message: string
  status?: number
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/**
 * Generic fetch wrapper with error handling and base URL
 */
async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
      ...options,
      credentials: "include", // Include cookies for cross-origin requests
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({})) as Record<string, unknown>;
      throw {
        message: (errorData.error as string) || `HTTP ${response.status}`,
        status: response.status,
      } as ApiError;
    }

    return response.json() as Promise<T>;
  } catch (error) {
    if (error instanceof Error) {
      throw {
        message: error.message,
      } as ApiError;
    }
    throw error;
  }
}

/**
 * Pipeline Status APIs
 */
export async function getPipelineStatus() {
  return apiFetch("/api/status");
}

export async function getPipelineCheckpoints() {
  return apiFetch("/api/pipeline/checkpoints");
}

/**
 * Agent Communication APIs
 */
export async function getAgentMessages(): Promise<AgentMessagesResponse> {
  return apiFetch("/api/agent/messages");
}

export async function getAgentNodes() {
  return apiFetch("/api/agent/nodes");
}

/**
 * Alerts APIs
 */
export async function getAllAlerts(): Promise<AlertsResponse> {
  return apiFetch("/api/alerts");
}

export async function getAlertsByDetector(detectorName: string) {
  return apiFetch(`/api/alerts/${encodeURIComponent(detectorName)}`);
}

/**
 * ML Predictions APIs
 */
export async function getAllPredictions() {
  return apiFetch("/api/predictions");
}

export async function getPredictionsByDetector(detectorName: string) {
  return apiFetch(`/api/predictions/${encodeURIComponent(detectorName)}`);
}

/**
 * Ground Truth APIs
 */
export async function getGroundTruthSummary() {
  return apiFetch("/api/ground-truth");
}

export async function getGroundTruthByType(attackType: string) {
  return apiFetch(`/api/ground-truth/${encodeURIComponent(attackType)}`);
}

/**
 * Metrics APIs
 */
export async function getMetrics(): Promise<MetricsResponse> {
  return apiFetch("/api/metrics");
}

export async function getMetricsChart(chartName: string) {
  return `${API_BASE_URL}/api/metrics/chart/${encodeURIComponent(chartName)}`;
}

/**
 * Live Traffic APIs
 */
export async function getTrafficSummary() {
  return apiFetch("/api/traffic/summary");
}

export async function getTrafficLive(): Promise<TrafficLiveResponse> {
  return apiFetch("/api/traffic/live");
}

/**
 * Logs APIs
 */
export async function listLogs() {
  return apiFetch("/api/logs");
}

export async function getLog(logName: string) {
  return apiFetch(`/api/logs/${encodeURIComponent(logName)}`);
}

/**
 * Feedback/Retraining APIs
 */
export async function getFeedbackStatus() {
  return apiFetch("/api/feedback/status");
}

export async function getMissedAttacks() {
  return apiFetch("/api/feedback/missed-attacks");
}

/**
 * Lab/Emulator APIs
 */
export async function getLabHosts() {
  return apiFetch("/api/lab/hosts");
}

export async function getLabTopology() {
  return apiFetch("/api/lab/topology");
}

/**
 * Dashboard APIs (Master Endpoint)
 */
export async function getDashboard() {
  return apiFetch("/api/dashboard");
}

