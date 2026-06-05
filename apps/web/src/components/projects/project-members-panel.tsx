'use client'

import { useState } from 'react'
import { UserPlus, Trash2 } from 'lucide-react'
import { useAddProjectMember, useRemoveProjectMember } from '@/hooks/use-projects'
import { FormField, inputCls } from '@/components/ui/form-field'
import { cn } from '@/lib/utils'
import type { ProjectMember } from '@/types'

interface AddMemberFormProps {
  projectId: string
  onDone: () => void
}

function AddMemberForm({ projectId, onDone }: AddMemberFormProps) {
  const [employeeId, setEmployeeId] = useState('')
  const [role, setRole] = useState<'VIEW' | 'MANAGE'>('VIEW')
  const { mutate, isPending, error } = useAddProjectMember(projectId)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!employeeId.trim()) return
    mutate(
      { employee_id: employeeId.trim(), role },
      { onSuccess: onDone }
    )
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-3 border-t border-surface-border pt-3 mt-3">
      <p className="text-xs text-text-primary/50 font-sans">Add a team member</p>
      <div className="grid grid-cols-2 gap-3">
        <FormField label="Employee ID" htmlFor="emp-id">
          <input
            id="emp-id"
            value={employeeId}
            onChange={(e) => setEmployeeId(e.target.value)}
            placeholder="22222222-…"
            className={inputCls}
          />
        </FormField>
        <FormField label="Access" htmlFor="member-role">
          <select
            id="member-role"
            value={role}
            onChange={(e) => setRole(e.target.value as 'VIEW' | 'MANAGE')}
            className={inputCls}
          >
            <option value="VIEW">View</option>
            <option value="MANAGE">Manage</option>
          </select>
        </FormField>
      </div>
      {error instanceof Error && (
        <p role="alert" className="text-xs text-accent-critical">{error.message}</p>
      )}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={isPending || !employeeId.trim()}
          className="px-3 py-1.5 text-xs font-sans font-medium bg-accent-saffron text-surface-deep rounded hover:bg-accent-warning transition-colors disabled:opacity-50"
        >
          {isPending ? 'Adding…' : 'Add'}
        </button>
        <button
          type="button"
          onClick={onDone}
          className="px-3 py-1.5 text-xs font-sans text-text-primary/50 hover:text-text-primary transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}

interface ProjectMembersPanelProps {
  projectId: string
  members: ProjectMember[]
  canManage: boolean
}

export function ProjectMembersPanel({
  projectId,
  members,
  canManage,
}: ProjectMembersPanelProps) {
  const [adding, setAdding] = useState(false)
  const { mutate: remove, isPending: removing } = useRemoveProjectMember(projectId)

  return (
    <section aria-label="Project members">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-sans font-semibold text-text-primary/50 uppercase tracking-wider">
          Team ({members.length})
        </h3>
        {canManage && !adding && (
          <button
            type="button"
            onClick={() => setAdding(true)}
            className="flex items-center gap-1.5 text-xs font-sans text-accent-saffron hover:text-accent-warning transition-colors focus-visible:ring-2 focus-visible:ring-accent-saffron rounded"
          >
            <UserPlus size={12} aria-hidden="true" />
            Add member
          </button>
        )}
      </div>

      {members.length === 0 ? (
        <p className="text-sm text-text-primary/40 font-sans py-2">No members assigned yet.</p>
      ) : (
        <ul className="space-y-1">
          {members.map((m) => (
            <li
              key={m.employee_id}
              className="flex items-center justify-between rounded-md px-3 py-2 bg-surface-base border border-surface-border"
            >
              <div className="min-w-0">
                <p className="text-sm font-sans text-text-primary truncate">{m.full_name}</p>
                <p className="text-xs font-mono text-text-primary/40">{m.employee_code} · {m.designation}</p>
              </div>
              <div className="flex items-center gap-2 flex-none ml-2">
                <span
                  className={cn(
                    'text-xs font-mono px-1.5 py-0.5 rounded',
                    m.role === 'MANAGE'
                      ? 'bg-accent-madder/20 text-accent-warning'
                      : 'bg-surface-border text-text-primary/50'
                  )}
                >
                  {m.role}
                </span>
                {canManage && (
                  <button
                    type="button"
                    onClick={() => remove(m.employee_id)}
                    disabled={removing}
                    aria-label={`Remove ${m.full_name} from project`}
                    className="text-text-primary/30 hover:text-accent-critical transition-colors disabled:opacity-50"
                  >
                    <Trash2 size={13} aria-hidden="true" />
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      {adding && (
        <AddMemberForm projectId={projectId} onDone={() => setAdding(false)} />
      )}
    </section>
  )
}
