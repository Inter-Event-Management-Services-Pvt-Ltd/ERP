import { vi, describe, it, expect } from 'vitest'

vi.mock('@/lib/supabase/server', () => ({
  createClient: vi.fn().mockResolvedValue({
    auth: {
      exchangeCodeForSession: vi.fn().mockResolvedValue({ error: null }),
    },
  }),
}))

vi.mock('next/server', () => ({
  NextResponse: {
    redirect: (url: string) =>
      new Response(null, { status: 307, headers: { Location: url } }),
  },
}))

import { GET } from '@/app/auth/callback/route'

describe('auth callback redirect', () => {
  it('redirects to /dashboard when next param is absent', async () => {
    const req = new Request('http://localhost/auth/callback?code=abc')
    const res = await GET(req)
    expect(res.headers.get('location')).toBe('http://localhost/dashboard')
  })

  it('redirects to the given path when next starts with /', async () => {
    const req = new Request('http://localhost/auth/callback?code=abc&next=/projects')
    const res = await GET(req)
    expect(res.headers.get('location')).toBe('http://localhost/projects')
  })

  it('falls back to /dashboard when next does not start with /', async () => {
    const req = new Request('http://localhost/auth/callback?code=abc&next=https://evil.com')
    const res = await GET(req)
    expect(res.headers.get('location')).toBe('http://localhost/dashboard')
  })

  it('redirects to /dashboard when code is absent (no session exchange)', async () => {
    const req = new Request('http://localhost/auth/callback')
    const res = await GET(req)
    expect(res.headers.get('location')).toBe('http://localhost/dashboard')
  })
})
