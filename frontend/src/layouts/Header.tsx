import { Cpu, Network, Sparkles, Radio } from "lucide-react"

const tags = [
  { icon: Cpu, label: "Neuromorphic IPS" },
  { icon: Network, label: "Agent Orchestration" },
  { icon: Sparkles, label: "Swarm Intelligence" },
]

export function Header() {
  return (
    <div className="flex w-full items-center justify-between gap-4">
      <div className="min-w-0">
        <h1 className="truncate text-base md:text-xl font-bold tracking-tight text-white">
          Dashboard Overview
        </h1>
        <div className="mt-1 hidden sm:flex items-center gap-3">
          {tags.map((tag, i) => (
            <span key={tag.label} className="flex items-center gap-3">
              <span className="flex items-center gap-1.5 text-[11px] font-medium text-white/70">
                <tag.icon className="h-3 w-3 text-white/60" />
                {tag.label}
              </span>
              {i < tags.length - 1 && <span className="h-3 w-px bg-white/20" />}
            </span>
          ))}
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-2 rounded-full border border-white/25 bg-white/10 py-1.5 pl-2.5 pr-3.5 backdrop-blur-sm">
        <span className="relative flex h-2.5 w-2.5 items-center justify-center">
          <span className="absolute h-full w-full animate-ping rounded-full bg-emerald-300 opacity-75" />
          <Radio className="relative h-2.5 w-2.5 text-emerald-300" strokeWidth={3} />
        </span>
        <span className="hidden text-xs font-semibold text-white sm:inline">System Active</span>
      </div>
    </div>
  )
}
