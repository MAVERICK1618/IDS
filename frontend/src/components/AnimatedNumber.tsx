import { useEffect, useRef, useState } from "react"

interface AnimatedNumberProps {
  value: number
  duration?: number
  decimals?: number
  suffix?: string
  className?: string
}

export function AnimatedNumber({ value, duration = 600, decimals = 0, suffix = "", className }: AnimatedNumberProps) {
  const [display, setDisplay] = useState(value)
  const prevValue = useRef(value)
  const frameRef = useRef<number | undefined>(undefined)

  useEffect(() => {
    const start = prevValue.current
    const end = value
    const startTime = performance.now()

    function tick(now: number) {
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      const current = start + (end - start) * eased
      setDisplay(current)
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(tick)
      } else {
        prevValue.current = end
      }
    }

    frameRef.current = requestAnimationFrame(tick)
    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current)
    }
  }, [value, duration])

  return (
    <span className={className}>
      {display.toFixed(decimals)}
      {suffix}
    </span>
  )
}
