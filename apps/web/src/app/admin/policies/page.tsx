'use client'

import { useState } from 'react'
import { format } from 'date-fns'
import { Plus, Pencil } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { Badge } from '@/components/status/badge'
import { usePolicies, useCreatePolicy, useUpdatePolicy } from '@/hooks/use-admin'
import { useMe } from '@/hooks/use-me'
import { apiErrorMessage } from '@/lib/errors'
import type { Policy, CreatePolicyPayload, UpdatePolicyPayload } from '@/types'

const inputCls = 'px-3 py-2 text-sm bg-surface-base border border-surface-border rounded-md text-text-primary placeholder:text-text-primary/25 focus:outline-none focus:ring-1 focus:ring-accent-saffron/50'
const labelCls = 'text-xs font-semibold text-text-primary/60 uppercase tracking-wide'

function defaultForm(): CreatePolicyPayload {
  return { name: '', action_code: '', effect: 'ALLOW', priority: 100, is_active: true }
}

function conditionsToString(c: Record<string, unknown> | null | undefined): string {
  if (!c) return ''
  try { return JSON.stringify(c, null, 2) } catch { return '' }
}

function stringToConditions(s: string): Record<string, unknown> | undefined {
  const trimmed = s.trim()
  if (!trimmed) return undefined
  try { return JSON.parse(trimmed) } catch { return undefined }
}

function PolicyForm({
  initial,
  onSubmit,
  onCancel,
  isPending,
  error,
  requiresOverride,
  overrideReason,
  onOverrideChange,
}: {
  initial: CreatePolicyPayload
  onSubmit: (payload: CreatePolicyPayload, overrideReason?: string) => void
  onCancel: () => void
  isPending: boolean
  error: string
  requiresOverride: boolean
  overrideReason: string
  onOverrideChange: (v: string) => void
}) {
  const [form, setForm] = useState<CreatePolicyPayload>(initial)
  const [conditionsStr, setConditionsStr] = useState(conditionsToString(initial.conditions as Record<string, unknown> | null | undefined))
  const [condError, setCondError] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setCondError('')
    if (!form.name.trim() || !form.action_code.trim()) return
    let conditions: Record<string, unknown> | undefined = undefined
    if (conditionsStr.trim()) {
      conditions = stringToConditions(conditionsStr)
      if (!conditions) { setCondError('Conditions must be valid JSON.'); return }
    }
    onSubmit({ ...form, conditions }, overrideReason || undefined)
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 p-4 bg-surface-base border border-surface-border rounded-lg">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="flex flex-col gap-1.5">
          <label className={labelCls}>Name <span className="text-accent-critical">*</span></label>
          <input className={inputCls} value={form.name} onChange={(e) => setForm(f => ({ ...f, name: e.target.value }))} placeholder="Policy name" />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className={labelCls}>Action Code <span className="text-accent-critical">*</span></label>
          <input className={inputCls} value={form.action_code} onChange={(e) => setForm(f => ({ ...f, action_code: e.target.value }))} placeholder="document.upload" />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className={labelCls}>Effect</label>
          <select className={inputCls} value={form.effect} onChange={(e) => setForm(f => ({ ...f, effect: e.target.value as 'ALLOW' | 'DENY' }))}>
            <option value="ALLOW">ALLOW</option>
            <option value="DENY">DENY</option>
          </select>
        </div>
        <div className="flex flex-col gap-1.5">
          <label className={labelCls}>Priority</label>
          <input type="number" className={inputCls} value={form.priority} onChange={(e) => setForm(f => ({ ...f, priority: Number(e.target.value) }))} min={1} max={1000} />
        </div>
      </div>
      <div className="flex flex-col gap-1.5">
        <label className={labelCls}>Conditions (JSON) <span className="font-normal normal-case text-text-primary/30">(optional)</span></label>
        <textarea
          className={`${inputCls} font-mono text-xs resize-none`}
          rows={3}
          value={conditionsStr}
          onChange={(e) => setConditionsStr(e.target.value)}
          placeholder='{"role": "MANAGER"}'
        />
        {condError && <p role="alert" className="text-xs text-accent-critical">{condError}</p>}
      </div>
      <div className="flex items-center gap-3">
        <input type="checkbox" id="pol-active" checked={form.is_active} onChange={(e) => setForm(f => ({ ...f, is_active: e.target.checked }))} className="accent-accent-saffron" />
        <label htmlFor="pol-active" className={labelCls}>Active</label>
      </div>
      {requiresOverride && (
        <div className="flex flex-col gap-1.5">
          <label className={`${labelCls} text-accent-warning`}>Override Reason (required) <span className="text-accent-critical">*</span></label>
          <input className={inputCls} value={overrideReason} onChange={(e) => onOverrideChange(e.target.value)} placeholder="Meaningful reason for Super User override…" />
        </div>
      )}
      {error && <p role="alert" className="text-xs text-accent-critical">{error}</p>}
      <div className="flex gap-3 pt-1">
        <button type="submit" disabled={isPending} className="px-3 py-1.5 text-xs font-medium bg-accent-saffron/10 border border-accent-saffron/30 text-accent-saffron rounded-lg hover:bg-accent-saffron/20 transition-colors disabled:opacity-50">
          {isPending ? 'Saving…' : 'Save Policy'}
        </button>
        <button type="button" onClick={onCancel} className="px-3 py-1.5 text-xs text-text-primary/60 hover:text-text-primary transition-colors">Cancel</button>
      </div>
    </form>
  )
}

