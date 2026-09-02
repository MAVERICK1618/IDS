import { type ReactNode, useState } from "react"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Menu } from "lucide-react"

interface DashboardLayoutProps {
  sidebar: ReactNode
  header: ReactNode
  children: ReactNode
}

export function DashboardLayout({ sidebar, header, children }: DashboardLayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background text-foreground">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex w-64 shrink-0 flex-col border-r border-border bg-card">
        {sidebar}
      </aside>

      {/* Main area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <header className="relative flex h-16 shrink-0 items-center gap-3 overflow-hidden px-4 md:px-6 bg-gradient-to-r from-primary via-primary to-info">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_60%_100%_at_100%_0%,rgba(255,255,255,0.15),transparent)]" />
          <div className="relative z-10 flex flex-1 items-center gap-3">
            <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
              <SheetTrigger render={<Button size="icon" variant="ghost" className="md:hidden shrink-0 text-white hover:bg-white/10 hover:text-white" />}>
                <Menu className="h-5 w-5" />
              </SheetTrigger>
              <SheetContent side="left" className="w-64 p-0">
                {sidebar}
              </SheetContent>
            </Sheet>
            <div className="flex-1 min-w-0">{header}</div>
          </div>
        </header>

        {/* Scrollable content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 [overflow-anchor:none]">
          {children}
        </main>
      </div>
    </div>
  )
}
