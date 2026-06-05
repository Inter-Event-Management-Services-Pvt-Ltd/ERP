import { createClient } from '@/lib/supabase/client'
import type { MeResponse, PermissionsResponse } from '@/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function getAccessToken(): Promise<string> {
  const supabase = createClient()
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