export default function AdminPoliciesPage() {
  const { data: user } = useMe()
  const { data: policies, isLoading, error, refetch } = usePolicies()
  const createMutation = useCreatePolicy()
  const updateMutation = useUpdatePolicy()

  const canManage = (user?.isSuperUser ?? false) || (user?.permissions.includes('policy.manage') ?? false)

  const [showCreate, setShowCreate] = useState(false)
  const [createError, setCreateError] = useState('')
  const [createRequiresOverride, setCreateRequiresOverride] = useState(false)
  const [createOverrideReason, setCreateOverrideReason] = useState('')

  const [editingId, setEditingId] = useState<string | null>(null)
  const [editError, setEditError] = useState('')
  const [editRequiresOverride, setEditRequiresOverride] = useState(false)
  const [editOverrideReason, setEditOverrideReason] = useState('')

  async function handleCreate(payload: CreatePolicyPayload, overrideReason?: string) {
    setCreateError('')
    try {
      await createMutation.mutateAsync({ payload, overrideReason })
      setShowCreate(false)
      setCreateRequiresOverride(false)
      setCreateOverrideReason('')
    } catch (err) {
      const code = (err as { code?: string }).code
      if (code === 'SUPER_USER_OVERRIDE_REASON_REQUIRED') {
        setCreateRequiresOverride(true)
      }
      setCreateError(apiErrorMessage(err))
    }
  }

  async function handleUpdate(id: string, payload: UpdatePolicyPayload, overrideReason?: string) {
    setEditError('')
    try {
      await updateMutation.mutateAsync({ id, payload, overrideReason })
      setEditingId(null)
      setEditRequiresOverride(false)
      setEditOverrideReason('')
    } catch (err) {
      const code = (err as { code?: string }).code
      if (code === 'SUPER_USER_OVERRIDE_REASON_REQUIRED') {
        setEditRequiresOverride(true)
      }
      setEditError(apiErrorMessage(err))
    }
  }

  return (
    <AppShell>
      <PageHeader
        title="Policies"
        subtitle="ABAC policy management"
        actions={
          canManage ? (
            <button
              type="button"
              onClick={() => { setShowCreate(true); setCreateError(''); setCreateRequiresOverride(false); setCreateOverrideReason('') }}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-accent-saffron/10 border border-accent-saffron/30 text-accent-saffron rounded-lg hover:bg-accent-saffron/20 transition-colors"
            >
              <Plus size={16} aria-hidden="true" />
              New Policy
            </button>
          ) : undefined
        }
      />

      <ContentArea>
        {showCreate && (
          <div className="mb-5">
            <h2 className="text-xs font-semibold text-text-primary/40 uppercase tracking-widest mb-3">New Policy</h2>
            <PolicyForm
              initial={defaultForm()}
              onSubmit={handleCreate}
              onCancel={() => { setShowCreate(false); setCreateError(''); setCreateRequiresOverride(false) }}
              isPending={createMutation.isPending}
              error={createError}
              requiresOverride={createRequiresOverride}
              overrideReason={createOverrideReason}
              onOverrideChange={setCreateOverrideReason}
            />
          </div>
        )}

        {isLoading && <SkeletonScreen rows={6} />}

        {!isLoading && error && (
          <ErrorState message={(error as Error).message} onRetry={() => refetch()} />
        )}

        {!isLoading && !error && policies?.length === 0 && (
          <EmptyState icon={Pencil} heading="No policies" body="Create the first ABAC policy." />
        )}

        {!isLoading && !error && policies && policies.length > 0 && (
          <div className="flex flex-col gap-3">
            {policies.map((pol: Policy) => (
              <div key={pol.id} className="rounded-lg border border-surface-border bg-surface-raised p-4">
                {editingId !== pol.id ? (
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex flex-col gap-1.5 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium text-text-primary/85">{pol.name}</span>
                        <Badge variant={pol.effect === 'ALLOW' ? 'approved' : 'rejected'}>{pol.effect}</Badge>
                        {!pol.is_active && <Badge variant="archived">Inactive</Badge>}
                      </div>
                      <div className="flex items-center gap-3 text-xs text-text-primary/50 font-mono flex-wrap">
                        <span>{pol.action_code}</span>
                        <span>priority {pol.priority}</span>
                        {pol.conditions && <span>conditions: {JSON.stringify(pol.conditions)}</span>}
                      </div>
                      <p className="text-xs text-text-primary/30 font-mono">
                        Created {format(new Date(pol.created_at), 'dd MMM yyyy')}
                        {' · Updated '}{format(new Date(pol.updated_at), 'dd MMM yyyy')}
                      </p>
                    </div>
                    {canManage && (
                      <button
                        type="button"
                        onClick={() => { setEditingId(pol.id); setEditError(''); setEditRequiresOverride(false); setEditOverrideReason('') }}
                        aria-label={`Edit policy ${pol.name}`}
                        className="text-text-primary/30 hover:text-accent-saffron transition-colors flex-none"
                      >
                        <Pencil size={13} aria-hidden="true" />
                      </button>
                    )}
                  </div>
                ) : (
                  <PolicyForm
                    initial={{ name: pol.name, action_code: pol.action_code, effect: pol.effect, priority: pol.priority, conditions: pol.conditions ?? undefined, is_active: pol.is_active }}
                    onSubmit={(payload, overrideReason) => handleUpdate(pol.id, payload, overrideReason)}
                    onCancel={() => { setEditingId(null); setEditError(''); setEditRequiresOverride(false) }}
                    isPending={updateMutation.isPending}
                    error={editError}
                    requiresOverride={editRequiresOverride}
                    overrideReason={editOverrideReason}
                    onOverrideChange={setEditOverrideReason}
                  />
                )}
              </div>
            ))}
          </div>
        )}
      </ContentArea>
    </AppShell>
  )
}
