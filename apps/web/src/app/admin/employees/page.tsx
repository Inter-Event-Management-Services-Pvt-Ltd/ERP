'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Plus, Search } from 'lucide-react'
import { AppShell } from '@/components/layout/app-shell'
import { PageHeader } from '@/components/layout/page-header'
import { ContentArea } from '@/components/layout/content-area'
import { SkeletonScreen } from '@/components/states/skeleton-screen'
import { EmptyState } from '@/components/states/empty-state'
import { ErrorState } from '@/components/states/error-state'
import { Badge } from '@/components/status/badge'
import { useEmployeeList, useCreateEmployee } from '@/hooks/use-employees'
import { useMe } from '@/hooks/use-me'
import { apiErrorMessage } from '@/lib/errors'
import type { BadgeVariant, EmploymentStatus, CreateEmployeePayload } from '@/types'

const STATUS_TABS: Array<{ label: string; value: string }> = [
  { label: 'Active', value: 'ACTIVE' },
  { label: 'On Leave', value: 'ON_LEAVE' },
  { label: 'Inactive', value: 'INACTIVE' },
  { label: 'Exited', value: 'EXITED' },
]

const STATUS_VARIANT: Record<EmploymentStatus, BadgeVariant> = {
  ACTIVE: 'active',
  ON_LEAVE: 'warning',
  INACTIVE: 'archived',
  EXITED: 'rejected',
}

