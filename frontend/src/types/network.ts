export interface NetworkNode {
  id: string
  label: string
  type: "internet" | "dmz" | "internal" | "dns" | "dhcp"
  count?: number
  status: "online" | "warning" | "offline"
  detail: string
}

export interface NetworkConfig {
  dmzServers: number
  internalHosts: number
  dnsServers: number
  dhcpServers: number
}