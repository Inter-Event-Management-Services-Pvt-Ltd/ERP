import { cn } from '@/lib/utils'

interface ContentAreaProps {
  children: React.ReactNode
  className?: string
}

export function ContentArea({ children, className }: ContentAreaProps) {
  return (
    <div className={cn('px-6 py-5 max-w-7xl mx-auto w-full', className)}>
      {children}
    </div>
  )
}
