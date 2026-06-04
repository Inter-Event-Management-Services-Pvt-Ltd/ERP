import { cn } from '@/lib/utils'

export function LoadingSpinner({ className }: { className?: string }) {
  return (
    <div role="status" aria-label="Loading" className={cn('inline-block', className)}>
      <div className="h-4 w-4 animate-spin rounded-full border-2 border-text-primary/20 border-t-accent-saffron" />
      <span className="sr-only">Loading…</span>
    </div>
  )
}
