interface LogoProps {
  className?: string
}

export function Logo({ className }: LogoProps) {
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <path
        d="M16 2L27 6.5V15C27 22.5 21.5 27.5 16 30C10.5 27.5 5 22.5 5 15V6.5L16 2Z"
        fill="url(#logoGradient)"
        fillOpacity="0.15"
        stroke="url(#logoGradient)"
        strokeWidth="1.6"
      />
      <circle cx="16" cy="13" r="2.1" fill="url(#logoGradient)" />
      <circle cx="11" cy="19" r="1.5" fill="url(#logoGradient)" fillOpacity="0.85" />
      <circle cx="21" cy="19" r="1.5" fill="url(#logoGradient)" fillOpacity="0.85" />
      <path d="M16 15V17.5M16 17.5L11.5 19M16 17.5L20.5 19" stroke="url(#logoGradient)" strokeWidth="1.3" strokeLinecap="round" />
      <defs>
        <linearGradient id="logoGradient" x1="5" y1="2" x2="27" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="var(--color-primary)" />
          <stop offset="1" stopColor="var(--color-info)" />
        </linearGradient>
      </defs>
    </svg>
  )
}
