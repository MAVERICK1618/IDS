import { type NetworkConfig, type NetworkNode } from "@/types/network"

export function buildTopologyNodes(config: NetworkConfig): NetworkNode[] {
  return [
    {
      id: "internet",
      label: "Internet",
      type: "internet",
      status: "online",
      detail: "External network boundary",
    },
    {
      id: "dmz",
      label: "DMZ Servers",
      type: "dmz",
      count: config.dmzServers,
      status: "online",
      detail: `${config.dmzServers} server(s) — web, mail, DNS-facing`,
    },
    {
      id: "internal",
      label: "Internal LAN",
      type: "internal",
      count: config.internalHosts,
      status: "online",
      detail: `${config.internalHosts} blue-team client host(s)`,
    },
    {
      id: "dns",
      label: "DNS Servers",
      type: "dns",
      count: config.dnsServers,
      status: "online",
      detail: `${config.dnsServers} DNS resolution server(s)`,
    },
    {
      id: "dhcp",
      label: "DHCP Servers",
      type: "dhcp",
      count: config.dhcpServers,
      status: "online",
      detail: `${config.dhcpServers} DHCP address assignment server(s)`,
    },
  ]
}