import { cn } from '@/lib/utils'

test('cn merges class names', () => {
  expect(cn('px-4', 'py-2')).toBe('px-4 py-2')
})

test('cn resolves Tailwind conflicts — last value wins', () => {
  expect(cn('px-4', 'px-8')).toBe('px-8')
})

test('cn handles conditional classes', () => {
  expect(cn('base', false && 'skipped', 'included')).toBe('base included')
})