function CreateEmployeeDialog({
  onClose,
  onCreated,
}: {
  onClose: () => void
  onCreated: () => void
}) {
  const mutation = useCreateEmployee()
  const [form, setForm] = useState<CreateEmployeePayload>({
    employee_code: '',
    full_name: '',
    official_email: '',
    phone: '',
    designation: '',
    employment_status: 'ACTIVE',
    joined_on: '',
  })
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    if (!form.employee_code.trim() || !form.full_name.trim() || !form.official_email.trim() || !form.designation.trim() || !form.joined_on) {
      setError('Employee code, full name, email, designation and join date are required.')
      return
    }
    try {
      await mutation.mutateAsync({
        ...form,
        phone: form.phone?.trim() || undefined,
      })
      onCreated()
      onClose()
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  const inputCls = 'px-3 py-2 text-sm bg-surface-base border border-surface-border rounded-md text-text-primary placeholder:text-text-primary/25 focus:outline-none focus:ring-1 focus:ring-accent-saffron/50'
  const labelCls = 'text-xs font-semibold text-text-primary/60 uppercase tracking-wide'

  return (
    <div
      className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      aria-label="New Employee"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-surface-raised border border-surface-border rounded-xl w-full max-w-lg p-6 flex flex-col gap-4 max-h-[90vh] overflow-y-auto">
        <h2 className="text-sm font-semibold text-text-primary">New Employee</h2>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="ec-code" className={labelCls}>Employee Code <span className="text-accent-critical">*</span></label>
              <input id="ec-code" className={inputCls} value={form.employee_code} onChange={(e) => setForm(f => ({ ...f, employee_code: e.target.value }))} placeholder="IEMS-OPS-010" />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="ec-status" className={labelCls}>Status <span className="text-accent-critical">*</span></label>
              <select id="ec-status" className={inputCls} value={form.employment_status} onChange={(e) => setForm(f => ({ ...f, employment_status: e.target.value as EmploymentStatus }))}>
                {STATUS_TABS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="ec-name" className={labelCls}>Full Name <span className="text-accent-critical">*</span></label>
            <input id="ec-name" className={inputCls} value={form.full_name} onChange={(e) => setForm(f => ({ ...f, full_name: e.target.value }))} placeholder="Aarav Mehta" />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="ec-email" className={labelCls}>Official Email <span className="text-accent-critical">*</span></label>
            <input id="ec-email" type="email" className={inputCls} value={form.official_email} onChange={(e) => setForm(f => ({ ...f, official_email: e.target.value }))} placeholder="aarav.mehta@iemsnewdelhi.com" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="ec-designation" className={labelCls}>Designation <span className="text-accent-critical">*</span></label>
              <input id="ec-designation" className={inputCls} value={form.designation} onChange={(e) => setForm(f => ({ ...f, designation: e.target.value }))} placeholder="Coordinator" />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="ec-phone" className={labelCls}>Phone</label>
              <input id="ec-phone" className={inputCls} value={form.phone ?? ''} onChange={(e) => setForm(f => ({ ...f, phone: e.target.value }))} placeholder="+91-99999-00000" />
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="ec-joined" className={labelCls}>Joined On <span className="text-accent-critical">*</span></label>
            <input id="ec-joined" type="date" className={inputCls} value={form.joined_on} onChange={(e) => setForm(f => ({ ...f, joined_on: e.target.value }))} />
          </div>

          {error && <p role="alert" className="text-xs text-accent-critical">{error}</p>}

          <div className="flex gap-3 pt-1">
            <button
              type="submit"
              disabled={mutation.isPending}
              className="px-4 py-2 text-sm font-medium bg-accent-saffron/10 border border-accent-saffron/30 text-accent-saffron rounded-lg hover:bg-accent-saffron/20 transition-colors disabled:opacity-50"
            >
              {mutation.isPending ? 'Creating…' : 'Create Employee'}
            </button>
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-text-primary/60 hover:text-text-primary transition-colors">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function AdminEmployeesPage() {
  const { data: user } = useMe()
  const [statusFilter, setStatusFilter] = useState('ACTIVE')
  const [searchInput, setSearchInput] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchInput.trim()), 300)
    return () => clearTimeout(timer)
  }, [searchInput])

  const canManage = (user?.isSuperUser ?? false) || (user?.permissions.includes('employee.manage') ?? false)

  const { data: employees, isLoading, error, refetch } = useEmployeeList({
    status: statusFilter,
    search: debouncedSearch || undefined,
    limit: 100,
  })

  return (
    <AppShell>
      <PageHeader
        title="Employees"
        subtitle="Employee directory and admin management"
        actions={
          canManage ? (
            <button
              type="button"
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-accent-saffron/10 border border-accent-saffron/30 text-accent-saffron rounded-lg hover:bg-accent-saffron/20 transition-colors"
            >
              <Plus size={16} aria-hidden="true" />
              New Employee
            </button>
          ) : undefined
        }
      />

      <ContentArea>
        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3 mb-5">
          <div className="flex gap-1 flex-wrap" role="group" aria-label="Filter by status">
            {STATUS_TABS.map((tab) => (
              <button
                key={tab.value}
                type="button"
                onClick={() => setStatusFilter(tab.value)}
                aria-pressed={statusFilter === tab.value}
                className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors ${
                  statusFilter === tab.value
                    ? 'bg-accent-saffron/10 text-accent-saffron border border-accent-saffron/30'
                    : 'text-text-primary/50 hover:text-text-primary border border-transparent'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2 border border-surface-border rounded-lg px-3 py-1.5 bg-surface-base sm:w-64">
            <Search size={13} className="text-text-primary/30 flex-none" aria-hidden="true" />
            <input
              type="search"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search name, code, email…"
              aria-label="Search employees"
              className="bg-transparent text-sm text-text-primary placeholder:text-text-primary/25 focus:outline-none flex-1"
            />
          </div>
        </div>

        {isLoading && <SkeletonScreen rows={8} />}

        {!isLoading && error && (
          <ErrorState message={(error as Error).message} onRetry={() => refetch()} />
        )}

        {!isLoading && !error && employees?.length === 0 && (
          <EmptyState icon={Search} heading="No employees" body="No employees match the current filter." />
        )}

        {!isLoading && !error && employees && employees.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-surface-border">
            <table className="w-full text-sm font-sans">
              <thead>
                <tr className="border-b border-surface-border bg-surface-raised">
                  {['Code', 'Name', 'Email', 'Designation', 'Status'].map((h) => (
                    <th key={h} scope="col" className="px-4 py-2.5 text-left text-xs font-semibold text-text-primary/50 uppercase tracking-wider whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {employees.map((emp, i) => (
                  <tr
                    key={emp.id}
                    className={`border-b border-surface-border last:border-0 hover:bg-surface-raised/50 transition-colors ${
                      i % 2 === 0 ? 'bg-surface-base' : 'bg-surface-deep/30'
                    }`}
                  >
                    <td className="px-4 py-3 font-mono text-xs text-text-primary/50 whitespace-nowrap">
                      {emp.employee_code}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <Link
                        href={`/admin/employees/${emp.id}`}
                        className="font-medium text-text-primary/80 hover:text-accent-saffron transition-colors"
                      >
                        {emp.full_name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-xs text-text-primary/55">{emp.official_email}</td>
                    <td className="px-4 py-3 text-text-primary/70">{emp.designation}</td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <Badge variant={STATUS_VARIANT[emp.employment_status as EmploymentStatus] ?? 'info'}>
                        {emp.employment_status}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </ContentArea>

      {showCreate && (
        <CreateEmployeeDialog
          onClose={() => setShowCreate(false)}
          onCreated={() => refetch()}
        />
      )}
    </AppShell>
  )
}
