'use client'

import { use, useState } from 'react'
import Link from 'next/link'
import { format } from 'date-fns'
import { ChevronRight, Loader2, Plus } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { ErrorState } from '@/components/states/error-state'
import { Badge } from '@/components/status/badge'
import { ProjectStatusBadge } from '@/components/projects/project-status-badge'
import { FormField, inputCls } from '@/components/ui/form-field'
import { useMe } from '@/hooks/use-me'
import { useTask, useUpdateTask, useAddTaskAssignees, useAddTaskComment, useLinkTaskDocument } from '@/hooks/use-tasks'
import { useTaskStatuses, usePriorityLevels } from '@/hooks/use-lookups'
import { useEmployeeSearch } from '@/hooks/use-employees'
import { apiErrorMessage } from '@/lib/errors'
import type { BadgeVariant, EmployeeSummary, TaskComment, TaskStatusCode } from '@/types'

const STATUS_VARIANT: Record<TaskStatusCode, BadgeVariant> = {
  TODO: 'pending',
  IN_PROGRESS: 'info',
  BLOCKED: 'warning',
  COMPLETED: 'approved',
  CANCELLED: 'archived',
}

function toLocalInputValue(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

interface Props {
  params: Promise<{ id: string }>
}

export default function TaskDetailPage({ params }: Props) {
  const { id } = use(params)
  const { data: user } = useMe()
  const canManage = (user?.isSuperUser || user?.permissions.includes('task.manage')) ?? false

  const { data: task, isLoading, error, refetch } = useTask(id)
  const { data: taskStatuses = [] } = useTaskStatuses()
  const { data: priorityLevels = [] } = usePriorityLevels()
  const { mutate: updateTask, isPending: updating } = useUpdateTask(id)
  const { mutate: addAssignees, isPending: addingAssignee } = useAddTaskAssignees(id)
  const { mutate: addComment, isPending: addingComment } = useAddTaskComment(id)
  const { mutate: linkDocument, isPending: linkingDocument } = useLinkTaskDocument(id)

  const [editError, setEditError] = useState<string | null>(null)
  const [assigneeSearch, setAssigneeSearch] = useState('')
  const { data: assigneeMatches = [] } = useEmployeeSearch(assigneeSearch)
  const [assigneeError, setAssigneeError] = useState<string | null>(null)

  const [commentText, setCommentText] = useState('')
  const [comments, setComments] = useState<TaskComment[]>([])
  const [commentError, setCommentError] = useState<string | null>(null)

  const [documentId, setDocumentId] = useState('')
  const [documentError, setDocumentError] = useState<string | null>(null)

  function handleFieldUpdate(payload: Parameters<typeof updateTask>[0]) {
    setEditError(null)
    updateTask(payload, { onError: (err) => setEditError(apiErrorMessage(err)) })
  }

  function addAssignee(emp: EmployeeSummary) {
    if (task?.assignees.some((a) => a.id === emp.id)) return
    setAssigneeError(null)
    addAssignees(
      { employee_ids: [emp.id] },
      {
        onSuccess: () => setAssigneeSearch(''),
        onError: (err) => setAssigneeError(apiErrorMessage(err)),
      }
    )
  }

  function handleAddComment(e: React.FormEvent) {
    e.preventDefault()
    if (!commentText.trim()) return
    setCommentError(null)
    addComment(
      { comment_text: commentText.trim() },
      {
        onSuccess: (comment) => {
          setComments((prev) => [...prev, comment])
          setCommentText('')
        },
        onError: (err) => setCommentError(apiErrorMessage(err)),
      }
    )
  }

  function handleLinkDocument(e: React.FormEvent) {
    e.preventDefault()
    if (!documentId.trim()) return
    setDocumentError(null)
    linkDocument(
      { document_id: documentId.trim() },
      {
        onSuccess: () => setDocumentId(''),
        onError: (err) => setDocumentError(apiErrorMessage(err)),
      }
    )
  }

  return (
    <AppShell>
      {isLoading && (
        <>
          <PageHeader title="Loading…" />
          <ContentArea>
            <SkeletonScreen rows={8} />
          </ContentArea>
        </>
      )}

      {!isLoading && error && (
        <>
          <PageHeader title="Task" />
          <ContentArea>
            <ErrorState
              message={error instanceof Error ? error.message : 'Failed to load task'}
              onRetry={() => refetch()}
            />
          </ContentArea>
        </>
      )}

      {!isLoading && task && (
        <>
          <PageHeader
            title={task.title}
            subtitle={
              <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-xs text-text-primary/40 font-sans">
                <Link href="/tasks" className="hover:text-text-primary/70 transition-colors">
                  Tasks
                </Link>
                <ChevronRight size={12} aria-hidden="true" />
                <span className="text-text-primary/60 truncate max-w-xs">{task.title}</span>
              </nav>
            }
          />

          <ContentArea className="space-y-6">
            {/* Overview */}
            <div className="rounded-lg border border-surface-border bg-surface-raised px-5 py-4 space-y-4">
              {canManage ? (
                <FormField label="Title" htmlFor="task-edit-title">
                  <input
                    id="task-edit-title"
                    type="text"
                    defaultValue={task.title}
                    onBlur={(e) => {
                      const v = e.target.value.trim()
                      if (v && v !== task.title) handleFieldUpdate({ title: v })
                    }}
                    className={inputCls}
                  />
                </FormField>
              ) : (
                task.description && <p className="text-sm font-sans text-text-primary/70">{task.description}</p>
              )}

              {canManage && (
                <FormField label="Description" htmlFor="task-edit-description">
                  <textarea
                    id="task-edit-description"
                    defaultValue={task.description ?? ''}
                    rows={3}
                    onBlur={(e) => {
                      const v = e.target.value.trim()
                      if (v !== (task.description ?? '')) handleFieldUpdate({ description: v })
                    }}
                    className={inputCls}
                  />
                </FormField>
              )}

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs uppercase tracking-wider text-text-primary/40 font-sans mb-1">Status</p>
                  {canManage ? (
                    <select
                      value={task.task_status_id}
                      onChange={(e) => handleFieldUpdate({ task_status_id: e.target.value })}
                      disabled={updating}
                      aria-label="Task status"
                      className={inputCls}
                    >
                      {taskStatuses.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.name}
                        </option>
                      ))}
                    </select>
                  ) : task.task_status ? (
                    <Badge variant={STATUS_VARIANT[task.task_status.code as TaskStatusCode] ?? 'info'}>
                      {task.task_status.name}
                    </Badge>
                  ) : (
                    '—'
                  )}
                </div>

                <div>
                  <p className="text-xs uppercase tracking-wider text-text-primary/40 font-sans mb-1">Priority</p>
                  {canManage ? (
                    <select
                      value={task.priority_level_id}
                      onChange={(e) => handleFieldUpdate({ priority_level_id: e.target.value })}
                      disabled={updating}
                      aria-label="Task priority"
                      className={inputCls}
                    >
                      {priorityLevels.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </select>
                  ) : task.priority_level ? (
                    <ProjectStatusBadge
                      code={task.priority_level.code}
                      name={task.priority_level.name}
                      type="priority"
                    />
                  ) : (
                    '—'
                  )}
                </div>

                <div>
                  <p className="text-xs uppercase tracking-wider text-text-primary/40 font-sans mb-1">Due</p>
                  {canManage ? (
                    <input
                      type="datetime-local"
                      defaultValue={toLocalInputValue(task.due_at)}
                      onBlur={(e) => {
                        const v = e.target.value
                        handleFieldUpdate({ due_at: v ? new Date(v).toISOString() : null })
                      }}
                      aria-label="Due date"
                      className={inputCls}
                    />
                  ) : (
                    <p className="text-sm font-mono text-text-primary">
                      {task.due_at ? format(new Date(task.due_at), 'dd MMM yyyy HH:mm') : '—'}
                    </p>
                  )}
                </div>

                <div>
                  <p className="text-xs uppercase tracking-wider text-text-primary/40 font-sans mb-1">Project</p>
                  {task.project ? (
                    <Link
                      href={`/projects/${task.project.id}`}
                      className="text-sm font-sans text-accent-saffron/80 hover:text-accent-saffron transition-colors"
                    >
                      {task.project.name}
                    </Link>
                  ) : (
                    <p className="text-sm font-sans text-text-primary/60">—</p>
                  )}
                </div>
              </div>

              {editError && <p role="alert" className="text-xs font-sans text-accent-critical">{editError}</p>}
            </div>

            {/* Assignees */}
            <div>
              <h2 className="font-serif italic text-lg text-text-primary mb-3">Assignees</h2>
              {task.assignees.length > 0 ? (
                <ul className="flex flex-wrap gap-1.5 mb-3">
                  {task.assignees.map((a) => (
                    <li
                      key={a.id}
                      className="rounded-full bg-surface-raised border border-surface-border px-2.5 py-1 text-xs font-sans text-text-primary/80"
                    >
                      {a.full_name}{' '}
                      <span className="text-text-primary/40 font-mono">{a.employee_code}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm font-sans text-text-primary/50 mb-3">No assignees yet.</p>
              )}

              {canManage && (
                <div className="max-w-sm">
                  <label htmlFor="task-assignee-search" className="text-xs font-sans text-text-primary/70 font-medium block mb-1">
                    Add assignee
                  </label>
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
                            disabled={addingAssignee}
                            className="w-full text-left px-3 py-1.5 hover:bg-surface-raised transition-colors disabled:opacity-40"
                          >
                            {emp.full_name}{' '}
                            <span className="text-text-primary/40 font-mono text-xs">{emp.employee_code}</span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                  {assigneeError && <p role="alert" className="mt-1 text-xs font-sans text-accent-critical">{assigneeError}</p>}
                </div>
              )}
            </div>

            {/* Documents */}
            <div>
              <h2 className="font-serif italic text-lg text-text-primary mb-3">Linked Documents</h2>
              {task.document_ids.length > 0 ? (
                <ul className="space-y-1 mb-3">
                  {task.document_ids.map((docId) => (
                    <li key={docId}>
                      <Link
                        href={`/documents/${docId}`}
                        className="text-sm font-mono text-accent-saffron/80 hover:text-accent-saffron transition-colors"
                      >
                        {docId}
                      </Link>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm font-sans text-text-primary/50 mb-3">No documents linked.</p>
              )}

              {canManage && (
                <form onSubmit={handleLinkDocument} className="flex gap-2 max-w-md">
                  <input
                    type="text"
                    value={documentId}
                    onChange={(e) => setDocumentId(e.target.value)}
                    placeholder="Document ID"
                    aria-label="Document ID to link"
                    className={inputCls}
                  />
                  <button
                    type="submit"
                    disabled={linkingDocument || !documentId.trim()}
                    className="flex items-center gap-1 px-3 py-2 text-sm font-sans font-medium rounded-md bg-accent-saffron text-surface-deep hover:bg-accent-warning disabled:opacity-40 transition-colors flex-none"
                  >
                    {linkingDocument ? <Loader2 size={14} className="animate-spin" aria-hidden="true" /> : <Plus size={14} aria-hidden="true" />}
                    Link
                  </button>
                </form>
              )}
              {documentError && <p role="alert" className="mt-1 text-xs font-sans text-accent-critical">{documentError}</p>}
            </div>

            {/* Comments */}
            <div>
              <h2 className="font-serif italic text-lg text-text-primary mb-3">Comments</h2>

              {comments.length > 0 ? (
                <ul className="space-y-3 mb-4">
                  {comments.map((c) => (
                    <li key={c.id} className="rounded-md border border-surface-border bg-surface-raised px-3 py-2">
                      <p className="text-sm font-sans text-text-primary">{c.comment_text}</p>
                      <p className="text-xs font-sans text-text-primary/40 mt-1">
                        {c.employee?.full_name ?? 'You'} · {format(new Date(c.created_at), 'dd MMM yyyy HH:mm')}
                      </p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm font-sans text-text-primary/50 mb-4">
                  No comments added in this session.
                </p>
              )}

              <form onSubmit={handleAddComment} className="flex gap-2 max-w-md">
                <input
                  type="text"
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  placeholder="Add a comment…"
                  aria-label="New comment"
                  className={inputCls}
                />
                <button
                  type="submit"
                  disabled={addingComment || !commentText.trim()}
                  className="flex items-center gap-1 px-3 py-2 text-sm font-sans font-medium rounded-md bg-accent-saffron text-surface-deep hover:bg-accent-warning disabled:opacity-40 transition-colors flex-none"
                >
                  {addingComment && <Loader2 size={14} className="animate-spin" aria-hidden="true" />}
                  Post
                </button>
              </form>
              {commentError && <p role="alert" className="mt-1 text-xs font-sans text-accent-critical">{commentError}</p>}
            </div>
          </ContentArea>
        </>
      )}
    </AppShell>
  )
}
