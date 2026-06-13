import { cn } from '@/lib/utils'

interface FormFieldProps {
  label: string
  htmlFor: string
  error?: string
  required?: boolean
  className?: string
  children: React.ReactNode
}

export function FormField({
  label,
  htmlFor,
  error,
  required,
  className,
  children,
}: FormFieldProps) {
  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      <label
        htmlFor={htmlFor}
        className="text-xs font-sans text-text-primary/70 font-medium"
      >
        {label}
        {required && (
          <span className="ml-0.5 text-accent-critical" aria-hidden="true">
            *
          </span>
        )}
      </label>
      {children}
      {error && (
        <p role="alert" className="text-xs text-accent-critical font-sans">
          {error}
        </p>
      )}
    </div>
  )
}

export const inputCls = cn(
  'w-full rounded-md border border-surface-border bg-surface-base px-3 py-2',
  'text-sm font-sans text-text-primary placeholder:text-text-primary/30',
  'focus:outline-none focus:ring-2 focus:ring-accent-saffron focus:ring-offset-1 focus:ring-offset-surface-raised',
  'disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-100'
)
