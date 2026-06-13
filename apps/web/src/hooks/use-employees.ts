import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchEmployees } from '@/lib/api'

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
