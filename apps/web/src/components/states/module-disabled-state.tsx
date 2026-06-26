import { PackageX } from 'lucide-react'

/** Shown when a module route is opened but the backend has disabled that module. */
export function ModuleDisabledState() {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-6 text-center">
      <PackageX size={40} aria-hidden="true" className="mb-4 text-text-primary/20" />
      <h2 className="font-serif italic text-xl text-text-primary mb-2">
        Not available yet
      </h2>
      <p className="text-sm text-text-primary/60 max-w-sm leading-relaxed">
        This module is not enabled for the current rollout. Continue using your
        existing process until your administrator announces the rollout.
      </p>
    </div>
  )
}
