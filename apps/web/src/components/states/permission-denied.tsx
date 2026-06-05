import { Lock } from 'lucide-react'

/** Generic 403 state — no resource name, ID, or path is exposed. */
export function PermissionDenied() {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-6 text-center">
      <Lock size={40} aria-hidden="true" className="mb-4 text-text-primary/20" />
      <h2 className="font-serif italic text-xl text-text-primary mb-2">
        Access restricted
      </h2>
      <p className="text-sm text-text-primary/60 max-w-sm leading-relaxed">
        You don&apos;t have permission to view this page. Contact your
        administrator if you believe this is an error.
      </p>
    </div>
  )
}
