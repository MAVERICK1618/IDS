import { useState, useCallback } from "react"
import { DashboardLayout } from "@/layouts/DashboardLayout"
import { Sidebar } from "@/layouts/Sidebar"
import { Header } from "@/layouts/Header"
import { Card } from "@/components/ui/card"
import { SectionHeader } from "@/components/SectionHeader"
import { EmptyState } from "@/components/EmptyState"
import { ControlBar } from "@/components/ControlBar"
import { TopologyView } from "@/components/TopologyView"
import { DeployModal } from "@/components/DeployModal"
import { ResultsGallery } from "@/components/ResultsGallery"
import { PacketMonitorPanel } from "@/components/panels/PacketMonitorPanel"
import { AgentFeedPanel } from "@/components/panels/AgentFeedPanel"
import { AttackTimelinePanel } from "@/components/panels/AttackTimelinePanel"
import { RLProgressPanel } from "@/components/panels/RLProgressPanel"
import { MetricsPanelWrapper } from "@/components/panels/MetricsPanelWrapper"
import { generateMockResults } from "@/data/mockResults"
import { useSystemStatus } from "@/hooks/useSystemStatus"
import { type NetworkConfig } from "@/types/network"
import { Network, Images } from "lucide-react"
import { toast } from "sonner"

function App() {
  const { state, start, stop, clean, cancel, deployStart, deployFinish } = useSystemStatus()
  const [modalOpen, setModalOpen] = useState(false)
  const [networkConfig, setNetworkConfig] = useState<NetworkConfig | null>(null)
  const [results] = useState(() => generateMockResults())

  const running = state === "running"

  const handleDeploy = useCallback(
    (config: NetworkConfig) => {
      deployStart()
      setTimeout(() => {
        setNetworkConfig(config)
        deployFinish()
        setModalOpen(false)
        toast.success("Network deployed", {
          description: `${config.dmzServers + config.internalHosts + config.dnsServers + config.dhcpServers} nodes online.`,
        })
      }, 2000)
    },
    [deployStart, deployFinish]
  )

  const handleClean = useCallback(() => {
    clean()
    setNetworkConfig(null)
  }, [clean])

  const handleDeployClick = useCallback(() => setModalOpen(true), [])

  return (
    <DashboardLayout sidebar={<Sidebar />} header={<Header />}>
      <div className="space-y-4">
        <div id="control-bar" className="animate-fade-in-up" style={{ animationDelay: "0ms" }}>
          <ControlBar
            state={state}
            onStart={start}
            onStop={stop}
            onClean={handleClean}
            onDeployClick={handleDeployClick}
            onCancel={cancel}
          />
        </div>

        <div id="topology" className="animate-fade-in-up" style={{ animationDelay: "80ms" }}>
          <Card className="p-4">
            <SectionHeader title="Network Topology" description="Emulated network layout" icon={Network} />
            {networkConfig ? (
              <TopologyView config={networkConfig} loading={state === "deploying"} />
            ) : (
              <EmptyState
                icon={Network}
                title="No network deployed"
                description="Deploy a network to see the topology visualization"
              />
            )}
          </Card>
        </div>

        <div id="packets" className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-stretch animate-fade-in-up" style={{ animationDelay: "160ms" }}>
          <PacketMonitorPanel active={running} />
          <div id="agents" className="h-full">
            <AgentFeedPanel active={running} />
          </div>
        </div>

        <div id="attacks" className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-stretch animate-fade-in-up" style={{ animationDelay: "240ms" }}>
          <AttackTimelinePanel active={running} />
          <div id="rl-progress" className="h-full">
            <RLProgressPanel active={running} />
          </div>
        </div>

        <div id="metrics" className="animate-fade-in-up" style={{ animationDelay: "320ms" }}>
          <MetricsPanelWrapper active={running} />
        </div>

        <div id="results" className="animate-fade-in-up" style={{ animationDelay: "400ms" }}>
          <Card className="p-4">
            <SectionHeader title="Results Gallery" description="Evaluation charts" icon={Images} />
            <ResultsGallery results={running ? results : []} />
          </Card>
        </div>
      </div>

      <DeployModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        onDeploy={handleDeploy}
        deploying={state === "deploying"}
      />
    </DashboardLayout>
  )
}

export default App
