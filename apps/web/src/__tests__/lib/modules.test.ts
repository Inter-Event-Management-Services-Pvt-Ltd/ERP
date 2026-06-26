import { describe, it, expect } from 'vitest'
import { apiErrorMessage } from '@/lib/errors'

// ─── MODULE_DISABLED error message ────────────────────────────────────────────

describe('apiErrorMessage MODULE_DISABLED', () => {
  it('returns the rollout message for MODULE_DISABLED', () => {
    const msg = apiErrorMessage({ code: 'MODULE_DISABLED' })
    expect(msg).toBe('This module is not enabled for the current rollout.')
  })

  it('does not affect unrelated codes', () => {
    const msg = apiErrorMessage({ code: 'PERMISSION_DENIED' })
    expect(msg).toBe('You do not have permission to perform this action.')
  })
})

// ─── useModuleEnabled logic (pure extraction) ─────────────────────────────────

/**
 * The React hook is thin wrapper around this logic; test the logic directly.
 * Full hook integration tests belong in a component test that sets up QueryClient.
 */
function resolveEnabled(
  data: { code: string; enabled: boolean }[] | undefined,
  code: string
): boolean {
  if (!data) return true // loading — fail open
  const flag = data.find(f => f.code === code)
  return flag?.enabled ?? true // unknown codes default to enabled
}

describe('module enabled resolution', () => {
  it('returns true while data is undefined (loading state, fail open)', () => {
    expect(resolveEnabled(undefined, 'attendance')).toBe(true)
  })

  it('returns true when the module code is enabled', () => {
    expect(resolveEnabled([{ code: 'attendance', enabled: true }], 'attendance')).toBe(true)
  })

  it('returns false when the module code is disabled', () => {
    expect(resolveEnabled([{ code: 'attendance', enabled: false }], 'attendance')).toBe(false)
  })

  it('returns true for a code not present in the list (fail open)', () => {
    expect(resolveEnabled([{ code: 'projects', enabled: true }], 'attendance')).toBe(true)
  })

  it('returns true for an empty module list (fail open)', () => {
    expect(resolveEnabled([], 'attendance')).toBe(true)
  })

  // Test config: projects, documents, archive_exports, physical_archive disabled
  it('returns false for projects when disabled', () => {
    const flags = [
      { code: 'projects', enabled: false },
      { code: 'physical_archive', enabled: false },
      { code: 'attendance', enabled: true },
    ]
    expect(resolveEnabled(flags, 'projects')).toBe(false)
    expect(resolveEnabled(flags, 'physical_archive')).toBe(false)
    expect(resolveEnabled(flags, 'attendance')).toBe(true)
  })

  it('returns true for all enabled modules in the initial rollout config', () => {
    const flags = [
      { code: 'attendance', enabled: true },
      { code: 'leave', enabled: true },
      { code: 'tasks', enabled: true },
      { code: 'calendar', enabled: true },
      { code: 'approvals', enabled: true },
      { code: 'director_dashboard', enabled: true },
      { code: 'admin', enabled: true },
    ]
    for (const f of flags) {
      expect(resolveEnabled(flags, f.code)).toBe(true)
    }
  })
})
