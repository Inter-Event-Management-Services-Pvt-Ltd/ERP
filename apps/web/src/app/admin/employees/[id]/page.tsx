'use client'

import { useState } from 'react'
import { use } from 'react'
import { format } from 'date-fns'
import { ArrowLeft, Trash2, Plus } from 'lucide-react'
import Link from 'next/link'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { ErrorState } from '@/components/states/error-state'
import { Badge } from '@/components/status/badge'
import {
  useEmployeeDetail,
  useUpdateEmployee,
  useDepartments,
  useRoles,
  useAssignEmployeeRole,
  useRemoveEmployeeRole,
  useAssignEmployeeDepartment,
} from '@/hooks/use-employees'
import { useMe } from '@/hooks/use-me'
import { apiErrorMessage } from '@/lib/errors'
import type { BadgeVariant, EmploymentStatus, UpdateEmployeePayload, AssignRolePayload, DepartmentAssignmentPayload } from '@/types'

const STATUS_VARIANT: Record<EmploymentStatus, BadgeVariant> = {
  ACTIVE: 'active',
  ON_LEAVE: 'warning',
  INACTIVE: 'archived',
  EXITED: 'rejected',
}

const inputCls = 'px-3 py-2 text-sm bg-surface-base border border-surface-border rounded-md text-text-primary placeholder:text-text-primary/25 focus:outline-none focus:ring-1 focus:ring-accent-saffron/50'
const labelCls = 'text-xs font-semibold text-text-primary/60 uppercase tracking-wide'

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border border-surface-border bg-surface-raised p-5 flex flex-col gap-4">
      <h2 className="text-xs font-semibold text-text-primary/40 uppercase tracking-widest">{title}</h2>
      {children}
    </section>
  )
}

