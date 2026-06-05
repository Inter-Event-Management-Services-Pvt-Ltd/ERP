import type { UserRole } from '@/types'
import { canAccess } from '@/hooks/use-role'

test('all six roles are represented', () => {
  const roles: UserRole[] = [
    'EMPLOYEE',
    'MANAGER',
    'ADMIN',
    'SUPER_ADMIN',
    'SUPER_USER',
    'DIRECTOR',
  ]
  expect(roles).toHaveLength(6)
})

test('canAccess: DIRECTOR can access director-only routes', () => {
  expect(canAccess(['DIRECTOR'], ['DIRECTOR'])).toBe(true)
})

test('canAccess: EMPLOYEE cannot access admin-only routes', () => {
  expect(canAccess(['EMPLOYEE'], ['ADMIN', 'SUPER_ADMIN', 'SUPER_USER'])).toBe(false)
})

test('canAccess: ADMIN can access admin routes', () => {
  expect(canAccess(['ADMIN'], ['ADMIN', 'SUPER_ADMIN', 'SUPER_USER'])).toBe(true)
})

test('canAccess: empty allowedRoles grants access to all', () => {
  expect(canAccess(['EMPLOYEE'], [])).toBe(true)
})
