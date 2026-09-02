import { Network, Activity, MessageSquare, ShieldAlert, Brain, BarChart3, Images } from "lucide-react"
import { Logo } from "@/components/Logo"

const navItems = [
  { icon: Network, label: "Topology", id: "topology" },
  { icon: Activity, label: "Live Packets", id: "packets" },
  { icon: MessageSquare, label: "Agent Feed", id: "agents" },
  { icon: ShieldAlert, label: "Attacks", id: "attacks" },
  { icon: Brain, label: "RL Progress", id: "rl-progress" },
  { icon: BarChart3, label: "Metrics", id: "metrics" },
  { icon: Images, label: "Results", id: "results" },
]

export function Sidebar() {
  const handleNavClick = (id: string) => {
    const el = document.getElementById(id)
    el?.scrollIntoView({ behavior: "smooth", block: "start" })
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2.5 px-6 py-5">
        <Logo className="h-7 w-7 shrink-0" />
        <div>
          <span className="block bg-gradient-to-r from-primary to-info bg-clip-text text-lg font-bold leading-tight text-transparent">
            Adaptive IDS
          </span>
          <span className="block text-[10px] font-medium tracking-wide text-muted-foreground">
            SOC DASHBOARD
          </span>
        </div>
      </div>
      <nav className="flex-1 space-y-1 px-3">
        {navItems.map((item) => (
          <button
            key={item.label}
            onClick={() => handleNavClick(item.id)}
            className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </button>
        ))}
      </nav>
    </div>
  )
}