export default function EmployeeDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const { data: user } = useMe()
  const { data: employee, isLoading, error, refetch } = useEmployeeDetail(id)
  const { data: departments } = useDepartments()
  const { data: roles } = useRoles()
  const updateMutation = useUpdateEmployee()
  const assignRoleMutation = useAssignEmployeeRole()
  const removeRoleMutation = useRemoveEmployeeRole()
  const assignDeptMutation = useAssignEmployeeDepartment()

  const canManageEmployees = (user?.isSuperUser ?? false) || (user?.permissions.includes('employee.manage') ?? false)
  const canManageRoles = (user?.isSuperUser ?? false) || (user?.permissions.includes('role.manage') ?? false)

  // Edit employee state
  const [editMode, setEditMode] = useState(false)
  const [editForm, setEditForm] = useState<UpdateEmployeePayload>({})
  const [editError, setEditError] = useState('')

  // Assign role state
  const [showAssignRole, setShowAssignRole] = useState(false)
  const [roleForm, setRoleForm] = useState<AssignRolePayload>({ role_id: '', expires_at: null })
  const [roleOverrideReason, setRoleOverrideReason] = useState('')
  const [showRoleOverride, setShowRoleOverride] = useState(false)
  const [roleError, setRoleError] = useState('')

  // Assign department state
  const [showAssignDept, setShowAssignDept] = useState(false)
  const [deptForm, setDeptForm] = useState<DepartmentAssignmentPayload>({ department_id: '', valid_from: '' })
  const [deptError, setDeptError] = useState('')

  function openEdit() {
    if (!employee) return
    setEditForm({
      full_name: employee.full_name,
      designation: employee.designation,
      employment_status: employee.employment_status,
    })
    setEditMode(true)
    setEditError('')
  }

  async function handleEditSubmit(e: React.FormEvent) {
    e.preventDefault()
    setEditError('')
    try {
      await updateMutation.mutateAsync({ id, payload: editForm })
      setEditMode(false)
    } catch (err) {
      setEditError(apiErrorMessage(err))
    }
  }

  async function handleAssignRole(e: React.FormEvent) {
    e.preventDefault()
    setRoleError('')
    if (!roleForm.role_id) { setRoleError('Select a role.'); return }
    try {
      await assignRoleMutation.mutateAsync({
        employeeId: id,
        payload: roleForm,
        overrideReason: roleOverrideReason || undefined,
      })
      setShowAssignRole(false)
      setRoleForm({ role_id: '', expires_at: null })
      setRoleOverrideReason('')
      setShowRoleOverride(false)
      refetch()
    } catch (err) {
      const code = (err as { code?: string }).code
      if (code === 'SUPER_USER_OVERRIDE_REASON_REQUIRED') {
        setShowRoleOverride(true)
        setRoleError(apiErrorMessage(err))
      } else {
        setRoleError(apiErrorMessage(err))
      }
    }
  }

  async function handleRemoveRole(roleId: string) {
    try {
      await removeRoleMutation.mutateAsync({ employeeId: id, roleId })
      refetch()
    } catch (err) {
      /* surface via refetch — role removal errors will show on next render */
      console.error(apiErrorMessage(err))
    }
  }

  async function handleAssignDept(e: React.FormEvent) {
    e.preventDefault()
    setDeptError('')
    if (!deptForm.department_id) { setDeptError('Select a department.'); return }
    if (!deptForm.valid_from) { setDeptError('Valid from date is required.'); return }
    try {
      await assignDeptMutation.mutateAsync({ employeeId: id, payload: deptForm })
      setShowAssignDept(false)
      setDeptForm({ department_id: '', valid_from: '' })
      refetch()
    } catch (err) {
      setDeptError(apiErrorMessage(err))
    }
  }

  if (isLoading) {
    return (
      <AppShell>
        <PageHeader title="Employee" subtitle="Loading…" />
        <ContentArea><SkeletonScreen rows={8} /></ContentArea>
      </AppShell>
    )
  }

  if (error || !employee) {
    return (
      <AppShell>
        <PageHeader title="Employee" subtitle="Not found" />
        <ContentArea>
          <ErrorState message={error ? (error as Error).message : 'Employee not found.'} onRetry={() => refetch()} />
        </ContentArea>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <PageHeader
        title={employee.full_name}
        subtitle={
          <Link href="/admin/employees" className="font-mono text-xs text-accent-saffron/60 hover:text-accent-saffron transition-colors uppercase tracking-wide">
            ← Employees
          </Link>
        }
      />
      <ContentArea>
        <div className="max-w-2xl flex flex-col gap-5">

          {/* Identity card */}
          <SectionCard title="Identity">
            {!editMode ? (
              <>
                <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 text-sm">
                  <div>
                    <dt className="text-xs text-text-primary/40 uppercase tracking-wider mb-0.5">Code</dt>
                    <dd className="font-mono text-xs text-text-primary/60">{employee.employee_code}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-text-primary/40 uppercase tracking-wider mb-0.5">Status</dt>
                    <dd><Badge variant={STATUS_VARIANT[employee.employment_status] ?? 'info'}>{employee.employment_status}</Badge></dd>
                  </div>
                  <div>
                    <dt className="text-xs text-text-primary/40 uppercase tracking-wider mb-0.5">Email</dt>
                    <dd className="text-text-primary/70 text-xs">{employee.official_email}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-text-primary/40 uppercase tracking-wider mb-0.5">Designation</dt>
                    <dd className="text-text-primary/70">{employee.designation}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-text-primary/40 uppercase tracking-wider mb-0.5">Super User</dt>
                    <dd className="text-text-primary/70">{employee.account?.is_super_user ? 'Yes' : 'No'}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-text-primary/40 uppercase tracking-wider mb-0.5">Account active</dt>
                    <dd className="text-text-primary/70">{employee.account?.is_active ? 'Yes' : 'No'}</dd>
                  </div>
                </dl>
                {canManageEmployees && (
                  <button type="button" onClick={openEdit} className="self-start text-xs font-medium text-accent-saffron hover:text-accent-saffron/70 transition-colors">
                    Edit details
                  </button>
                )}
              </>
            ) : (
              <form onSubmit={handleEditSubmit} className="flex flex-col gap-3">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="flex flex-col gap-1.5">
                    <label htmlFor="edit-name" className={labelCls}>Full Name</label>
                    <input id="edit-name" className={inputCls} value={editForm.full_name ?? ''} onChange={(e) => setEditForm(f => ({ ...f, full_name: e.target.value }))} />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label htmlFor="edit-designation" className={labelCls}>Designation</label>
                    <input id="edit-designation" className={inputCls} value={editForm.designation ?? ''} onChange={(e) => setEditForm(f => ({ ...f, designation: e.target.value }))} />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label htmlFor="edit-status" className={labelCls}>Status</label>
                    <select id="edit-status" className={inputCls} value={editForm.employment_status ?? ''} onChange={(e) => setEditForm(f => ({ ...f, employment_status: e.target.value as EmploymentStatus }))}>
                      {(['ACTIVE', 'ON_LEAVE', 'INACTIVE', 'EXITED'] as const).map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label htmlFor="edit-left" className={labelCls}>Left On</label>
                    <input id="edit-left" type="date" className={inputCls} value={editForm.left_on ?? ''} onChange={(e) => setEditForm(f => ({ ...f, left_on: e.target.value || null }))} />
                  </div>
                </div>
                {editError && <p role="alert" className="text-xs text-accent-critical">{editError}</p>}
                <div className="flex gap-3 pt-1">
                  <button type="submit" disabled={updateMutation.isPending} className="px-4 py-2 text-sm font-medium bg-accent-saffron/10 border border-accent-saffron/30 text-accent-saffron rounded-lg hover:bg-accent-saffron/20 transition-colors disabled:opacity-50">
                    {updateMutation.isPending ? 'Saving…' : 'Save Changes'}
                  </button>
                  <button type="button" onClick={() => setEditMode(false)} className="px-4 py-2 text-sm text-text-primary/60 hover:text-text-primary transition-colors">Cancel</button>
                </div>
              </form>
            )}
          </SectionCard>

          {/* Department */}
          <SectionCard title="Department">
            <div className="text-sm">
              {employee.current_department ? (
                <span>
                  <span className="font-mono text-xs text-text-primary/40 mr-1.5">{employee.current_department.code}</span>
                  <span className="text-text-primary/80">{employee.current_department.name}</span>
                </span>
              ) : (
                <span className="text-text-primary/30">No department assigned</span>
              )}
            </div>
            {canManageEmployees && !showAssignDept && (
              <button type="button" onClick={() => setShowAssignDept(true)} className="self-start text-xs font-medium text-accent-saffron hover:text-accent-saffron/70 transition-colors">
                Change department
              </button>
            )}
            {showAssignDept && (
              <form onSubmit={handleAssignDept} className="flex flex-col gap-3 p-4 bg-surface-base border border-surface-border rounded-lg">
                <div className="flex flex-col gap-1.5">
                  <label htmlFor="dept-select" className={labelCls}>Department <span className="text-accent-critical">*</span></label>
                  <select id="dept-select" className={inputCls} value={deptForm.department_id} onChange={(e) => setDeptForm(f => ({ ...f, department_id: e.target.value }))}>
                    <option value="">Select…</option>
                    {departments?.map(d => <option key={d.id} value={d.id}>{d.code} — {d.name}</option>)}
                  </select>
                </div>
                <div className="flex flex-col gap-1.5">
                  <label htmlFor="dept-from" className={labelCls}>Valid From <span className="text-accent-critical">*</span></label>
                  <input id="dept-from" type="date" className={inputCls} value={deptForm.valid_from} onChange={(e) => setDeptForm(f => ({ ...f, valid_from: e.target.value }))} />
                </div>
                {deptError && <p role="alert" className="text-xs text-accent-critical">{deptError}</p>}
                <div className="flex gap-3">
                  <button type="submit" disabled={assignDeptMutation.isPending} className="px-3 py-1.5 text-xs font-medium bg-accent-saffron/10 border border-accent-saffron/30 text-accent-saffron rounded-lg hover:bg-accent-saffron/20 transition-colors disabled:opacity-50">
                    {assignDeptMutation.isPending ? 'Saving…' : 'Assign'}
                  </button>
                  <button type="button" onClick={() => setShowAssignDept(false)} className="px-3 py-1.5 text-xs text-text-primary/60 hover:text-text-primary transition-colors">Cancel</button>
                </div>
              </form>
            )}
          </SectionCard>

          {/* Roles */}
          <SectionCard title="Roles">
            {employee.roles.length === 0 ? (
              <p className="text-sm text-text-primary/40">No roles assigned.</p>
            ) : (
              <ul className="flex flex-col gap-2">
                {employee.roles.map((ra) => (
                  <li key={ra.role.id} className="flex items-center justify-between gap-4 p-3 bg-surface-base border border-surface-border rounded-lg">
                    <div>
                      <span className="font-mono text-xs text-accent-saffron/80 mr-2">{ra.role.code}</span>
                      <span className="text-sm text-text-primary/80">{ra.role.name}</span>
                      {ra.expires_at && (
                        <span className="ml-2 text-xs text-text-primary/40">
                          expires {format(new Date(ra.expires_at), 'dd MMM yyyy')}
                        </span>
                      )}
                    </div>
                    {canManageRoles && (
                      <button
                        type="button"
                        onClick={() => handleRemoveRole(ra.role.id)}
                        disabled={removeRoleMutation.isPending}
                        aria-label={`Remove ${ra.role.name} role`}
                        className="text-text-primary/30 hover:text-accent-critical transition-colors disabled:opacity-50"
                      >
                        <Trash2 size={13} aria-hidden="true" />
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            )}

            {canManageRoles && !showAssignRole && (
              <button type="button" onClick={() => setShowAssignRole(true)} className="self-start flex items-center gap-1.5 text-xs font-medium text-accent-saffron hover:text-accent-saffron/70 transition-colors">
                <Plus size={12} aria-hidden="true" />
                Assign role
              </button>
            )}

            {showAssignRole && (
              <form onSubmit={handleAssignRole} className="flex flex-col gap-3 p-4 bg-surface-base border border-surface-border rounded-lg">
                <div className="flex flex-col gap-1.5">
                  <label htmlFor="role-select" className={labelCls}>Role <span className="text-accent-critical">*</span></label>
                  <select id="role-select" className={inputCls} value={roleForm.role_id} onChange={(e) => setRoleForm(f => ({ ...f, role_id: e.target.value }))}>
                    <option value="">Select…</option>
                    {roles?.map(r => <option key={r.id} value={r.id}>{r.code} — {r.name}</option>)}
                  </select>
                </div>
                <div className="flex flex-col gap-1.5">
                  <label htmlFor="role-expires" className={labelCls}>Expires At <span className="font-normal normal-case text-text-primary/30">(optional)</span></label>
                  <input id="role-expires" type="date" className={inputCls} value={roleForm.expires_at ?? ''} onChange={(e) => setRoleForm(f => ({ ...f, expires_at: e.target.value || null }))} />
                </div>
                {showRoleOverride && (
                  <div className="flex flex-col gap-1.5">
                    <label htmlFor="role-override" className={labelCls}>Override Reason <span className="text-accent-critical">*</span></label>
                    <input id="role-override" className={inputCls} value={roleOverrideReason} onChange={(e) => setRoleOverrideReason(e.target.value)} placeholder="Meaningful reason for Super User override…" />
                  </div>
                )}
                {roleError && <p role="alert" className="text-xs text-accent-critical">{roleError}</p>}
                <div className="flex gap-3">
                  <button type="submit" disabled={assignRoleMutation.isPending} className="px-3 py-1.5 text-xs font-medium bg-accent-saffron/10 border border-accent-saffron/30 text-accent-saffron rounded-lg hover:bg-accent-saffron/20 transition-colors disabled:opacity-50">
                    {assignRoleMutation.isPending ? 'Assigning…' : 'Assign'}
                  </button>
                  <button type="button" onClick={() => { setShowAssignRole(false); setShowRoleOverride(false); setRoleError('') }} className="px-3 py-1.5 text-xs text-text-primary/60 hover:text-text-primary transition-colors">Cancel</button>
                </div>
              </form>
            )}
          </SectionCard>

        </div>
      </ContentArea>
    </AppShell>
  )
}
