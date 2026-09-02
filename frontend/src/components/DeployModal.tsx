import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Minus, Plus, Server, Monitor, Globe2, Wifi, Loader2 } from "lucide-react"
import { type NetworkConfig } from "@/types/network"
import { toast } from "sonner"

interface DeployModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onDeploy: (config: NetworkConfig) => void
  deploying: boolean
}

const fields: { key: keyof NetworkConfig; label: string; description: string; icon: typeof Server; min: number; max: number }[] = [
  { key: "dmzServers", label: "DMZ Servers", description: "Number of DMZ servers (web, mail, DNS, etc.)", icon: Server, min: 0, max: 10 },
  { key: "internalHosts", label: "Internal Hosts", description: "Number of internal blue-team client hosts", icon: Monitor, min: 1, max: 50 },
  { key: "dnsServers", label: "DNS Servers", description: "Number of DNS resolution servers in DMZ", icon: Globe2, min: 0, max: 5 },
  { key: "dhcpServers", label: "DHCP Servers", description: "Number of DHCP address assignment servers in DMZ", icon: Wifi, min: 0, max: 5 },
]

export function DeployModal({ open, onOpenChange, onDeploy, deploying }: DeployModalProps) {
  const [config, setConfig] = useState<NetworkConfig>({
    dmzServers: 1,
    internalHosts: 10,
    dnsServers: 1,
    dhcpServers: 1,
  })

  const update = (key: keyof NetworkConfig, delta: number, min: number, max: number) => {
    setConfig((prev) => ({
      ...prev,
      [key]: Math.min(max, Math.max(min, prev[key] + delta)),
    }))
  }

  const totalNodes = config.dmzServers + config.internalHosts + config.dnsServers + config.dhcpServers

  const handleDeploy = () => {
    if (totalNodes === 0) {
      toast.error("Invalid configuration", { description: "At least one node is required to deploy." })
      return
    }
    onDeploy(config)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Network Configuration</DialogTitle>
          <DialogDescription>Set the topology before deploying the emulated network.</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {fields.map((field) => {
            const Icon = field.icon
            return (
              <div key={field.key} className="flex items-center justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 rounded-md bg-accent p-1.5">
                    <Icon className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{field.label}</p>
                    <p className="text-xs text-muted-foreground max-w-[220px]">{field.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    size="icon"
                    variant="outline"
                    className="h-7 w-7"
                    disabled={config[field.key] <= field.min}
                    onClick={() => update(field.key, -1, field.min, field.max)}
                  >
                    <Minus className="h-3 w-3" />
                  </Button>
                  <span className="w-6 text-center font-mono text-sm font-semibold">{config[field.key]}</span>
                  <Button
                    type="button"
                    size="icon"
                    variant="outline"
                    className="h-7 w-7"
                    disabled={config[field.key] >= field.max}
                    onClick={() => update(field.key, 1, field.min, field.max)}
                  >
                    <Plus className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            )
          })}
        </div>

        <div className="rounded-lg bg-muted p-3">
          <p className="text-xs font-medium text-muted-foreground mb-2">TOPOLOGY SUMMARY</p>
          <div className="grid grid-cols-5 gap-2 text-center">
            <div>
              <p className="font-mono text-sm font-semibold">{config.dmzServers}</p>
              <p className="text-[10px] text-muted-foreground">DMZ</p>
            </div>
            <div>
              <p className="font-mono text-sm font-semibold">{config.internalHosts}</p>
              <p className="text-[10px] text-muted-foreground">Hosts</p>
            </div>
            <div>
              <p className="font-mono text-sm font-semibold">{config.dnsServers}</p>
              <p className="text-[10px] text-muted-foreground">DNS</p>
            </div>
            <div>
              <p className="font-mono text-sm font-semibold">{config.dhcpServers}</p>
              <p className="text-[10px] text-muted-foreground">DHCP</p>
            </div>
            <div>
              <p className="font-mono text-sm font-semibold text-primary">{totalNodes}</p>
              <p className="text-[10px] text-muted-foreground">Total</p>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={deploying}>
            Cancel
          </Button>
          <Button onClick={handleDeploy} disabled={deploying} className="gap-1.5">
            {deploying && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Deploy Network
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}