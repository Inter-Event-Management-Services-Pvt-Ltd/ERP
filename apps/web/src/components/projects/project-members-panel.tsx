'use client'

import { useId, useRef, useState, useEffect, KeyboardEvent } from 'react'
import { UserPlus, Trash2, X, Loader2 } from 'lucide-react'
import { useRemoveProjectMember, useAddProjectMember } from '@/hooks/use-projects'
import { useEmployeeSearch } from '@/hooks/use-employees'
import { cn } from '@/lib/utils'
import type { ProjectMember, ProjectMemberRole, EmployeeSummary } from '@/types'

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
      </div>

      {members.length === 0 ? (
        <p className="text-sm text-text-primary/40 font-sans py-2">No members assigned yet.</p>
      ) : (
        <ul className="space-y-1 mb-3">
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

      {canManage && (
        <AddMemberForm projectId={projectId} existingMemberIds={members.map((m) => m.employee_id)} />
      )}
    </section>
  )
}

function AddMemberForm({
  projectId,
  existingMemberIds,
}: {
  projectId: string
  existingMemberIds: string[]
}) {
  const listboxId = useId()
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLUListElement>(null)

  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [activeIndex, setActiveIndex] = useState(-1)
  const [selected, setSelected] = useState<EmployeeSummary | null>(null)
  const [accessLevel, setAccessLevel] = useState<ProjectMemberRole>('VIEW')
  const [dropdownOpen, setDropdownOpen] = useState(false)

  const { data: results = [], isFetching } = useEmployeeSearch(search)
  const filteredResults = results.filter((e) => !existingMemberIds.includes(e.id))

  const { mutate: add, isPending: adding, reset: resetMutation } = useAddProjectMember(projectId)

  useEffect(() => {
    if (dropdownOpen && filteredResults.length > 0) {
      setActiveIndex(0)
    } else {
      setActiveIndex(-1)
    }
  }, [filteredResults, dropdownOpen])

  function openForm() {
    setOpen(true)
    setTimeout(() => inputRef.current?.focus(), 0)
  }

  function closeForm() {
    setOpen(false)
    setSearch('')
    setSelected(null)
    setAccessLevel('VIEW')
    setDropdownOpen(false)
    setActiveIndex(-1)
    resetMutation()
  }

  function selectEmployee(emp: EmployeeSummary) {
    setSelected(emp)
    setSearch('')
    setDropdownOpen(false)
    setActiveIndex(-1)
  }

  function clearSelected() {
    setSelected(null)
    setSearch('')
    setTimeout(() => inputRef.current?.focus(), 0)
  }

  function handleSearchChange(value: string) {
    setSearch(value)
    setSelected(null)
    setDropdownOpen(value.trim().length >= 2)
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (!dropdownOpen || filteredResults.length === 0) {
      if (e.key === 'Escape') closeForm()
      return
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIndex((i) => Math.min(i + 1, filteredResults.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIndex((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter' && activeIndex >= 0) {
      e.preventDefault()
      selectEmployee(filteredResults[activeIndex])
    } else if (e.key === 'Escape') {
      setDropdownOpen(false)
    }
  }

  function handleSubmit() {
    if (!selected) return
    add(
      { employee_id: selected.id, access_level: accessLevel },
      { onSuccess: closeForm }
    )
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={openForm}
        className="flex items-center gap-1.5 text-xs font-sans text-accent-saffron/70 hover:text-accent-saffron transition-colors py-1"
      >
        <UserPlus size={12} aria-hidden="true" />
        Add member
      </button>
    )
  }

  return (
    <div className="rounded-md border border-surface-border bg-surface-base p-3 space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-sans font-semibold text-text-primary/50 uppercase tracking-wider">
          Add member
        </p>
        <button
          type="button"
          onClick={closeForm}
          aria-label="Cancel adding member"
          className="text-text-primary/30 hover:text-text-primary/60 transition-colors"
        >
          <X size={13} aria-hidden="true" />
        </button>
      </div>

      {/* Employee search combobox */}
      <div className="relative">
        <label
          htmlFor={`${listboxId}-input`}
          className="text-xs font-sans text-text-primary/70 font-medium block mb-1"
        >
          Employee
        </label>

        {selected ? (
          <div className="flex items-center justify-between rounded-md border border-accent-saffron/30 bg-surface-raised px-3 py-2">
            <div className="min-w-0">
              <p className="text-sm font-sans text-text-primary truncate">{selected.full_name}</p>
              <p className="text-xs font-mono text-text-primary/40">{selected.employee_code} · {selected.designation}</p>
            </div>
            <button
              type="button"
              onClick={clearSelected}
              aria-label="Clear selected employee"
              className="ml-2 text-text-primary/30 hover:text-text-primary/60 transition-colors flex-none"
            >
              <X size={13} aria-hidden="true" />
            </button>
          </div>
        ) : (
          <div
            role="combobox"
            aria-expanded={dropdownOpen}
            aria-haspopup="listbox"
            aria-controls={listboxId}
            aria-owns={listboxId}
          >
            <input
              ref={inputRef}
              id={`${listboxId}-input`}
              type="text"
              value={search}
              onChange={(e) => handleSearchChange(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => {
                if (search.trim().length >= 2) setDropdownOpen(true)
              }}
              onBlur={(e) => {
                if (!listRef.current?.contains(e.relatedTarget as Node)) {
                  setTimeout(() => setDropdownOpen(false), 150)
                }
              }}
              placeholder="Type name or code…"
              autoComplete="off"
              aria-autocomplete="list"
              aria-activedescendant={
                activeIndex >= 0 ? `${listboxId}-opt-${activeIndex}` : undefined
              }
              className={cn(
                'w-full rounded-md border border-surface-border bg-surface-raised px-3 py-2',
                'text-sm font-sans text-text-primary placeholder:text-text-primary/30',
                'focus:outline-none focus:ring-2 focus:ring-accent-saffron focus:ring-offset-1 focus:ring-offset-surface-base',
                'transition-colors duration-100'
              )}
            />
          </div>
        )}

        {/* Dropdown results */}
        {dropdownOpen && !selected && (
          <ul
            ref={listRef}
            id={listboxId}
            role="listbox"
            aria-label="Employee search results"
            className="absolute left-0 right-0 top-full mt-1 z-50 rounded-md border border-surface-border bg-surface-deep shadow-lg overflow-hidden max-h-44 overflow-y-auto"
          >
            {isFetching && filteredResults.length === 0 ? (
              <li className="flex items-center gap-2 px-3 py-2.5 text-xs font-sans text-text-primary/40">
                <Loader2 size={12} className="animate-spin" aria-hidden="true" />
                Searching…
              </li>
            ) : filteredResults.length === 0 ? (
              <li className="px-3 py-2.5 text-xs font-sans text-text-primary/40">
                No active employees found.
              </li>
            ) : (
              filteredResults.map((emp, i) => (
                <li
                  key={emp.id}
                  id={`${listboxId}-opt-${i}`}
                  role="option"
                  aria-selected={i === activeIndex}
                  onMouseDown={(e) => {
                    e.preventDefault()
                    selectEmployee(emp)
                  }}
                  onMouseEnter={() => setActiveIndex(i)}
                  className={cn(
                    'px-3 py-2 cursor-pointer transition-colors',
                    i === activeIndex ? 'bg-surface-raised' : 'hover:bg-surface-raised/60'
                  )}
                >
                  <p className="text-sm font-sans text-text-primary">{emp.full_name}</p>
                  <p className="text-xs font-mono text-text-primary/40">
                    {emp.employee_code} · {emp.designation}
                  </p>
                </li>
              ))
            )}
          </ul>
        )}
      </div>

      {/* Access level */}
      <div>
        <label
          htmlFor={`${listboxId}-access`}
          className="text-xs font-sans text-text-primary/70 font-medium block mb-1"
        >
          Access level
        </label>
        <select
          id={`${listboxId}-access`}
          value={accessLevel}
          onChange={(e) => setAccessLevel(e.target.value as ProjectMemberRole)}
          className={cn(
            'w-full rounded-md border border-surface-border bg-surface-raised px-3 py-2',
            'text-sm font-sans text-text-primary',
            'focus:outline-none focus:ring-2 focus:ring-accent-saffron focus:ring-offset-1 focus:ring-offset-surface-base',
            'transition-colors duration-100'
          )}
        >
          <option value="VIEW">VIEW — read-only</option>
          <option value="CONTRIBUTE">CONTRIBUTE — upload & edit</option>
          <option value="MANAGE">MANAGE — full control</option>
        </select>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 justify-end">
        <button
          type="button"
          onClick={closeForm}
          className="text-xs font-sans text-text-primary/50 hover:text-text-primary/80 px-3 py-1.5 rounded-md transition-colors"
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!selected || adding}
          className={cn(
            'flex items-center gap-1.5 text-xs font-sans px-3 py-1.5 rounded-md transition-colors',
            'bg-accent-saffron/90 text-surface-deep font-medium',
            'hover:bg-accent-saffron disabled:opacity-40 disabled:cursor-not-allowed'
          )}
        >
          {adding && <Loader2 size={11} className="animate-spin" aria-hidden="true" />}
          Add
        </button>
      </div>
    </div>
  )
}
