'use client'

import { UserPlus, Trash2 } from 'lucide-react'
import { useRemoveProjectMember } from '@/hooks/use-projects'
import { cn } from '@/lib/utils'
import type { ProjectMember } from '@/types'

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
  const { mutate: remove, isPending: removing } = useRemoveProjectMember(projectId)

  return (
    <section aria-label="Project members">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-sans font-semibold text-text-primary/50 uppercase tracking-wider">
          Team ({members.length})
        </h3>
        {canManage && (
          <span
            title="Employee search is not yet available (OPEN-021)"
            className="flex items-center gap-1.5 text-xs font-sans text-text-primary/25 cursor-not-allowed select-none"
            aria-disabled="true"
          >
            <UserPlus size={12} aria-hidden="true" />
            Add member
          </span>
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
                <p className="text-sm font-sans text-text-primary truncate">{m.employee.full_name}</p>
                <p className="text-xs font-mono text-text-primary/40">{m.employee.employee_code}</p>
              </div>
              <div className="flex items-center gap-2 flex-none ml-2">
                <span
                  className={cn(
                    'text-xs font-mono px-1.5 py-0.5 rounded',
                    m.access_level === 'MANAGE'
                      ? 'bg-accent-madder/20 text-accent-warning'
                      : m.access_level === 'CONTRIBUTE'
                      ? 'bg-accent-saffron/10 text-accent-saffron'
                      : 'bg-surface-border text-text-primary/50'
                  )}
                >
                  {m.access_level}
                </span>
                {canManage && (
                  <button
                    type="button"
                    onClick={() => remove(m.employee_id)}
                    disabled={removing}
                    aria-label={`Remove ${m.employee.full_name}`}
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
    </section>
  )
}
