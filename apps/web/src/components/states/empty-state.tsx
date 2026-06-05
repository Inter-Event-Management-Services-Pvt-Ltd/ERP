import { InboxIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface EmptyStateProps {
  heading: string
  body: string
  icon?: React.ElementType
  action?: React.ReactNode
  className?: string
}

export function EmptyState({
  heading,
  body,
  icon: Icon = InboxIcon,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-20 px-6 text-center',
        className
      )}
    >
      <Icon size={40} aria-hidden="true" className="mb-4 text-text-primary/20" />
      <h2 className="font-serif italic text-xl text-text-primary mb-2">{heading}</h2>
      <p className="text-sm text-text-primary/60 max-w-sm leading-relaxed">{body}</p>
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}
