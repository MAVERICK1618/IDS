export interface ResultImage {
  id: string
  title: string
  description: string
  status: "ready" | "loading" | "missing"
  // In real integration this would be a URL from the backend (ML/outputs/*.png)
  placeholder: boolean
}