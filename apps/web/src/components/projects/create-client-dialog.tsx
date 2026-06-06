'use client'

import { useEffect, useRef } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { X } from 'lucide-react'
import { FormField, inputCls } from '@/components/ui/form-field'
import { useCreateClient } from '@/hooks/use-clients'
import { cn } from '@/lib/utils'

const STOP_WORDS = new Set([
  'private', 'limited', 'pvt', 'ltd', 'llp', 'inc', 'corp',
  'corporation', 'company', 'co', 'and', 'the', 'of', 'for',
])

function deriveClientCode(legalName: string): string {
  const words = legalName
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9\s]/g, '')
    .split(/\s+/)
    .filter((w) => w.length > 0 && !STOP_WORDS.has(w.toLowerCase()))

  if (words.length === 0) return ''
  if (words.length === 1) return words[0].slice(0, 12)
  return words.map((w) => w[0]).join('').slice(0, 12)
}

const schema = z.object({
  client_code: z
    .string()
    .min(1, 'Client code is required')
    .max(20, 'Max 20 characters')
    .regex(/^[A-Z0-9_-]+$/, 'Uppercase letters, numbers, - and _ only'),
  legal_name: z.string().min(1, 'Legal name is required').max(200),
  display_name: z.string().min(1, 'Display name is required').max(100),
  notes: z.string().max(500).optional(),
})

type FormValues = z.infer<typeof schema>

interface CreateClientDialogProps {
  open: boolean
  onClose: () => void
  onCreated?: (clientId: string) => void
}

export function CreateClientDialog({
  open,
  onClose,
  onCreated,
}: CreateClientDialogProps) {
  const { mutate, isPending, error } = useCreateClient()
  const firstRef = useRef<HTMLInputElement>(null)

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    control,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const legalName = useWatch({ control, name: 'legal_name', defaultValue: '' })

  useEffect(() => {
    setValue('client_code', deriveClientCode(legalName), { shouldValidate: false })
  }, [legalName, setValue])

  useEffect(() => {
    if (open) {
      reset()
      setTimeout(() => firstRef.current?.focus(), 50)
    }
  }, [open, reset])

  function onSubmit(values: FormValues) {
    mutate(values, {
      onSuccess: (client) => {
        onCreated?.(client.id)
        onClose()
      },
    })
  }

  if (!open) return null

  const apiError =
    error instanceof Error ? error.message : error ? 'Failed to create client' : null

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-client-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <div
        className="absolute inset-0 bg-surface-deep/80"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="relative w-full max-w-md rounded-xl bg-surface-raised border border-surface-border shadow-2xl animate-in fade-in-0 zoom-in-95 duration-180">
        <div className="gradient-strip" aria-hidden="true" />
        <div className="px-6 py-5">
          <div className="flex items-center justify-between mb-5">
            <h2
              id="create-client-title"
              className="text-sm font-sans font-semibold text-text-primary"
            >
              New Client
            </h2>
            <button
              onClick={onClose}
              aria-label="Close dialog"
              className="text-text-primary/40 hover:text-text-primary/70 transition-colors rounded focus-visible:ring-2 focus-visible:ring-accent-saffron"
            >
              <X size={16} aria-hidden="true" />
            </button>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
            <FormField label="Legal Name" htmlFor="legal_name" required error={errors.legal_name?.message}>
              <input
                {...register('legal_name')}
                id="legal_name"
                ref={(el) => {
                  register('legal_name').ref(el)
                  if (el) (firstRef as React.MutableRefObject<HTMLInputElement>).current = el
                }}
                placeholder="Acme Events Private Limited"
                className={cn(inputCls, errors.legal_name && 'border-accent-critical')}
              />
            </FormField>

            <FormField label="Client Code" htmlFor="client_code" error={errors.client_code?.message}>
              <div className="relative">
                <input
                  {...register('client_code')}
                  id="client_code"
                  readOnly
                  tabIndex={-1}
                  placeholder="—"
                  className={cn(inputCls, 'cursor-default text-text-primary/50 select-none')}
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-mono text-text-primary/30 pointer-events-none select-none">
                  auto
                </span>
              </div>
            </FormField>

            <FormField label="Display Name" htmlFor="display_name" required error={errors.display_name?.message}>
              <input
                {...register('display_name')}
                id="display_name"
                placeholder="Acme Events"
                className={cn(inputCls, errors.display_name && 'border-accent-critical')}
              />
            </FormField>

            <FormField label="Notes" htmlFor="notes" error={errors.notes?.message}>
              <textarea
                {...register('notes')}
                id="notes"
                rows={2}
                placeholder="Optional internal notes"
                className={cn(inputCls, 'resize-none')}
              />
            </FormField>

            {apiError && (
              <p role="alert" className="text-xs text-accent-critical font-sans">
                {apiError}
              </p>
            )}

            <div className="flex justify-end gap-2 pt-1">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-sans text-text-primary/60 hover:text-text-primary transition-colors rounded-md focus-visible:ring-2 focus-visible:ring-accent-saffron"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isPending}
                className="px-4 py-2 text-sm font-sans font-medium bg-accent-saffron text-surface-deep rounded-md hover:bg-accent-warning transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus-visible:ring-2 focus-visible:ring-accent-saffron focus-visible:ring-offset-2 focus-visible:ring-offset-surface-raised"
              >
                {isPending ? 'Creating…' : 'Create Client'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
