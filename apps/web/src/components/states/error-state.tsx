import { AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ErrorStateProps {
  message: string
  onRetry?: () => void
  className?: string
}

export function ErrorState({ message, onRetry, className }: ErrorStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-20 px-6 text-center',
        className
      )}
    >
      <AlertTriangle size={40} aria-hidden="true" className="mb-4 text-accent-critical" />
      <h2 className="font-serif italic text-xl text-text-primary mb-2">
        Something went wrong
      </h2>
      <p className="text-sm text-text-primary/60 max-w-sm leading-relaxed">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-6 px-4 py-2 text-sm font-sans rounded-md bg-accent-madder text-text-primary hover:bg-accent-madder/80 transition-colors"
        >
          Retry
        </button>
      )}
    </div>
  )
}
