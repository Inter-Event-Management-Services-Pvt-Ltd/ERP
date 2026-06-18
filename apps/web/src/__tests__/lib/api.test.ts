import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

const mockGetSession = vi.fn()

vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({ auth: { getSession: mockGetSession } }),
}))

import { fetchMe } from '@/lib/api'

describe('apiFetch', () => {
  const realFetch = globalThis.fetch

  beforeEach(() => {
    mockGetSession.mockResolvedValue({
      data: { session: { access_token: 'test-token' } },
    })
  })

  afterEach(() => {
    globalThis.fetch = realFetch
  })

  it('returns parsed JSON on a 200 response', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: { get: () => null },
      json: async () => ({ id: 'u1', email: 'a@b.com' }),
    })
    const result = await fetchMe()
    expect(result).toMatchObject({ id: 'u1', email: 'a@b.com' })
  })

  it('throws with code and status from the error envelope', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      statusText: 'Forbidden',
      headers: { get: () => null },
      json: async () => ({
        error: { code: 'PERMISSION_DENIED', message: 'Access denied' },
      }),
    })
    await expect(fetchMe()).rejects.toMatchObject({
      message: 'Access denied',
      code: 'PERMISSION_DENIED',
      status: 403,
    })
  })

  it('falls back to HTTP_NNN code when the error envelope is absent', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      headers: { get: () => null },
      json: async () => ({}),
    })
    await expect(fetchMe()).rejects.toMatchObject({
      code: 'HTTP_500',
      status: 500,
    })
  })

  it('throws No active session when the Supabase session is null', async () => {
    mockGetSession.mockResolvedValueOnce({ data: { session: null } })
    await expect(fetchMe()).rejects.toThrow('No active session')
  })

  it('attaches requestId to a thrown error when x-request-id header is present', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      headers: { get: (h: string) => (h === 'x-request-id' ? 'req-abc' : null) },
      json: async () => ({ error: { code: 'NOT_FOUND', message: 'Not found' } }),
    })
    await expect(fetchMe()).rejects.toMatchObject({
      code: 'NOT_FOUND',
      requestId: 'req-abc',
    })
  })
})
