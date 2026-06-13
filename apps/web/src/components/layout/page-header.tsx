import { cn } from '@/lib/utils'

interface PageHeaderProps {
  title: string
  subtitle?: React.ReactNode
  /** Right-side action buttons */
  actions?: React.ReactNode
  children?: React.ReactNode
  className?: string
}

export function PageHeader({ title, subtitle, actions, children, className }: PageHeaderProps) {
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
          <div className="mt-0.5">
            {typeof subtitle === 'string' ? (
              <p className="font-mono text-xs text-accent-saffron tracking-wide uppercase">
                {subtitle}
              </p>
            ) : (
              subtitle
            )}
          </div>
        )}
      </div>
      {(actions || children) && (
        <div className="flex items-center gap-2 mt-0.5 flex-none">
          {actions}
          {children}
        </div>
      )}
    </div>
  )
}
