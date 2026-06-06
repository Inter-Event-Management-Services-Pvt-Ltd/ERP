'use client'

import { useEffect, useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { X } from 'lucide-react'
import { FormField, inputCls } from '@/components/ui/form-field'
import { useCreateProject } from '@/hooks/use-projects'
import { useClients } from '@/hooks/use-clients'
import { cn } from '@/lib/utils'

const STOP_WORDS = new Set([
  'a', 'an', 'the', 'and', 'or', 'of', 'for', 'in', 'on', 'at', 'to',
  'with', 'by', 'from', 'annual', 'quarterly', 'monthly',
])

function deriveProjectCode(name: string, eventDate: string): string {
  const words = name
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9\s]/g, '')
    .split(/\s+/)
    .filter((w) => w.length > 0 && !STOP_WORDS.has(w.toLowerCase()))

  const acronym = words.length === 0
    ? ''
    : words.length === 1
    ? words[0].slice(0, 8)
    : words.map((w) => w[0]).join('').slice(0, 8)

  const year = eventDate ? new Date(eventDate).getFullYear() : new Date().getFullYear()
  return acronym ? `${acronym}-${year}` : ''
}

const schema = z.object({
  project_code: z
    .string()
    .min(1, 'Project code is required')
    .max(40, 'Max 40 characters')
    .regex(/^[A-Z0-9_-]+$/, 'Uppercase letters, numbers, - and _ only'),
  name: z.string().min(1, 'Project name is required').max(200),
  client_id: z.string().min(1, 'Client is required'),
  event_date: z.string().min(1, 'Event date is required'),
  venue: z.string().min(1, 'Venue is required').max(200),
  description: z.string().max(1000).optional(),
  project_type_id: z.string().min(1, 'Project type is required'),
  project_status_id: z.string().min(1, 'Status is required'),
  priority_level_id: z.string().min(1, 'Priority is required'),
})

type FormValues = z.infer<typeof schema>

interface CreateProjectDialogProps {
  open: boolean
  onClose: () => void
  onCreated?: (projectId: string) => void
  /** Lookup IDs for project type / status / priority — from GET /v1/project-types etc.
   *  Until those endpoints exist, pass static seed values. See OPEN-016. */
  lookups: {
    projectTypes: Array<{ id: string; name: string }>
    projectStatuses: Array<{ id: string; name: string }>
    priorityLevels: Array<{ id: string; name: string }>
  }
}

export function CreateProjectDialog({
  open,
  onClose,
  onCreated,
  lookups,
}: CreateProjectDialogProps) {
  const { mutate, isPending, error } = useCreateProject()
  const { data: clients = [] } = useClients()
  const [codeTouched, setCodeTouched] = useState(false)

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    control,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const projectName = useWatch({ control, name: 'name', defaultValue: '' })
  const eventDate = useWatch({ control, name: 'event_date', defaultValue: '' })

  useEffect(() => {
    if (!codeTouched) {
      setValue('project_code', deriveProjectCode(projectName, eventDate), { shouldValidate: false })
    }
  }, [projectName, eventDate, codeTouched, setValue])

  useEffect(() => {
    if (open) {
      reset()
      setCodeTouched(false)
    }
  }, [open, reset])

  function onSubmit(values: FormValues) {
    mutate(
      {
        project_code: values.project_code,
        name: values.name,
        client_id: values.client_id,
        event_date: values.event_date,
        venue: values.venue,
        description: values.description,
        project_type_id: values.project_type_id,
        project_status_id: values.project_status_id,
        priority_level_id: values.priority_level_id,
      },
      {
        onSuccess: (project) => {
          onCreated?.(project.id)
          onClose()
        },
      }
    )
  }

  if (!open) return null

  const apiError =
    error instanceof Error ? error.message : error ? 'Failed to create project' : null

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-project-title"
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
              id="create-project-title"
              className="text-sm font-sans font-semibold text-text-primary"
            >
              New Project
            </h2>
            <button
              onClick={onClose}
              aria-label="Close dialog"
              className="text-text-primary/40 hover:text-text-primary/70 transition-colors rounded focus-visible:ring-2 focus-visible:ring-accent-saffron"
            >
              <X size={16} aria-hidden="true" />
            </button>
          </div>
        </div>

        <form
          onSubmit={handleSubmit(onSubmit)}
          noValidate
          className="overflow-y-auto flex-1 px-6 pb-6 space-y-4"
        >
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Project Name" htmlFor="name" required error={errors.name?.message}>
              <input
                {...register('name')}
                id="name"
                placeholder="Annual Leadership Conference"
                autoFocus
                className={cn(inputCls, errors.name && 'border-accent-critical')}
              />
            </FormField>

            <FormField label="Project Code" htmlFor="project_code" required error={errors.project_code?.message}>
              <div className="relative">
                <input
                  {...register('project_code')}
                  id="project_code"
                  placeholder="Auto-generated"
                  onChange={(e) => {
                    register('project_code').onChange(e)
                    setCodeTouched(true)
                  }}
                  className={cn(inputCls, errors.project_code && 'border-accent-critical', !codeTouched && 'text-text-primary/60')}
                />
                {!codeTouched && (
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-mono text-text-primary/30 pointer-events-none select-none">
                    auto
                  </span>
                )}
              </div>
            </FormField>
          </div>

          <FormField label="Client" htmlFor="client_id" required error={errors.client_id?.message}>
            <select
              {...register('client_id')}
              id="client_id"
              className={cn(inputCls, errors.client_id && 'border-accent-critical')}
            >
              <option value="">Select client…</option>
              {clients.filter((c) => c.is_active).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.display_name} ({c.client_code})
                </option>
              ))}
            </select>
          </FormField>

          <div className="grid grid-cols-2 gap-4">
            <FormField label="Project Type" htmlFor="project_type_id" required error={errors.project_type_id?.message}>
              <select
                {...register('project_type_id')}
                id="project_type_id"
                className={cn(inputCls, errors.project_type_id && 'border-accent-critical')}
              >
                <option value="">Select…</option>
                {lookups.projectTypes.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </FormField>

            <FormField label="Status" htmlFor="project_status_id" required error={errors.project_status_id?.message}>
              <select
                {...register('project_status_id')}
                id="project_status_id"
                className={cn(inputCls, errors.project_status_id && 'border-accent-critical')}
              >
                <option value="">Select…</option>
                {lookups.projectStatuses.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </FormField>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <FormField label="Priority" htmlFor="priority_level_id" required error={errors.priority_level_id?.message}>
              <select
                {...register('priority_level_id')}
                id="priority_level_id"
                className={cn(inputCls, errors.priority_level_id && 'border-accent-critical')}
              >
                <option value="">Select…</option>
                {lookups.priorityLevels.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </FormField>

            <FormField label="Event Date" htmlFor="event_date" required error={errors.event_date?.message}>
              <input
                {...register('event_date')}
                id="event_date"
                type="date"
                className={cn(inputCls, errors.event_date && 'border-accent-critical')}
              />
            </FormField>
          </div>

          <FormField label="Venue" htmlFor="venue" required error={errors.venue?.message}>
            <input
              {...register('venue')}
              id="venue"
              placeholder="New Delhi"
              className={cn(inputCls, errors.venue && 'border-accent-critical')}
            />
          </FormField>

          <FormField label="Description" htmlFor="description" error={errors.description?.message}>
            <textarea
              {...register('description')}
              id="description"
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
              {isPending ? 'Creating…' : 'Create Project'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
