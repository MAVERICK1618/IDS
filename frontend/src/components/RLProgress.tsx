import { memo } from "react"
import { AreaChart, Area, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts"
import { type TrainingPoint } from "@/types/rl"
import { EmptyState } from "@/components/EmptyState"
import { AnimatedNumber } from "@/components/AnimatedNumber"
import { Brain } from "lucide-react"

interface RLProgressProps {
  points: TrainingPoint[]
  latest: TrainingPoint | null
}

function RLProgressComponent({ points, latest }: RLProgressProps) {
  if (points.length === 0 || !latest) {
    return (
      <EmptyState
        icon={Brain}
        title="No training data yet"
        description="Reinforcement learning progress will chart here"
      />
    )
  }

  return (
    <div>
      {/* Model status */}
      <div className="mb-4 flex items-center justify-between rounded-lg bg-accent px-3 py-2.5">
        <div className="flex items-center gap-2">
          <Brain className="h-4 w-4 text-primary" />
          <div>
            <p className="text-xs font-semibold">RL MODEL</p>
            <p className="text-[10px] text-muted-foreground">Training</p>
          </div>
        </div>
        <div className="flex gap-4 text-right">
          <div>
            <p className="font-mono text-sm font-semibold">
              <AnimatedNumber value={latest.cycle} decimals={0} />
            </p>
            <p className="text-[10px] text-muted-foreground">Cycle</p>
          </div>
          <div>
            <p className="font-mono text-sm font-semibold text-success">
              +<AnimatedNumber value={latest.reward} decimals={2} />
            </p>
            <p className="text-[10px] text-muted-foreground">Reward</p>
          </div>
        </div>
      </div>

      {/* Reward chart */}
      <p className="mb-1 text-xs font-medium text-muted-foreground">Training Reward</p>
      <ResponsiveContainer width="100%" height={100}>
        <AreaChart data={points} margin={{ top: 4, right: 4, left: 4, bottom: 0 }}>
          <defs>
            <linearGradient id="rewardGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--color-primary)" stopOpacity={0.35} />
              <stop offset="100%" stopColor="var(--color-primary)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="cycle" hide />
          <YAxis domain={[0, 1]} hide />
          <Tooltip
            contentStyle={{ fontSize: 11, borderRadius: 8, border: "1px solid var(--color-border)" }}
            labelFormatter={(v) => `Cycle ${v}`}
          />
          <Area type="monotone" dataKey="reward" stroke="var(--color-primary)" strokeWidth={2} fill="url(#rewardGradient)" />
        </AreaChart>
      </ResponsiveContainer>

      {/* Accuracy chart */}
      <p className="mb-1 mt-3 text-xs font-medium text-muted-foreground">Detection Accuracy</p>
      <ResponsiveContainer width="100%" height={80}>
        <AreaChart data={points} margin={{ top: 4, right: 4, left: 4, bottom: 0 }}>
          <defs>
            <linearGradient id="accuracyGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--color-success)" stopOpacity={0.35} />
              <stop offset="100%" stopColor="var(--color-success)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="cycle" hide />
          <YAxis domain={[0, 1]} hide />
          <Tooltip
            contentStyle={{ fontSize: 11, borderRadius: 8, border: "1px solid var(--color-border)" }}
            labelFormatter={(v) => `Cycle ${v}`}
          />
          <Area type="monotone" dataKey="accuracy" stroke="var(--color-success)" strokeWidth={2} fill="url(#accuracyGradient)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export const RLProgress = memo(RLProgressComponent)
