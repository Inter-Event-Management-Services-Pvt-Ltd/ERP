import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center font-mono text-[10px] tracking-widest uppercase px-2 py-0.5 rounded-sm',
  {
    variants: {
      variant: {
        active:   'bg-accent-saffron/15 text-accent-saffron',
        pending:  'bg-surface-raised text-text-primary/60',
        overdue:  'bg-accent-warning/15 text-accent-warning',
        approved: 'bg-accent-saffron/15 text-accent-saffron',
        rejected: 'bg-accent-madder/25 text-accent-critical',
        archived: 'bg-surface-raised text-text-primary/40',
        info:     'bg-surface-raised text-text-primary/60',
        warning:  'bg-accent-warning/15 text-accent-warning',
        critical: 'bg-accent-madder/30 text-accent-critical',
      },
    },
    defaultVariants: { variant: 'info' },
  }
)

interface BadgeProps extends VariantProps<typeof badgeVariants> {
  children: React.ReactNode
  className?: string
}

export function Badge({ variant, children, className }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)}>
      {children}
    </span>
  )
}
