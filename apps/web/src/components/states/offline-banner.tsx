import { WifiOff } from 'lucide-react'

export function OfflineBanner({ visible }: { visible: boolean }) {
  if (!visible) return null

  return (
    <div
      role="status"
      aria-live="polite"
      className="flex items-center gap-2 px-4 py-2 bg-accent-warning/10 border-b border-accent-warning/30 text-accent-warning text-sm font-sans flex-none"
    >
      <WifiOff size={14} aria-hidden="true" />
      <span>You&apos;re offline. Showing cached data.</span>
    </div>
  )
}
