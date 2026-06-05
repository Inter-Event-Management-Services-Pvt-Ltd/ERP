import { cn } from '@/lib/utils'
import { TopBar } from './top-bar'
import { Sidebar } from './sidebar'
import { OfflineBanner } from '@/components/states/offline-banner'

interface AppShellProps {
  children: React.ReactNode
  breadcrumb?: React.ReactNode
  className?: string
  offline?: boolean
}

export function AppShell({ children, breadcrumb, className, offline = false }: AppShellProps) {
  return (
    <div className="flex h-screen overflow-hidden bg-surface-base">
      <Sidebar />

      <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
        <TopBar breadcrumb={breadcrumb} />

        {/* 2px gradient strip — once per shell, never on cards */}
        <div className="gradient-strip" aria-hidden="true" />

        <OfflineBanner visible={offline} />

        <main
          id="main-content"
          className={cn('flex-1 overflow-y-auto', className)}
        >
          {children}
        </main>
      </div>
    </div>
  )
}
