'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2, X } from 'lucide-react'
import { FormField, inputCls } from '@/components/ui/form-field'
import { usePriorityLevels } from '@/hooks/use-lookups'
import { useProjects } from '@/hooks/use-projects'
import { useCreateTask } from '@/hooks/use-tasks'
import { useEmployeeSearch } from '@/hooks/use-employees'
import { apiErrorMessage } from '@/lib/errors'
import type { EmployeeSummary } from '@/types'

interface CreateTaskDialogProps {
  open: boolean
  onClose: () => void
}

export function CreateTaskDialog({ open, onClose }: CreateTaskDialogProps) {
  const router = useRouter()
  const { data: priorityLevels = [] } = usePriorityLevels()
  const { data: projects = [] } = useProjects()
  const { mutate, isPending } = useCreateTask()
  const cancelRef = useRef<HTMLButtonElement>(null)

  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [projectId, setProjectId] = useState('')
  const [priorityLevelId, setPriorityLevelId] = useState('')
  const [dueAt, setDueAt] = useState('')
  const [assignees, setAssignees] = useState<EmployeeSummary[]>([])
  const [assigneeSearch, setAssigneeSearch] = useState('')
  const { data: assigneeMatches = [] } = useEmployeeSearch(assigneeSearch)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setTitle('')
      setDescription('')
      setProjectId('')
      setPriorityLevelId('')
      setDueAt('')
      setAssignees([])
      setAssigneeSearch('')
      setError(null)
      cancelRef.current?.focus()
    }
  }, [open])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  function addAssignee(emp: EmployeeSummary) {
    if (!assignees.some((a) => a.id === emp.id)) {
      setAssignees((prev) => [...prev, emp])
    }
    setAssigneeSearch('')
  }

  function removeAssignee(id: string) {
    setAssignees((prev) => prev.filter((a) => a.id !== id))
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!title.trim() || !priorityLevelId) {
      setError('Title and priority are required.')
      return
    }
    setError(null)
    mutate(
      {
        title: title.trim(),
        description: description.trim() || undefined,
        project_id: projectId || undefined,
        priority_level_id: priorityLevelId,
        due_at: dueAt ? new Date(dueAt).toISOString() : undefined,
        assignee_ids: assignees.map((a) => a.id),
      },
      {
        onSuccess: (task) => {
          onClose()
          router.push(`/tasks/${task.id}`)
        },
        onError: (err) => setError(apiErrorMessage(err)),
      }
    )
  }

  return (
    <div role="dialog" aria-modal="true" aria-labelledby="task-dialog-title" className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} aria-hidden="true" />
      <form
        onSubmit={handleSubmit}
        className="relative bg-surface-raised border border-surface-border rounded-lg p-6 max-w-lg w-full mx-4 animate-scale-in space-y-4 max-h-[90vh] overflow-y-auto"
      >
        <h2 id="task-dialog-title" className="font-serif italic text-lg text-text-primary">
          New Task
        </h2>

        <FormField label="Title" htmlFor="task-title" required>
          <input
            id="task-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            aria-required="true"
            className={inputCls}
          />
        </FormField>

        <FormField label="Description" htmlFor="task-description">
          <textarea
            id="task-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className={inputCls}
          />
        </FormField>

        <div className="grid grid-cols-2 gap-3">
          <FormField label="Project" htmlFor="task-project">
            <select
              id="task-project"
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              className={inputCls}
            >
              <option value="">None</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </FormField>

          <FormField label="Priority" htmlFor="task-priority" required>
            <select
              id="task-priority"
              value={priorityLevelId}
              onChange={(e) => setPriorityLevelId(e.target.value)}
              required
              aria-required="true"
              className={inputCls}
            >
              <option value="">Select…</option>
              {priorityLevels.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </FormField>
        </div>

        <FormField label="Due date" htmlFor="task-due">
          <input
            id="task-due"
            type="datetime-local"
            value={dueAt}
            onChange={(e) => setDueAt(e.target.value)}
            className={inputCls}
          />
        </FormField>

        <FormField label="Assignees" htmlFor="task-assignee-search">
          <input
            id="task-assignee-search"
            type="text"
            value={assigneeSearch}
            onChange={(e) => setAssigneeSearch(e.target.value)}
            placeholder="Search employees…"
            className={inputCls}
          />
          {assigneeSearch.trim().length >= 2 && assigneeMatches.length > 0 && (
            <ul className="mt-1 rounded-md border border-surface-border bg-surface-base max-h-32 overflow-y-auto text-sm font-sans">
              {assigneeMatches.map((emp) => (
                <li key={emp.id}>
                  <button
                    type="button"
                    onClick={() => addAssignee(emp)}
                    className="w-full text-left px-3 py-1.5 hover:bg-surface-raised transition-colors"
                  >
                    {emp.full_name}{' '}
                    <span className="text-text-primary/40 font-mono text-xs">{emp.employee_code}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
          {assignees.length > 0 && (
            <ul className="mt-2 flex flex-wrap gap-1.5">
              {assignees.map((a) => (
                <li
                  key={a.id}
                  className="flex items-center gap-1 rounded-full bg-surface-base border border-surface-border px-2 py-0.5 text-xs font-sans text-text-primary/80"
                >
                  {a.full_name}
                  <button
                    type="button"
                    onClick={() => removeAssignee(a.id)}
                    aria-label={`Remove ${a.full_name}`}
                    className="text-text-primary/40 hover:text-accent-critical transition-colors"
                  >
                    <X size={12} aria-hidden="true" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </FormField>

        {error && <p role="alert" className="text-xs font-sans text-accent-critical">{error}</p>}

        <div className="flex gap-3 justify-end">
          <button
            ref={cancelRef}
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-sans rounded-md border border-surface-border text-text-primary/70 hover:text-text-primary hover:bg-surface-base transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isPending}
            className="flex items-center gap-1.5 px-4 py-2 text-sm font-sans font-medium rounded-md bg-accent-saffron text-surface-deep hover:bg-accent-warning disabled:opacity-40 transition-colors"
          >
            {isPending && <Loader2 size={14} className="animate-spin" aria-hidden="true" />}
            Create Task
          </button>
        </div>
      </form>
    </div>
  )
}
