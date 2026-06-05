import { createClient as createSupabaseClient } from '@/lib/supabase/client'
import type {
  MeResponse,
  PermissionsResponse,
  Client,
  CreateClientPayload,
  Project,
  CreateProjectPayload,
  UpdateProjectPayload,
  AddProjectMemberPayload,
  FolderNode,
  EmployeeSummary,
} from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function getAccessToken(): Promise<string> {
  const supabase = createSupabaseClient()
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  if (!token) throw new Error('No active session')
  return token
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = await getAccessToken()
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(init?.headers ?? {}),
    },
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const code = body?.error?.code ?? `HTTP_${res.status}`
    const message = body?.error?.message ?? res.statusText
    throw Object.assign(new Error(message), { code, status: res.status })
  }

  return res.json() as Promise<T>
}

export async function fetchMe(): Promise<MeResponse> {
  return apiFetch<MeResponse>('/v1/me')
}

export async function fetchPermissions(): Promise<PermissionsResponse> {
  return apiFetch<PermissionsResponse>('/v1/me/permissions')
}

// ─── Clients ──────────────────────────────────────────────────────────────────

export async function fetchClients(): Promise<Client[]> {
  return apiFetch<Client[]>('/v1/clients')
}

export async function fetchClient(id: string): Promise<Client> {
  return apiFetch<Client>(`/v1/clients/${id}`)
}

export async function createClient(payload: CreateClientPayload): Promise<Client> {
  return apiFetch<Client>('/v1/clients', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateClient(
  id: string,
  payload: Partial<CreateClientPayload>
): Promise<Client> {
  return apiFetch<Client>(`/v1/clients/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

// ─── Projects ─────────────────────────────────────────────────────────────────

export async function fetchProjects(): Promise<Project[]> {
  return apiFetch<Project[]>('/v1/projects')
}

export async function fetchProject(id: string): Promise<Project> {
  return apiFetch<Project>(`/v1/projects/${id}`)
}

export async function createProject(payload: CreateProjectPayload): Promise<Project> {
  return apiFetch<Project>('/v1/projects', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateProject(
  id: string,
  payload: UpdateProjectPayload
): Promise<Project> {
  return apiFetch<Project>(`/v1/projects/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function addProjectMember(
  projectId: string,
  payload: AddProjectMemberPayload
): Promise<void> {
  await apiFetch<unknown>(`/v1/projects/${projectId}/members`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function removeProjectMember(
  projectId: string,
  employeeId: string
): Promise<void> {
  await apiFetch<unknown>(`/v1/projects/${projectId}/members/${employeeId}`, {
    method: 'DELETE',
  })
}

// ─── Folders ──────────────────────────────────────────────────────────────────

export async function fetchFolderTree(projectId: string): Promise<FolderNode> {
  return apiFetch<FolderNode>(`/v1/projects/${projectId}/folders/tree`)
}

// ─── Employees ────────────────────────────────────────────────────────────────

export async function fetchEmployees(): Promise<EmployeeSummary[]> {
  return apiFetch<EmployeeSummary[]>('/v1/employees')
}
