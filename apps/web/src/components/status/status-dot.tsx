import { cn } from '@/lib/utils'

type DotColor = 'green' | 'yellow' | 'red' | 'grey'

const dotColors: Record<DotColor, string> = {
  green:  'bg-green-400',
  yellow: 'bg-accent-warning',
  red:    'bg-accent-critical',
  grey:   'bg-text-primary/30',
}

interface StatusDotProps {
  color: DotColor
  label: string
  className?: string
}

export function StatusDot({ color, label, className }: StatusDotProps) {
  return (
    <span className={cn('flex items-center gap-1.5', className)}>
      <span
        aria-hidden="true"
        className={cn('w-1.5 h-1.5 rounded-full flex-none', dotColors[color])}
      />
      <span className="text-xs font-sans text-text-primary/70">{label}</span>
    </span>
  )
}
