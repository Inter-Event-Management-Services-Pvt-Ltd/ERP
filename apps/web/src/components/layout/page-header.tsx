import { cn } from '@/lib/utils'

interface PageHeaderProps {
  title: string
  subtitle?: string
  children?: React.ReactNode
  className?: string
}

export function PageHeader({ title, subtitle, children, className }: PageHeaderProps) {
  return (
    <div
      className={cn(
        'flex items-start justify-between px-6 py-5 border-b border-surface-border flex-none',
        className
      )}
    >
      <div>
        <h1 className="font-serif italic text-2xl text-text-primary leading-tight">
          {title}
        </h1>
        {subtitle && (
          <p className="mt-0.5 font-mono text-xs text-accent-saffron tracking-wide uppercase">
            {subtitle}
          </p>
        )}
      </div>
      {children && (
        <div className="flex items-center gap-2 mt-0.5 flex-none">{children}</div>
      )}
    </div>
  )
}
