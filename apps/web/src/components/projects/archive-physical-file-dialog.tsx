'use client'

import { useEffect } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { X } from 'lucide-react'
import { FormField, inputCls } from '@/components/ui/form-field'
import { FileSlotPicker } from '@/components/archive/file-slot-picker'
import { useCreatePhysicalFile } from '@/hooks/use-physical-archive'
import { apiErrorMessage } from '@/lib/errors'
import { cn } from '@/lib/utils'
import type { PhysicalFile } from '@/types'

const schema = z.object({
  physical_file_code: z.string().min(1, 'File code is required').max(60),
  archive_location_id: z.string().min(1, 'Select a file slot to archive into'),
  volume_number: z.coerce.number().int('Must be a whole number').min(1, 'Must be at least 1'),
  archived_on: z.string().optional(),
  notes: z.string().max(2000).optional(),
})

type FormValues = z.infer<typeof schema>

interface ArchivePhysicalFileDialogProps {
  open: boolean
  projectId: string
  onClose: () => void
  onCreated?: (file: PhysicalFile) => void
}

export function ArchivePhysicalFileDialog({
  open,
  projectId,
  onClose,
  onCreated,
}: ArchivePhysicalFileDialogProps) {
  const { mutate, isPending, error, reset: resetMutation } = useCreatePhysicalFile(projectId)

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    control,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { volume_number: 1, archive_location_id: '' },
  })

  const locationId = useWatch({ control, name: 'archive_location_id' })

  useEffect(() => {
    if (open) {
      reset({ volume_number: 1, archive_location_id: '' })
      resetMutation()
    }
  }, [open, reset, resetMutation])

  function onSubmit(values: FormValues) {
    mutate(
      {
        physical_file_code: values.physical_file_code.trim(),
        archive_location_id: values.archive_location_id,
        volume_number: values.volume_number,
        archived_on: values.archived_on || undefined,
        notes: values.notes?.trim() || undefined,
      },
      {
        onSuccess: (file) => {
          onCreated?.(file)
          onClose()
        },
      }
    )
  }

  if (!open) return null

  const apiError = error ? apiErrorMessage(error) : null

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="archive-physical-file-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <div
        className="absolute inset-0 bg-surface-deep/80"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="relative w-full max-w-lg rounded-xl bg-surface-raised border border-surface-border shadow-2xl animate-in fade-in-0 zoom-in-95 duration-180 max-h-[90vh] flex flex-col">
        <div className="gradient-strip flex-none" aria-hidden="true" />
        <div className="px-6 pt-5 pb-2 flex-none">
          <div className="flex items-center justify-between">
            <h2
              id="archive-physical-file-title"
              className="text-sm font-sans font-semibold text-text-primary"
            >
              Archive Physical File
            </h2>
            <button
              onClick={onClose}
              aria-label="Close dialog"
              className="text-text-primary/40 hover:text-text-primary/70 transition-colors rounded focus-visible:ring-2 focus-visible:ring-accent-saffron"
            >
              <X size={16} aria-hidden="true" />
            </button>
          </div>
          <p className="text-xs font-sans text-text-primary/40 mt-1">
            Register a physical (hard copy) file for this project in the archive.
          </p>
        </div>

        <form
          onSubmit={handleSubmit(onSubmit)}
          noValidate
          className="overflow-y-auto flex-1 px-6 pb-6 space-y-4"
        >
          <FormField label="File Code" htmlFor="physical_file_code" required error={errors.physical_file_code?.message}>
            <input
              {...register('physical_file_code')}
              id="physical_file_code"
              placeholder="PF-2026-001"
              autoFocus
              className={cn(inputCls, 'font-mono', errors.physical_file_code && 'border-accent-critical')}
            />
          </FormField>

          <FormField
            label="Archive Location"
            htmlFor="archive_location_id"
            required
            error={errors.archive_location_id?.message}
          >
            <FileSlotPicker
              value={locationId || null}
              onChange={(id) => setValue('archive_location_id', id ?? '', { shouldValidate: true })}
            />
            <p className="text-xs font-sans text-text-primary/30">
              Only active file-slot locations can be selected. Build out racks, shelves, cabinets and
              boxes from the Archive → Rooms screens first.
            </p>
          </FormField>

          <div className="grid grid-cols-2 gap-4">
            <FormField label="Volume Number" htmlFor="volume_number" required error={errors.volume_number?.message}>
              <input
                {...register('volume_number')}
                id="volume_number"
                type="number"
                min={1}
                step={1}
                className={cn(inputCls, 'font-mono', errors.volume_number && 'border-accent-critical')}
              />
            </FormField>

            <FormField label="Archived On" htmlFor="archived_on" error={errors.archived_on?.message}>
              <input
                {...register('archived_on')}
                id="archived_on"
                type="date"
                className={cn(inputCls, 'font-mono')}
              />
            </FormField>
          </div>

          <FormField label="Notes" htmlFor="notes" error={errors.notes?.message}>
            <textarea
              {...register('notes')}
              id="notes"
              rows={2}
              placeholder="Optional"
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
              {isPending ? 'Archiving…' : 'Archive File'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
