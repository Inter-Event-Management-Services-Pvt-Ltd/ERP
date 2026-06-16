'use client'

import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  fetchEmployees,
  fetchDepartments,
  fetchRoles,
  fetchEmployeeDetail,
  createEmployee,
  updateEmployee,
  assignEmployeeRole,
  removeEmployeeRole,
  assignEmployeeDepartment,
} from '@/lib/api'
import type {
  CreateEmployeePayload,
  UpdateEmployeePayload,
  AssignRolePayload,
  DepartmentAssignmentPayload,
} from '@/types'

function useDebounce(value: string, delay: number): string {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}

export function useEmployeeSearch(search: string) {
  const debouncedSearch = useDebounce(search, 300)
  const enabled = debouncedSearch.trim().length >= 2

  return useQuery({
    queryKey: ['employees', 'search', debouncedSearch],
    queryFn: () => fetchEmployees({ status: 'ACTIVE', search: debouncedSearch }),
    enabled,
    staleTime: 30 * 1000,
    placeholderData: [],
  })
}

export function useEmployeeList(params?: { status?: string; search?: string; limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ['employees', 'list', params],
    queryFn: () => fetchEmployees(params),
    staleTime: 30 * 1000,
  })
}

export function useDepartments() {
  return useQuery({
    queryKey: ['departments'],
    queryFn: fetchDepartments,
    staleTime: 10 * 60 * 1000,
  })
}

export function useRoles() {
  return useQuery({
    queryKey: ['roles'],
    queryFn: fetchRoles,
    staleTime: 10 * 60 * 1000,
  })
}

export function useEmployeeDetail(employeeId: string) {
  return useQuery({
    queryKey: ['employees', employeeId],
    queryFn: () => fetchEmployeeDetail(employeeId),
    staleTime: 30 * 1000,
    enabled: !!employeeId,
  })
}

export function useCreateEmployee() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateEmployeePayload) => createEmployee(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['employees'] })
    },
  })
}

export function useUpdateEmployee() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateEmployeePayload }) =>
      updateEmployee(id, payload),
    onSuccess: (_data, { id }) => {
      qc.invalidateQueries({ queryKey: ['employees', id] })
      qc.invalidateQueries({ queryKey: ['employees', 'list'] })
    },
  })
}

export function useAssignEmployeeRole() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      employeeId,
      payload,
      overrideReason,
    }: {
      employeeId: string
      payload: AssignRolePayload
      overrideReason?: string
    }) => assignEmployeeRole(employeeId, payload, overrideReason),
    onSuccess: (_data, { employeeId }) => {
      qc.invalidateQueries({ queryKey: ['employees', employeeId] })
    },
  })
}

export function useRemoveEmployeeRole() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      employeeId,
      roleId,
      overrideReason,
    }: {
      employeeId: string
      roleId: string
      overrideReason?: string
    }) => removeEmployeeRole(employeeId, roleId, overrideReason),
    onSuccess: (_data, { employeeId }) => {
      qc.invalidateQueries({ queryKey: ['employees', employeeId] })
    },
  })
}

export function useAssignEmployeeDepartment() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      employeeId,
      payload,
    }: {
      employeeId: string
      payload: DepartmentAssignmentPayload
    }) => assignEmployeeDepartment(employeeId, payload),
    onSuccess: (_data, { employeeId }) => {
      qc.invalidateQueries({ queryKey: ['employees', employeeId] })
    },
  })
}
