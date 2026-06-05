import { DirectorGuard } from '@/components/layout/director-guard'

export default function DirectorLayout({ children }: { children: React.ReactNode }) {
  return <DirectorGuard>{children}</DirectorGuard>
}
